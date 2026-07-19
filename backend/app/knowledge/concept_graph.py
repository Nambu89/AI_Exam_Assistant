"""Concept-map builder — the visual differentiator.

Two sources, same output shape (``ConceptMap``):

* **GraphRAG** — when a GraphRAG project has been indexed, read the generated
  ``entities.parquet`` / ``relationships.parquet`` / ``community_reports.parquet``
  and turn them into nodes/edges/communities. This is the "real" graph produced
  by LLM entity/relationship extraction + Leiden community detection.
* **Offline** — with no index and no LLM, build a lightweight graph by
  extracting capitalised concept phrases from the corpus and connecting concepts
  that co-occur in the same section. Communities default to one per corpus file.

This lets the concept map render out-of-the-box (offline) and light up with the
richer GraphRAG graph once indexed.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from app.config import get_settings
from app.knowledge.local_corpus import corpus_dir
from app.models.schemas import Community, ConceptEdge, ConceptMap, ConceptNode

# Capitalised multi-word phrases + known acronyms → candidate concepts.
_PHRASE = re.compile(r"\b(?:[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3}|[A-Z]{2,6})\b")
_PHRASE_STOP = {
    "The", "This", "That", "These", "Those", "For", "With", "When", "Which",
    "Azure", "Microsoft", "It", "In", "On", "As", "A", "An", "And", "Or", "If",
}


def _extract_concepts(text: str) -> list[str]:
    out: list[str] = []
    for m in _PHRASE.findall(text):
        phrase = m.strip()
        if phrase in _PHRASE_STOP or len(phrase) < 3:
            continue
        # Keep multi-word phrases and meaningful acronyms; drop bare stopwords.
        if " " in phrase or phrase.isupper():
            out.append(phrase)
    return out


def _offline_concept_map(subject: str) -> ConceptMap:
    root = corpus_dir()
    subject_dir = root / subject
    files = (
        sorted(subject_dir.rglob("*.md")) if subject_dir.exists() else sorted(root.rglob("*.md"))
    )

    freq: Counter[str] = Counter()
    co: Counter[tuple[str, str]] = Counter()
    community_of: dict[str, int] = {}
    community_titles: dict[int, str] = {}

    for idx, md in enumerate(files):
        if md.name.lower() == "readme.md":
            continue
        text = md.read_text(encoding="utf-8")
        community_titles[idx] = _file_title(text, md)
        # Section-level co-occurrence.
        for section in re.split(r"\n#{1,3}\s+", text):
            concepts = list(dict.fromkeys(_extract_concepts(section)))[:25]
            for c in concepts:
                freq[c] += 1
                community_of.setdefault(c, idx)
            for i in range(len(concepts)):
                for j in range(i + 1, len(concepts)):
                    a, b = sorted((concepts[i], concepts[j]))
                    co[(a, b)] += 1

    # Keep the most frequent concepts to keep the graph readable.
    top = {c for c, _ in freq.most_common(60)}
    nodes = [
        ConceptNode(
            id=c,
            label=c,
            community=community_of.get(c, 0),
            size=float(freq[c]),
        )
        for c in top
    ]
    edges = [
        ConceptEdge(source=a, target=b, weight=float(w))
        for (a, b), w in co.items()
        if a in top and b in top and w >= 2
    ]
    communities = [Community(id=i, title=t) for i, t in sorted(community_titles.items())]
    return ConceptMap(
        subject=subject, backend="offline", nodes=nodes, edges=edges, communities=communities
    )


def _file_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def _graphrag_concept_map(subject: str, level: int) -> ConceptMap | None:
    """Read a GraphRAG index output if present. Returns None if unavailable."""
    settings = get_settings()
    out_dir = Path(settings.graphrag_root) / "output"
    entities_p = out_dir / "entities.parquet"
    rels_p = out_dir / "relationships.parquet"
    if not entities_p.exists() or not rels_p.exists():
        return None
    try:
        import pandas as pd
    except ImportError:
        return None

    entities = pd.read_parquet(entities_p)
    rels = pd.read_parquet(rels_p)

    # Column names vary across GraphRAG versions; resolve defensively.
    def col(df, *candidates, default=None):
        for c in candidates:
            if c in df.columns:
                return c
        return default

    e_title = col(entities, "title", "name")
    e_comm = col(entities, "community")
    e_deg = col(entities, "degree", "frequency")

    nodes: list[ConceptNode] = []
    for _, row in entities.iterrows():
        title = str(row[e_title])
        nodes.append(
            ConceptNode(
                id=title,
                label=title,
                community=int(row[e_comm]) if e_comm and pd.notna(row[e_comm]) else 0,
                size=float(row[e_deg]) if e_deg and pd.notna(row[e_deg]) else 1.0,
            )
        )

    r_src = col(rels, "source", "head")
    r_tgt = col(rels, "target", "tail")
    r_w = col(rels, "weight", "rank")
    edges = [
        ConceptEdge(
            source=str(row[r_src]),
            target=str(row[r_tgt]),
            weight=float(row[r_w]) if r_w and pd.notna(row[r_w]) else 1.0,
        )
        for _, row in rels.iterrows()
    ]

    communities: list[Community] = []
    reports_p = out_dir / "community_reports.parquet"
    if reports_p.exists():
        reports = pd.read_parquet(reports_p)
        c_id = col(reports, "community", "id")
        c_title = col(reports, "title")
        c_sum = col(reports, "summary")
        c_level = col(reports, "level")
        for _, row in reports.iterrows():
            if c_level and pd.notna(row[c_level]) and int(row[c_level]) != level:
                continue
            communities.append(
                Community(
                    id=int(row[c_id]) if c_id and pd.notna(row[c_id]) else 0,
                    title=str(row[c_title]) if c_title else "",
                    summary=str(row[c_sum]) if c_sum else "",
                )
            )

    return ConceptMap(
        subject=subject, backend="graphrag", nodes=nodes, edges=edges, communities=communities
    )


def build_concept_map(subject: str = "az-900", level: int = 1) -> ConceptMap:
    """Return the GraphRAG-derived map when indexed, else the offline map."""
    graph = _graphrag_concept_map(subject, level)
    if graph is not None and graph.nodes:
        return graph
    return _offline_concept_map(subject)


# Small helper reused by the analytics agent / topics endpoint.
def corpus_subjects() -> list[tuple[str, str, list[str]]]:
    """Return (subject_id, title, [topic titles]) for each subject in the corpus."""
    root = corpus_dir()
    out: list[tuple[str, str, list[str]]] = []
    if not root.exists():
        return out
    for subject_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        topics: list[str] = []
        title = subject_dir.name.upper()
        for md in sorted(subject_dir.rglob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            text = md.read_text(encoding="utf-8")
            topics.append(_file_title(text, md))
        out.append((subject_dir.name, title, topics))
    return out
