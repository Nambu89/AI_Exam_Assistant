"""Credential-free lexical retriever over the Markdown study corpus.

This is what powers *offline mode*: no LLM, no vector store, no Azure. It splits
each corpus file into heading-delimited sections and ranks them against the
query with a small TF-IDF-ish keyword score. It is intentionally simple — its
job is to make "clone and run" work and to give the test-suite a deterministic
grounding source, not to compete with GraphRAG or Foundry IQ.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from app.config import REPO_ROOT
from app.knowledge.base import RetrievalResult, RetrievedChunk, SearchMode

_WORD = re.compile(r"[a-zA-Z0-9]+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "for", "on",
    "with", "as", "by", "that", "this", "it", "be", "can", "which", "what",
    "how", "why", "when", "where", "into", "from", "at", "its", "you", "your",
}


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text) if w.lower() not in _STOP and len(w) > 2]


@lru_cache
def corpus_dir() -> Path:
    return REPO_ROOT / "data" / "corpus"


def _split_sections(text: str, source: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading, body) sections on ## / ### boundaries."""
    parts: list[tuple[str, str]] = []
    current_heading = source
    buffer: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            if buffer:
                parts.append((current_heading, "\n".join(buffer).strip()))
                buffer = []
            current_heading = re.sub(r"^#+\s+", "", line).strip()
        else:
            buffer.append(line)
    if buffer:
        parts.append((current_heading, "\n".join(buffer).strip()))
    return [(h, b) for h, b in parts if b]


class LocalCorpusRetriever:
    name = "local-corpus"

    def __init__(self, root: Path | None = None):
        self._root = root or corpus_dir()
        self._chunks: list[RetrievedChunk] = []
        self._df: Counter[str] = Counter()
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        for md in sorted(self._root.rglob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            rel = md.relative_to(self._root).as_posix()
            text = md.read_text(encoding="utf-8")
            for heading, body in _split_sections(text, rel):
                source = f"{rel}#{heading}"
                self._chunks.append(RetrievedChunk(text=f"## {heading}\n{body}", source=source))
                for term in set(_tokenize(body)):
                    self._df[term] += 1
        self._loaded = True

    def _score(self, query_terms: list[str], chunk: RetrievedChunk) -> float:
        n_docs = max(len(self._chunks), 1)
        tokens = _tokenize(chunk.text)
        if not tokens:
            return 0.0
        tf = Counter(tokens)
        score = 0.0
        for term in query_terms:
            if term in tf:
                idf = math.log((n_docs + 1) / (self._df.get(term, 0) + 1)) + 1.0
                score += (tf[term] / len(tokens)) * idf
        return score

    async def search(self, query: str, mode: SearchMode = SearchMode.DRIFT) -> RetrievalResult:
        self._ensure_loaded()
        query_terms = _tokenize(query)

        # GLOBAL: return the highest-level headings across all files so the model
        # (or the offline template) can synthesise a syllabus-wide answer.
        top_k = 8 if mode == SearchMode.GLOBAL else 4

        ranked = sorted(
            self._chunks,
            key=lambda c: self._score(query_terms, c),
            reverse=True,
        )
        hits = [c for c in ranked if self._score(query_terms, c) > 0][:top_k]
        if not hits:
            hits = ranked[:top_k]  # fall back to something rather than nothing

        for c in hits:
            c.score = round(self._score(query_terms, c), 4)

        context = "\n\n---\n\n".join(f"[source: {c.source}]\n{c.text}" for c in hits)
        return RetrievalResult(context=context, chunks=hits, mode=mode, backend=self.name)

    def all_chunks(self) -> list[RetrievedChunk]:
        self._ensure_loaded()
        return list(self._chunks)
