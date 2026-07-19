"""Retriever selection with graceful degradation.

Resolution order is driven by ``KNOWLEDGE_BACKEND`` and the active provider, but
the local corpus retriever is ALWAYS the final fallback so the assistant can
still ground its answers if a cloud backend is misconfigured or an index is
missing. A misconfigured cloud never means "no grounding".
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.config import KnowledgeBackend, ModelProvider, get_settings
from app.knowledge.base import RetrievalResult, Retriever, SearchMode
from app.knowledge.local_corpus import LocalCorpusRetriever

logger = logging.getLogger(__name__)


class CompositeRetriever:
    """Try retrievers in order; return the first non-empty result."""

    name = "composite"

    def __init__(self, retrievers: list[Retriever]):
        # De-dupe while preserving order; guarantee a local fallback at the end.
        self._retrievers = retrievers
        if not any(isinstance(r, LocalCorpusRetriever) for r in self._retrievers):
            self._retrievers.append(LocalCorpusRetriever())

    async def search(self, query: str, mode: SearchMode = SearchMode.DRIFT) -> RetrievalResult:
        last: RetrievalResult | None = None
        for retriever in self._retrievers:
            try:
                result = await retriever.search(query, mode)
            except Exception as exc:  # noqa: BLE001 - deliberate degrade
                logger.warning("retriever %s failed: %s", getattr(retriever, "name", "?"), exc)
                continue
            if not result.is_empty:
                return result
            last = result
        return last or RetrievalResult(context="", backend="none", mode=mode)

    @property
    def backends(self) -> list[str]:
        return [getattr(r, "name", "?") for r in self._retrievers]


def _build_chain() -> list[Retriever]:
    settings = get_settings()
    chain: list[Retriever] = []

    want = settings.knowledge_backend
    has_foundry = bool(settings.azure_search_endpoint and settings.foundry_knowledge_base)

    def add_foundry() -> None:
        try:
            from app.knowledge.foundry_iq import FoundryIqRetriever

            chain.append(FoundryIqRetriever())
        except Exception as exc:  # noqa: BLE001
            logger.info("Foundry IQ retriever unavailable: %s", exc)

    def add_graphrag() -> None:
        from app.knowledge.graphrag_service import GraphRagRetriever

        gr = GraphRagRetriever()
        if gr.is_indexed():
            chain.append(gr)
        else:
            logger.info("GraphRAG index not found; skipping GraphRAG retriever")

    if settings.model_provider != ModelProvider.LOCAL:
        if want == KnowledgeBackend.FOUNDRY_IQ:
            add_foundry()
        elif want == KnowledgeBackend.GRAPHRAG:
            add_graphrag()
        else:  # AUTO
            if has_foundry:
                add_foundry()
            add_graphrag()

    chain.append(LocalCorpusRetriever())
    return chain


@lru_cache
def get_retriever() -> CompositeRetriever:
    chain = _build_chain()
    retriever = CompositeRetriever(chain)
    logger.info("Retriever chain: %s", retriever.backends)
    return retriever
