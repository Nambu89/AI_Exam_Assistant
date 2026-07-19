"""Prepare the GraphRAG input folder from the study corpus.

Usage:
    python -m app.ingest [--subject az-900]

Then index with the GraphRAG CLI:
    graphrag index --root backend/graphrag

Cost tip: GraphRAG entity/relationship extraction is ~75% of indexing cost.
``settings.yaml`` is configured to use the cheap ``ROUTER_MODEL`` (gpt-5-nano)
for extraction and the ``CHAT_MODEL`` only for community reports.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from app.config import get_settings
from app.knowledge.local_corpus import corpus_dir


def prepare_input(subject: str | None = None) -> int:
    settings = get_settings()
    gr_root = Path(settings.graphrag_root)
    input_dir = gr_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    root = corpus_dir()
    base = root / subject if subject else root
    if not base.exists():
        base = root

    count = 0
    for md in sorted(base.rglob("*.md")):
        if md.name.lower() == "readme.md":
            continue
        # GraphRAG reads .txt by default; keep a flat, prefixed name for traceability.
        rel = md.relative_to(root).as_posix().replace("/", "__")
        target = input_dir / f"{rel}.txt"
        shutil.copyfile(md, target)
        count += 1

    print(f"Prepared {count} document(s) in {input_dir}")
    print("Next: graphrag index --root", gr_root)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", default=None, help="Corpus subject folder, e.g. az-900")
    args = parser.parse_args()
    prepare_input(args.subject)
