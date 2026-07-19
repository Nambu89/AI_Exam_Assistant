"""Showcase: Microsoft Agent Framework NATIVE orchestration (cloud path).

The always-on coordinator in :mod:`app.agents.orchestrator` is intentionally
simple so the offline demo and the eval gate work without credentials. This
module demonstrates the framework-native orchestration patterns that light up
when a real model provider is configured:

* **Handoff**    — Triage hands full control to a specialist tutor.
* **Concurrent** — Several graders assess the same essay in parallel.
* **Magentic**   — A manager plans an open-ended task ("build me a study plan").

These builders are imported lazily and guarded: the exact symbol paths were
still stabilising in the Agent Framework 1.11 docs (see ARCHITECTURE.md), so we
resolve them defensively and raise a clear error if the installed version
differs. Nothing here runs in offline mode.

Verify against your installed version before relying on it:
    pip show agent-framework
"""

from __future__ import annotations

from typing import Any

from app.agents.prompts import TUTOR
from app.clients.agent_factory import make_agent
from app.config import ModelProvider, get_settings


def _require_cloud() -> None:
    if get_settings().model_provider == ModelProvider.LOCAL:
        raise RuntimeError(
            "Native Agent Framework orchestration requires a cloud provider "
            "(MODEL_PROVIDER=foundry|azure_openai|openai)."
        )


def build_handoff_workflow(subjects: list[str]) -> Any:
    """Triage → per-subject tutor handoff workflow.

    Mirrors the documented pattern::

        HandoffBuilder(participants=[...])
            .with_start_agent(triage)
            .add_handoff(triage, [tutor_a, tutor_b])
            .build()
    """
    _require_cloud()
    from agent_framework.orchestrations import HandoffBuilder  # type: ignore

    triage = make_agent(
        name="triage",
        instructions=(
            "You are a triage agent. Identify the subject the student is asking about "
            "and hand off to the matching subject tutor."
        ),
    )
    tutors = [
        make_agent(name=f"tutor-{s}", instructions=f"{TUTOR}\nYou specialise in: {s}.")
        for s in subjects
    ]

    builder = HandoffBuilder(name="exam_tutor_handoff", participants=[triage, *tutors])
    builder = builder.with_start_agent(triage)
    builder = builder.add_handoff(triage, tutors)
    return builder.build()


def build_concurrent_graders() -> Any:
    """Three graders assess the same free-text answer in parallel, then aggregate."""
    _require_cloud()
    from agent_framework.orchestrations import ConcurrentBuilder  # type: ignore

    lenses = {
        "correctness": "Grade only factual correctness against the syllabus.",
        "completeness": "Grade how complete the answer is.",
        "clarity": "Grade clarity and structure.",
    }
    graders = [make_agent(name=f"grader-{k}", instructions=v) for k, v in lenses.items()]
    return ConcurrentBuilder(participants=graders).build()


def build_study_plan_manager() -> Any:
    """Magentic manager that plans an open-ended study task across specialists."""
    _require_cloud()
    from agent_framework.orchestrations import MagenticBuilder  # type: ignore

    planner = make_agent(
        name="planner", instructions="Break a study goal into an ordered plan of tasks."
    )
    tutor = make_agent(name="tutor", instructions=TUTOR)
    examiner = make_agent(
        name="examiner", instructions="Create checkpoint quizzes for each plan milestone."
    )
    return MagenticBuilder(participants=[planner, tutor, examiner]).build()
