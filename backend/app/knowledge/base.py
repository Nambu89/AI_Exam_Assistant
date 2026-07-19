"""Retrieval abstractions shared by every knowledge backend.

The assistant grounds *everything* it says in the study corpus. A retriever
returns both a ready-to-prompt ``context`` string and the individual
``chunks``/``sources`` so the UI can show the student exactly where an answer
(or an exam question) comes from — trust and traceability are first-class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class SearchMode(str, Enum):
    """Maps directly onto GraphRAG's query methods.

    * ``LOCAL``  — entity-centric, cheap: "what is X?", factual lookups.
    * ``GLOBAL`` — holistic map-reduce over community reports: "what are the
      main topics of the syllabus?", coverage questions.
    * ``DRIFT``  — local search enriched with community context; the default for
      conversational tutoring. (GraphRAG issue #1642: DRIFT is unreliable on the
      Azure AI Search vector store — use LanceDB for DRIFT.)
    """

    LOCAL = "local"
    GLOBAL = "global"
    DRIFT = "drift"


@dataclass(slots=True)
class RetrievedChunk:
    text: str
    source: str
    score: float = 0.0


@dataclass(slots=True)
class RetrievalResult:
    context: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    mode: SearchMode = SearchMode.LOCAL
    backend: str = "unknown"

    @property
    def sources(self) -> list[str]:
        seen: dict[str, None] = {}
        for c in self.chunks:
            seen.setdefault(c.source, None)
        return list(seen)

    @property
    def is_empty(self) -> bool:
        return not self.context.strip()


@runtime_checkable
class Retriever(Protocol):
    name: str

    async def search(self, query: str, mode: SearchMode = SearchMode.DRIFT) -> RetrievalResult: ...
