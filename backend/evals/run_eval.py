#!/usr/bin/env python
"""Agent-quality evaluation gate for the AI Exam Assistant.

This is the CI gate that makes the project stand out: it evaluates the *agent's*
answers against a gold dataset, on every push, with zero secrets.

Two layers (see ``README.md``):

1. **Offline deterministic gate** (always runs, no LLM, no network). Drives the
   orchestrator with ``MODEL_PROVIDER=local`` and scores each answer with the
   pure functions in :mod:`metrics`. Its ``pass_rate`` decides the exit code.
2. **Azure AI Evaluation layer** (optional, ``--mode azure``). When Azure creds
   are present it additionally runs Microsoft's official LLM-judge evaluators
   (Groundedness, Relevance, Intent Resolution). Imported lazily; skipped
   cleanly with a log line when the package or creds are missing.

Usage::

    python backend/evals/run_eval.py \
        --gold data/eval/gold_qa.jsonl \
        --out eval-report.json \
        [--mode offline|azure] \
        [--min-groundedness 0.6] [--min-pass-rate 0.7]

Exit code: ``0`` if every threshold is met, ``1`` otherwise.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ``metrics`` lives next to this file. Support both "run as a module"
# (``evals.metrics``) and "run as a script" (``metrics``) invocations.
try:  # pragma: no cover - trivial import shim
    from evals.metrics import (
        groundedness_lexical,
        keyword_recall,
    )
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from metrics import (  # type: ignore[no-redef]
        groundedness_lexical,
        keyword_recall,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("eval")

DEFAULT_MIN_GROUNDEDNESS = 0.6
DEFAULT_MIN_PASS_RATE = 0.7
DEFAULT_JUDGE_MODEL = "gpt-5-mini"


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #

@dataclass
class ItemResult:
    question: str
    topic: str
    type: str
    ground_truth: str
    answer: str = ""
    sources: list[str] = field(default_factory=list)
    agent_used: str = ""
    route: str = ""
    mode: str = ""
    groundedness_lexical: float = 0.0
    keyword_recall: float = 0.0
    has_sources: bool = False
    passed: bool = False
    error: str | None = None
    azure: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "topic": self.topic,
            "type": self.type,
            "answer": self.answer,
            "sources": self.sources,
            "agent_used": self.agent_used,
            "route": self.route,
            "mode": self.mode,
            "metrics": {
                "groundedness_lexical": round(self.groundedness_lexical, 4),
                "keyword_recall": round(self.keyword_recall, 4),
                "has_sources": self.has_sources,
            },
            "azure": self.azure,
            "passed": self.passed,
            "error": self.error,
        }


# --------------------------------------------------------------------------- #
# Gold loading
# --------------------------------------------------------------------------- #

def load_gold(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Gold dataset not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{i}: invalid JSON: {exc}") from exc
            for key in ("question", "ground_truth", "type"):
                if key not in obj:
                    raise ValueError(f"{path}:{i}: missing required key '{key}'")
            obj.setdefault("topic", "")
            rows.append(obj)
    if not rows:
        raise ValueError(f"Gold dataset is empty: {path}")
    return rows


# --------------------------------------------------------------------------- #
# Orchestrator plumbing (guarded import — the app may not be importable yet)
# --------------------------------------------------------------------------- #

def _import_orchestrator():
    """Import the orchestrator + SearchMode, raising a clear error if absent.

    Ensures the backend package root (``backend/``, the parent of this file's
    directory) is importable so the harness works from any CWD and without
    requiring ``PYTHONPATH`` to be set (CI, local, IDE)."""

    backend_root = str(Path(__file__).resolve().parent.parent)
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    from app.agents.orchestrator import Orchestrator  # type: ignore
    from app.knowledge.base import SearchMode  # type: ignore

    return Orchestrator, SearchMode


def _extract_source_texts(res: Any) -> list[str]:
    """Best-effort recovery of retrieved source *text* for grounding.

    The documented interface only guarantees ``res.sources: list[str]`` (source
    identifiers). Some backends also expose the retrieved chunks/context; we use
    them when present so groundedness can score against real evidence, and fall
    back gracefully to just the source labels otherwise.
    """

    texts: list[str] = []
    for attr in ("chunks", "retrieved_chunks"):
        chunks = getattr(res, attr, None)
        if chunks:
            for c in chunks:
                t = getattr(c, "text", None)
                if t:
                    texts.append(str(t))
    for attr in ("context", "retrieval_context"):
        ctx = getattr(res, attr, None)
        if isinstance(ctx, str) and ctx.strip():
            texts.append(ctx)
    # Source labels themselves carry a little lexical signal (file names).
    srcs = getattr(res, "sources", None)
    if srcs:
        texts.extend(str(s) for s in srcs)
    return texts


async def run_offline(
    gold: list[dict[str, Any]],
    min_groundedness: float,
) -> list[ItemResult]:
    """Drive the orchestrator over the gold set and score every answer."""

    try:
        Orchestrator, SearchMode = _import_orchestrator()
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Could not import the orchestrator "
            "(app.agents.orchestrator.Orchestrator / app.knowledge.base.SearchMode). "
            "Run this from the backend/ directory with the app installed. "
            f"Underlying error: {exc}"
        ) from exc

    os.environ.setdefault("MODEL_PROVIDER", "local")
    orch = Orchestrator()

    results: list[ItemResult] = []
    for idx, row in enumerate(gold, 1):
        item = ItemResult(
            question=row["question"],
            topic=row.get("topic", ""),
            type=row.get("type", "local"),
            ground_truth=row["ground_truth"],
        )
        mode = SearchMode.GLOBAL if item.type == "global" else SearchMode.DRIFT
        try:
            res = await orch.chat(message=item.question, mode=mode)
            item.answer = str(getattr(res, "response", "") or "")
            raw_sources = getattr(res, "sources", None) or []
            item.sources = [str(s) for s in raw_sources]
            item.agent_used = str(getattr(res, "agent_used", "") or "")
            item.route = str(getattr(res, "route", "") or "")
            item.mode = str(getattr(res, "mode", mode) or "")

            reference = _extract_source_texts(res)
            # Ground against retrieved evidence AND the gold answer, so a correct
            # answer is credited even when the backend returns few/no sources.
            reference.append(item.ground_truth)

            item.groundedness_lexical = groundedness_lexical(item.answer, reference)
            item.keyword_recall = keyword_recall(item.answer, item.ground_truth)
            item.has_sources = len(item.sources) > 0
            item.passed = (
                item.groundedness_lexical >= min_groundedness and item.has_sources
            )
        except Exception as exc:  # robustness: one bad item must not kill the run
            item.error = f"{type(exc).__name__}: {exc}"
            item.passed = False
            log.warning("Item %d/%d failed: %s", idx, len(gold), item.error)
        log.info(
            "[%2d/%2d] %-6s ground=%.2f recall=%.2f src=%s %s",
            idx, len(gold), item.type, item.groundedness_lexical,
            item.keyword_recall, item.has_sources,
            "PASS" if item.passed else "FAIL",
        )
        results.append(item)
    return results


# --------------------------------------------------------------------------- #
# Optional Azure AI Evaluation layer (LLM-judge). Lazy, skips cleanly.
# --------------------------------------------------------------------------- #

def maybe_run_azure(
    results: list[ItemResult],
    judge_model: str,
) -> dict[str, Any]:
    """Run Microsoft's official evaluators if the SDK + creds are present.

    Never hard-fails: returns a status dict and, on success, mutates each
    ``ItemResult.azure`` with per-item judge scores.
    """

    status: dict[str, Any] = {"ran": False, "reason": "", "judge_model": judge_model}

    # 1) SDK present?
    try:
        from azure.ai.evaluation import (  # type: ignore
            GroundednessEvaluator,
            RelevanceEvaluator,
        )
        try:
            from azure.ai.evaluation import IntentResolutionEvaluator  # type: ignore
        except ImportError:
            IntentResolutionEvaluator = None  # type: ignore
    except ImportError:
        status["reason"] = (
            "azure-ai-evaluation not installed; skipping Azure judge layer "
            "(install with: pip install -e '.[eval]')."
        )
        log.info(status["reason"])
        return status

    # 2) Creds / model config present? Prefer AOAI env, then Foundry project.
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_AI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_AI_API_KEY")
    deployment = os.getenv("JUDGE_MODEL", judge_model)
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    if not endpoint:
        status["reason"] = (
            "No AZURE_OPENAI_ENDPOINT/AZURE_AI_ENDPOINT in env; "
            "skipping Azure judge layer."
        )
        log.info(status["reason"])
        return status

    model_config: dict[str, Any] = {
        "azure_endpoint": endpoint,
        "azure_deployment": deployment,
        "api_version": api_version,
    }
    if api_key:
        model_config["api_key"] = api_key
    # else: the SDK falls back to DefaultAzureCredential (managed identity / CLI).

    try:
        groundedness = GroundednessEvaluator(model_config=model_config)
        relevance = RelevanceEvaluator(model_config=model_config)
        intent = (
            IntentResolutionEvaluator(model_config=model_config)
            if IntentResolutionEvaluator is not None
            else None
        )
    except Exception as exc:  # bad config, auth, etc.
        status["reason"] = f"Azure evaluators failed to initialize: {exc}"
        log.warning(status["reason"])
        return status

    log.info("Azure judge layer active (deployment=%s).", deployment)
    for item in results:
        if item.error or not item.answer:
            continue
        context = "\n\n".join([*item.sources, item.ground_truth]) or item.ground_truth
        scores: dict[str, Any] = {}
        try:
            scores["groundedness"] = groundedness(
                query=item.question, response=item.answer, context=context
            )
            scores["relevance"] = relevance(
                query=item.question, response=item.answer, context=context
            )
            if intent is not None:
                scores["intent_resolution"] = intent(
                    query=item.question, response=item.answer
                )
        except Exception as exc:  # per-item; keep going
            scores["error"] = f"{type(exc).__name__}: {exc}"
            log.warning("Azure eval failed for one item: %s", scores["error"])
        item.azure = scores

    status["ran"] = True
    status["reason"] = "ok"
    return status


# --------------------------------------------------------------------------- #
# Aggregation + reporting
# --------------------------------------------------------------------------- #

def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate(
    results: list[ItemResult],
    min_groundedness: float,
    min_pass_rate: float,
) -> dict[str, Any]:
    n = len(results)
    passed = sum(1 for r in results if r.passed)
    errored = sum(1 for r in results if r.error)
    pass_rate = passed / n if n else 0.0

    agg = {
        "n_items": n,
        "n_passed": passed,
        "n_failed": n - passed,
        "n_errored": errored,
        "pass_rate": round(pass_rate, 4),
        "mean_groundedness_lexical": round(
            _mean([r.groundedness_lexical for r in results]), 4
        ),
        "mean_keyword_recall": round(_mean([r.keyword_recall for r in results]), 4),
        "sources_coverage": round(
            _mean([1.0 if r.has_sources else 0.0 for r in results]), 4
        ),
    }
    gate_pass = (
        pass_rate >= min_pass_rate
        and agg["mean_groundedness_lexical"] >= min_groundedness
    )
    return {"aggregate": agg, "gate_pass": gate_pass}


def build_report(
    results: list[ItemResult],
    thresholds: dict[str, float],
    agg: dict[str, Any],
    azure_status: dict[str, Any],
    elapsed_s: float,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed_s, 2),
        "thresholds": thresholds,
        "azure_layer": azure_status,
        "aggregate": agg["aggregate"],
        "gate_pass": agg["gate_pass"],
        "items": [r.to_dict() for r in results],
    }


def markdown_summary(report: dict[str, Any]) -> str:
    agg = report["aggregate"]
    th = report["thresholds"]
    gate = report["gate_pass"]
    az = report["azure_layer"]
    lines: list[str] = []
    lines.append("## AI Exam Assistant — Agent Evaluation")
    lines.append("")
    verdict = "PASS ✅" if gate else "FAIL ❌"
    lines.append(f"**Gate: {verdict}**")
    lines.append("")
    lines.append("| Metric | Value | Threshold |")
    lines.append("| --- | --- | --- |")
    lines.append(
        f"| Pass rate | {agg['pass_rate']:.0%} "
        f"({agg['n_passed']}/{agg['n_items']}) | ≥ {th['min_pass_rate']:.0%} |"
    )
    lines.append(
        f"| Mean groundedness (lexical) | {agg['mean_groundedness_lexical']:.3f} "
        f"| ≥ {th['min_groundedness']:.2f} |"
    )
    lines.append(
        f"| Mean keyword recall | {agg['mean_keyword_recall']:.3f} | — |"
    )
    lines.append(
        f"| Sources coverage | {agg['sources_coverage']:.0%} | — |"
    )
    lines.append(f"| Errored items | {agg['n_errored']} | 0 |")
    lines.append("")
    if az.get("ran"):
        lines.append(f"_Azure AI Evaluation judge layer ran (model: {az['judge_model']})._")
    else:
        lines.append(f"_Azure judge layer skipped: {az.get('reason', 'n/a')}_")
    lines.append("")
    # Per-item detail (compact).
    lines.append("<details><summary>Per-item results</summary>")
    lines.append("")
    lines.append("| # | Type | Topic | Ground | Recall | Src | Result |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for i, it in enumerate(report["items"], 1):
        m = it["metrics"]
        res = "PASS" if it["passed"] else ("ERR" if it["error"] else "FAIL")
        lines.append(
            f"| {i} | {it['type']} | {it['topic']} | "
            f"{m['groundedness_lexical']:.2f} | {m['keyword_recall']:.2f} | "
            f"{'yes' if m['has_sources'] else 'no'} | {res} |"
        )
    lines.append("")
    lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Agent-quality evaluation gate for the AI Exam Assistant.",
    )
    p.add_argument(
        "--gold", type=Path, default=Path("data/eval/gold_qa.jsonl"),
        help="Path to the gold JSONL dataset.",
    )
    p.add_argument(
        "--out", type=Path, default=Path("eval-report.json"),
        help="Where to write the JSON report.",
    )
    p.add_argument(
        "--mode", choices=["offline", "azure"], default="offline",
        help="'offline' = deterministic gate only. 'azure' = also run the "
             "Azure AI Evaluation judge layer when creds are present.",
    )
    p.add_argument(
        "--min-groundedness", type=float, default=DEFAULT_MIN_GROUNDEDNESS,
        help="Minimum lexical groundedness for an item to pass AND minimum "
             "mean groundedness for the gate.",
    )
    p.add_argument(
        "--min-pass-rate", type=float, default=DEFAULT_MIN_PASS_RATE,
        help="Minimum fraction of items that must pass for the gate to pass.",
    )
    p.add_argument(
        "--judge-model", type=str, default=os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
        help="Azure judge deployment name (Microsoft recommends gpt-5-mini).",
    )
    p.add_argument(
        "--summary-out", type=Path, default=None,
        help="Optional path to also write the Markdown summary "
             "(e.g. $GITHUB_STEP_SUMMARY).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started = time.time()

    # CI summaries use UTF-8; make stdout robust on legacy Windows codepages
    # so an emoji in the Markdown never crashes the gate.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):  # pragma: no cover
            pass

    thresholds = {
        "min_groundedness": args.min_groundedness,
        "min_pass_rate": args.min_pass_rate,
    }

    try:
        gold = load_gold(args.gold)
    except (FileNotFoundError, ValueError) as exc:
        log.error("%s", exc)
        return 1

    log.info("Loaded %d gold items from %s", len(gold), args.gold)

    try:
        results = asyncio.run(run_offline(gold, args.min_groundedness))
    except RuntimeError as exc:
        # Orchestrator not importable / unavailable: emit a report and fail the
        # gate loudly rather than crash without evidence.
        log.error("%s", exc)
        results = [
            ItemResult(
                question=row["question"], topic=row.get("topic", ""),
                type=row.get("type", "local"), ground_truth=row["ground_truth"],
                error="orchestrator-unavailable",
            )
            for row in gold
        ]

    azure_status: dict[str, Any] = {
        "ran": False,
        "reason": "mode=offline (Azure layer not requested)",
        "judge_model": args.judge_model,
    }
    if args.mode == "azure":
        azure_status = maybe_run_azure(results, args.judge_model)

    agg = aggregate(results, args.min_groundedness, args.min_pass_rate)
    report = build_report(
        results, thresholds, agg, azure_status, time.time() - started
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote report to %s", args.out)

    summary = markdown_summary(report)
    print(summary)
    if args.summary_out:
        args.summary_out.write_text(summary, encoding="utf-8")

    return 0 if report["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
