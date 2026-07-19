"""Orchestrator — the multi-agent entry point used by the API and the evals.

Flow for ``chat``:
    guardrails → CoordinatorAgent routes → dispatch to Tutor / Exam / Analytics.

This is a deliberate, readable orchestration over Microsoft Agent Framework
agents. The framework-native orchestration builders (Handoff / Magentic /
Concurrent) are showcased separately in :mod:`app.agents.af_orchestration` for
the cloud path; this coordinator keeps the always-on, offline-capable path
simple and testable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.agents.analytics_agent import AnalyticsAgent
from app.agents.exam_agent import ExamAgent
from app.agents.router import CoordinatorAgent
from app.agents.tutor_agent import TutorAgent
from app.knowledge.base import SearchMode
from app.models.schemas import (
    Answer,
    Difficulty,
    Exam,
    GradeResult,
    HistoryItem,
    Question,
    RecommendationsResponse,
)
from app.security.guardrails import check_input


@dataclass(slots=True)
class ChatResult:
    response: str
    agent_used: str
    route: str
    mode: str
    sources: list[str] = field(default_factory=list)
    session_id: str = ""


class Orchestrator:
    def __init__(self) -> None:
        self._coordinator = CoordinatorAgent()
        self._tutor = TutorAgent()
        self._exam = ExamAgent()
        self._analytics = AnalyticsAgent()
        self._sessions: dict[str, list[str]] = {}

    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        mode: SearchMode | None = None,
    ) -> ChatResult:
        session_id = session_id or str(uuid.uuid4())

        guard = await check_input(message)
        if not guard.allowed:
            return ChatResult(
                response=f"I can't help with that. ({guard.reason})",
                agent_used="guardrail",
                route="blocked",
                mode=(mode or SearchMode.DRIFT).value,
                session_id=session_id,
            )

        route = await self._coordinator.route(message)
        self._sessions.setdefault(session_id, []).append(message)

        if route == "analytics":
            recs = self._analytics.recommendations([])
            text = " ".join(recs.recommendations)
            return ChatResult(
                text, "analytics", route, (mode or SearchMode.DRIFT).value, [], session_id
            )

        if route == "exam":
            sample = await self._exam.generate_exam("az-900", [], 1, Difficulty.MEDIUM)
            if sample.questions:
                q = sample.questions[0]
                opts = "\n".join(f"  {k}) {v}" for k, v in q.options.items())
                text = (
                    "Here's a quick practice question — head to the Exam tab for a full test:\n\n"
                    f"{q.stem}\n{opts}"
                )
                return ChatResult(
                    text, "exam", route, (mode or SearchMode.DRIFT).value, q.sources, session_id
                )

        # Default: tutor.
        answer = await self._tutor.answer(message, mode or SearchMode.DRIFT)
        return ChatResult(
            response=answer.text,
            agent_used="tutor",
            route=route if route in ("tutor", "exam", "analytics") else "tutor",
            mode=answer.mode.value,
            sources=answer.sources,
            session_id=session_id,
        )

    # ---- Exam ----
    async def generate_exam(
        self,
        subject: str,
        topics: list[str],
        num_questions: int,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> Exam:
        return await self._exam.generate_exam(subject, topics, num_questions, difficulty)

    def grade_exam(self, questions: list[Question], answers: list[Answer]) -> GradeResult:
        return ExamAgent.grade(questions, answers)

    # ---- Analytics ----
    def recommendations(self, history: list[HistoryItem]) -> RecommendationsResponse:
        return self._analytics.recommendations(history)
