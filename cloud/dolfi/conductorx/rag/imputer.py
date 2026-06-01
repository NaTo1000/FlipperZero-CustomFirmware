"""
RAG Imputer — fills missing retrieval chunks by inferring from adjacent tags.

If a level returns 0 results, the imputer tries:
  bot missing  → synthesize from mid chunks
  mid missing  → synthesize from top chunks
  top missing  → use a fallback general context stub
"""
from __future__ import annotations

from typing import Optional

from .retriever import RAGRetriever, RetrievedChunk, Level, Domain


class RAGImputer:
    """
    Wraps RAGRetriever and fills gaps in the top→mid→bot cascade.
    """

    def __init__(self, retriever: RAGRetriever) -> None:
        self._retriever = retriever

    def retrieve_with_imputation(
        self,
        query: str,
        domain: Optional[Domain] = None,
    ) -> str:
        """
        Retrieve with automatic imputation of missing levels.
        Returns assembled XML context string.
        """
        top = self._retriever.retrieve_raw(query, level="top", domain=domain)
        mid = self._retriever.retrieve_raw(query, level="mid", domain=domain)
        bot = self._retriever.retrieve_raw(query, level="bot", domain=domain)

        # Impute missing levels
        if not top:
            top = [self._stub_chunk("top", domain, "No architectural context found.")]
        if not mid:
            mid = self._impute_from_above(top, "mid", domain)
        if not bot:
            bot = self._impute_from_above(mid, "bot", domain)

        all_chunks = top + mid + bot
        sections = [
            f'<context level="{c.level}" domain="{c.domain}" type="{c.chunk_type}">\n'
            f"{c.text.strip()}\n</context>"
            for c in all_chunks
        ]
        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _impute_from_above(
        above: list[RetrievedChunk],
        target_level: Level,
        domain: Optional[Domain],
    ) -> list[RetrievedChunk]:
        """
        Create synthetic chunks at target_level by summarising the above-level text.
        In production this would call the LLM to generate a summary.
        Here we just re-label the above chunks as the target level.
        """
        return [
            RetrievedChunk(
                level=target_level,
                domain=c.domain,
                chunk_type=c.chunk_type,
                text=f"[Imputed from {c.level}] {c.text}",
                score=c.score * 0.8,
                source=c.source,
            )
            for c in above[:2]
        ]

    @staticmethod
    def _stub_chunk(
        level: Level,
        domain: Optional[Domain],
        text: str,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            level=level,
            domain=domain or "general",
            chunk_type="reference",
            text=text,
            score=0.0,
            source="imputer",
        )
