"""Foundry IQ retriever — Azure AI Foundry knowledge base + agentic retrieval.

Foundry IQ (GA in part since the 2026-04-01 Search REST API) is Microsoft's
managed knowledge layer: a *knowledge base* over one or more *knowledge sources*,
queried with *agentic retrieval* (a planner decomposes the question into parallel
sub-queries, then reranks). Microsoft reports up to +54% recall vs single-shot
RAG.

This retriever calls a knowledge base backed by Azure AI Search using the
agentic-retrieval client from ``azure-search-documents`` (installed via the
``[eval]``/cloud extras). It authenticates with a Microsoft Entra credential
(no keys). If the SDK or configuration is missing, callers fall back to GraphRAG
or the local corpus.

Verification note: the exact client/parameter names for agentic retrieval were
still stabilising at build time — confirm against the installed
``azure-search-documents`` version before production use.
"""

from __future__ import annotations

from app.config import get_settings
from app.knowledge.base import RetrievalResult, RetrievedChunk, SearchMode


class FoundryIqUnavailable(RuntimeError):
    pass


class FoundryIqRetriever:
    name = "foundry_iq"

    def __init__(self) -> None:
        s = get_settings()
        self._endpoint = s.azure_search_endpoint
        self._kb = s.foundry_knowledge_base
        if not self._endpoint or not self._kb:
            raise FoundryIqUnavailable("AZURE_SEARCH_ENDPOINT / FOUNDRY_KNOWLEDGE_BASE not set")

    async def search(self, query: str, mode: SearchMode = SearchMode.DRIFT) -> RetrievalResult:
        try:
            from azure.identity.aio import DefaultAzureCredential
            from azure.search.documents.agent.aio import KnowledgeAgentRetrievalClient
            from azure.search.documents.agent.models import (
                KnowledgeAgentMessage,
                KnowledgeAgentMessageTextContent,
                KnowledgeAgentRetrievalRequest,
            )
        except ImportError as exc:  # pragma: no cover - env dependent
            raise FoundryIqUnavailable("azure-search-documents agent client not installed") from exc

        credential = DefaultAzureCredential()
        client = KnowledgeAgentRetrievalClient(
            endpoint=self._endpoint, agent_name=self._kb, credential=credential
        )
        try:
            request = KnowledgeAgentRetrievalRequest(
                messages=[
                    KnowledgeAgentMessage(
                        role="user",
                        content=[KnowledgeAgentMessageTextContent(text=query)],
                    )
                ]
            )
            result = await client.retrieve(retrieval_request=request)
        finally:
            await client.close()
            await credential.close()

        # The response exposes a synthesised context plus per-reference activity.
        context_text = getattr(result, "response", None) or ""
        if isinstance(context_text, list):  # some versions return message list
            context_text = " ".join(
                getattr(c, "text", "") for m in context_text for c in getattr(m, "content", [])
            )

        chunks: list[RetrievedChunk] = []
        for ref in getattr(result, "references", []) or []:
            source = getattr(ref, "source_data", None) or getattr(ref, "doc_key", "") or ""
            chunks.append(RetrievedChunk(text=str(getattr(ref, "content", "")), source=str(source)))

        return RetrievalResult(
            context=str(context_text), chunks=chunks, mode=mode, backend=self.name
        )
