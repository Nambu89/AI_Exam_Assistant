"""GraphRAG retriever — wraps the official ``graphrag`` package (MIT, v3.1.x).

Query-mode mapping (see docs/ARCHITECTURE.md):
* DRIFT  → conversational tutoring (local detail + community context)
* LOCAL  → factual, entity-centric lookups
* GLOBAL → holistic "what are the main topics / coverage" questions

Requires a GraphRAG project that has already been indexed
(``python -m app.ingest`` → ``graphrag index``). If the index is missing or the
package is unavailable, callers should fall back to the local corpus retriever.

Note (GraphRAG issue #1642, 2026): DRIFT search is unreliable against the Azure
AI Search vector store; use the default LanceDB vector store for DRIFT.
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.knowledge.base import RetrievalResult, RetrievedChunk, SearchMode


class GraphRagUnavailable(RuntimeError):
    pass


class GraphRagRetriever:
    name = "graphrag"

    def __init__(self, root: Path | None = None):
        self._root = Path(root or get_settings().graphrag_root)

    def is_indexed(self) -> bool:
        out = self._root / "output"
        return (out / "entities.parquet").exists() and (out / "community_reports.parquet").exists()

    async def search(self, query: str, mode: SearchMode = SearchMode.DRIFT) -> RetrievalResult:
        if not self.is_indexed():
            raise GraphRagUnavailable(f"No GraphRAG index under {self._root}")

        try:
            import graphrag.api as gr_api
            import pandas as pd
            from graphrag.config.load_config import load_config
        except ImportError as exc:  # pragma: no cover - env dependent
            raise GraphRagUnavailable("graphrag package not installed") from exc

        config = load_config(self._root)
        out = self._root / "output"

        entities = pd.read_parquet(out / "entities.parquet")
        communities = pd.read_parquet(out / "communities.parquet")
        reports = pd.read_parquet(out / "community_reports.parquet")

        if mode == SearchMode.GLOBAL:
            response, context = await gr_api.global_search(
                config=config,
                entities=entities,
                communities=communities,
                community_reports=reports,
                community_level=2,
                dynamic_community_selection=False,
                response_type="Multiple Paragraphs",
                query=query,
            )
        else:
            text_units = pd.read_parquet(out / "text_units.parquet")
            relationships = pd.read_parquet(out / "relationships.parquet")
            search_fn = gr_api.drift_search if mode == SearchMode.DRIFT else gr_api.local_search
            response, context = await search_fn(
                config=config,
                entities=entities,
                communities=communities,
                community_reports=reports,
                text_units=text_units,
                relationships=relationships,
                covariates=None,
                community_level=2,
                response_type="Multiple Paragraphs",
                query=query,
            )

        chunks = _context_to_chunks(context)
        return RetrievalResult(context=str(response), chunks=chunks, mode=mode, backend=self.name)


def _context_to_chunks(context: object) -> list[RetrievedChunk]:
    """Best-effort extraction of source references from GraphRAG's context dict.

    GraphRAG returns a context object whose shape varies by version/mode; we pull
    entity/source titles when present so the UI can cite them. Failures degrade to
    an empty source list rather than raising.
    """
    chunks: list[RetrievedChunk] = []
    try:
        import pandas as pd

        if isinstance(context, dict):
            for key in ("sources", "entities", "reports"):
                frame = context.get(key)
                if isinstance(frame, pd.DataFrame):
                    label_col = next(
                        (c for c in ("title", "name", "source_id", "id") if c in frame.columns),
                        None,
                    )
                    if label_col:
                        for val in frame[label_col].head(8).tolist():
                            chunks.append(RetrievedChunk(text="", source=str(val)))
    except Exception:  # pragma: no cover - defensive
        return chunks
    return chunks
