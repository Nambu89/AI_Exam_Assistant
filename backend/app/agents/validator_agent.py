"""Validator agent — quality gate for generated questions.

Offline mode: deterministic structural checks (always run).
Cloud mode: additionally asks a GPT-5 agent whether the answer is supported by
the context and unambiguous.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.agents.prompts import VALIDATOR
from app.clients.agent_factory import make_agent
from app.config import get_settings
from app.models.schemas import Question


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    reason: str = ""


def structural_check(q: Question) -> ValidationResult:
    if not q.stem.strip():
        return ValidationResult(False, "empty stem")
    if set(q.options) != {"A", "B", "C", "D"}:
        return ValidationResult(False, "must have exactly options A-D")
    values = [v.strip() for v in q.options.values()]
    if any(not v for v in values):
        return ValidationResult(False, "empty option")
    if len(set(values)) != 4:
        return ValidationResult(False, "duplicate options")
    if q.correct not in q.options:
        return ValidationResult(False, "correct answer not among options")
    return ValidationResult(True)


class ValidatorAgent:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._agent = make_agent(
            name="validator",
            instructions=VALIDATOR,
            model=self._settings.reasoning_model,
        )

    async def validate(self, question: Question, context: str = "") -> ValidationResult:
        structural = structural_check(question)
        if not structural.valid or self._settings.is_offline or not context:
            return structural
        prompt = (
            f"CONTEXT:\n{context}\n\nQUESTION: {question.stem}\n"
            f"OPTIONS: {json.dumps(question.options)}\n"
            f"STATED CORRECT: {question.correct}\n"
            "Is this question valid per your rules? Return the JSON verdict."
        )
        try:
            run = await self._agent.run(prompt)
            data = json.loads(run.text[run.text.find("{") : run.text.rfind("}") + 1])
            return ValidationResult(bool(data.get("valid", True)), str(data.get("reason", "")))
        except Exception:  # noqa: BLE001 - trust structural check if judge unavailable
            return structural
