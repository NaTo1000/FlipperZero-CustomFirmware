"""
ConductorX RAG — Quad-tag cascade retriever.

Retrieval order: top → mid → bot
Each level is retrieved independently and assembled with section tags.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from .indexer import COLLECTION, Domain, Level, ChunkType

XML_TEMPLATE = "<context level=\"{level}\" domain=\"{domain}\" type=\"{chunk_type}\">\n{text}\n</context>"


@dataclass
class RetrievedChunk:
    level: Level
    domain: Domain
    chunk_type: ChunkType
    text: str
    score: float
    source: str


class RAGRetriever:
    """
    Retrieves chunks using the top→mid→bot cascade strategy.

    For each level, the most relevant chunks are fetched and
    assembled into a structured XML context block for the LLM.
    """

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        embed_fn=None,
        top_k_per_level: int = 3,
    ) -> None:
        self._client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self._embed = embed_fn or self._stub_embed
        self._top_k = top_k_per_level

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        domain: Optional[Domain] = None,
    ) -> str:
        """
        Run the top→mid→bot cascade and return an XML context string
        ready to inject into the LLM system prompt.
        """
        sections: list[str] = []
        for level in ("top", "mid", "bot"):
            chunks = self._search(query, level=level, domain=domain)  # type: ignore[arg-type]
            for chunk in chunks:
                sections.append(
                    XML_TEMPLATE.format(
                        level=chunk.level,
                        domain=chunk.domain,
                        chunk_type=chunk.chunk_type,
                        text=chunk.text.strip(),
                    )
                )
        return "\n\n".join(sections) if sections else ""

    def retrieve_raw(
        self,
        query: str,
        level: Optional[Level] = None,
        domain: Optional[Domain] = None,
    ) -> list[RetrievedChunk]:
        """Return raw chunks without XML wrapping."""
        if level:
            return self._search(query, level=level, domain=domain)
        results = []
        for lvl in ("top", "mid", "bot"):
            results.extend(self._search(query, level=lvl, domain=domain))  # type: ignore[arg-type]
        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _search(
        self,
        query: str,
        level: Level,
        domain: Optional[Domain] = None,
    ) -> list[RetrievedChunk]:
        conditions = [
            FieldCondition(key="level", match=MatchValue(value=level))
        ]
        if domain:
            conditions.append(
                FieldCondition(key="domain", match=MatchValue(value=domain))
            )
        query_filter = Filter(must=conditions)
        vector = self._embed(query)

        results = self._client.search(
            collection_name=COLLECTION,
            query_vector=vector,
            query_filter=query_filter,
            limit=self._top_k,
            with_payload=True,
        )
        return [
            RetrievedChunk(
                level=r.payload["level"],
                domain=r.payload["domain"],
                chunk_type=r.payload["chunk_type"],
                text=r.payload["text"],
                score=r.score,
                source=r.payload.get("source", ""),
            )
            for r in results
        ]

    @staticmethod
    def _stub_embed(text: str) -> list[float]:
        import random
        rng = random.Random(hash(text) % (2**32))
        return [rng.random() for _ in range(1536)]
