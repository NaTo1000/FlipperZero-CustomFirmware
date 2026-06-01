"""
ConductorX RAG — Quad-tag document indexer.

Tags every chunk with 4 dimensions:
  level:   top | mid | bot
  domain:  firmware | nfc | subghz | ir | badusb | ibutton | crypto | sql | general
  type:    tutorial | reference | error | recovery | code | pricing | legal
  recency: live | recent | archive
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

Level = Literal["top", "mid", "bot"]
Domain = Literal[
    "firmware", "nfc", "subghz", "ir", "badusb", "ibutton", "crypto", "sql", "general"
]
ChunkType = Literal[
    "tutorial", "reference", "error", "recovery", "code", "pricing", "legal"
]
Recency = Literal["live", "recent", "archive"]

COLLECTION = "conductorx_rag"
VECTOR_DIM = 1536  # OpenAI/compatible embedding dimension


@dataclass
class ChunkMeta:
    level: Level
    domain: Domain
    chunk_type: ChunkType
    recency: Recency
    source: str
    chunk_index: int


def _chunk_id(text: str, meta: ChunkMeta) -> str:
    raw = f"{meta.source}:{meta.chunk_index}:{text[:64]}"
    return hashlib.sha256(raw.encode()).hexdigest()


class RAGIndexer:
    """
    Indexes text chunks into Qdrant with quad-tag metadata.

    Embeddings are generated via the configured embedding function
    (defaults to a passthrough stub; replace with real embedding call).
    """

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        embed_fn=None,
    ) -> None:
        self._client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self._embed = embed_fn or self._stub_embed
        self._ensure_collection()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_chunk(self, text: str, meta: ChunkMeta) -> str:
        """Embed and upsert a single chunk. Returns the chunk ID."""
        chunk_id = _chunk_id(text, meta)
        vector = self._embed(text)
        payload = {**asdict(meta), "text": text}
        self._client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(id=chunk_id, vector=vector, payload=payload)],
        )
        return chunk_id

    def index_file(
        self,
        path: str | Path,
        meta_overrides: dict | None = None,
        chunk_size: int = 512,
        overlap: int = 64,
    ) -> list[str]:
        """Chunk a text file and index all chunks."""
        text = Path(path).read_text(encoding="utf-8")
        chunks = self._chunk_text(text, chunk_size, overlap)
        ids = []
        source = str(path)
        for i, chunk in enumerate(chunks):
            meta = ChunkMeta(
                level=meta_overrides.get("level", "mid") if meta_overrides else "mid",
                domain=meta_overrides.get("domain", "general") if meta_overrides else "general",
                chunk_type=meta_overrides.get("chunk_type", "reference") if meta_overrides else "reference",
                recency=meta_overrides.get("recency", "archive") if meta_overrides else "archive",
                source=source,
                chunk_index=i,
            )
            ids.append(self.index_chunk(chunk, meta))
        return ids

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if COLLECTION not in existing:
            self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )

    @staticmethod
    def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + size
            chunks.append(" ".join(words[start:end]))
            start += size - overlap
        return chunks

    @staticmethod
    def _stub_embed(text: str) -> list[float]:
        """Stub embedding — replace with real model call in production."""
        import random
        rng = random.Random(hash(text) % (2**32))
        return [rng.random() for _ in range(VECTOR_DIM)]
