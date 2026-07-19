"""Question generator agent.

Cloud mode: a GPT-5 agent writes MCQs grounded in retrieved context and returns
JSON. Any parsing/grounding failure falls back to the deterministic
:mod:`app.agents.exam_builder` so the endpoint never returns garbage.
Offline mode: uses the deterministic builder directly.
"""

from __future__ import annotations

import json
import re
import uuid

from app.agents import exam_builder
from app.agents.prompts import QUESTION_GENERATOR
from app.clients.agent_factory import make_agent
from app.config import get_settings
from app.knowledge.base import SearchMode
from app.knowledge.factory import get_retriever
from app.models.schemas import Difficulty, Exam, Question


def _extract_json(text: str) -> list[dict]:
    """Pull the first JSON array out of an LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array in response")
    return json.loads(text[start : end + 1])


class QuestionGeneratorAgent:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._retriever = get_retriever()
        self._agent = make_agent(
            name="question-generator",
            instructions=QUESTION_GENERATOR,
            model=self._settings.chat_model,
        )

    async def generate(
        self,
        subject: str,
        topics: list[str],
        num_questions: int,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> Exam:
        if self._settings.is_offline:
            return exam_builder.build_questions(subject, topics, num_questions, difficulty)

        topic_str = ", ".join(topics) if topics else "all topics"
        query = f"Key testable concepts for {subject}: {topic_str}"
        result = await self._retriever.search(query, SearchMode.GLOBAL)
        prompt = (
            f"CONTEXT:\n{result.context}\n\n"
            f"Write {num_questions} {difficulty.value} multiple-choice questions "
            f"about {subject} ({', '.join(topics) if topics else 'any topic'}). "
            "Return only the JSON array described in your instructions."
        )
        try:
            run = await self._agent.run(prompt)
            raw = _extract_json(run.text)
            questions = self._to_questions(raw, result.sources)
            if questions:
                return Exam(exam_id=str(uuid.uuid4()), subject=subject, questions=questions)
        except Exception:  # noqa: BLE001 - fall back to deterministic builder
            pass
        return exam_builder.build_questions(subject, topics, num_questions, difficulty)

    @staticmethod
    def _to_questions(raw: list[dict], sources: list[str]) -> list[Question]:
        questions: list[Question] = []
        for i, item in enumerate(raw, start=1):
            options = item.get("options", {})
            correct = str(item.get("correct", "")).strip().upper()
            if set(options) < {"A", "B", "C", "D"} or correct not in ("A", "B", "C", "D"):
                continue
            questions.append(
                Question(
                    id=f"q{i}",
                    stem=str(item["stem"]),
                    options={k: str(options[k]) for k in ("A", "B", "C", "D")},  # type: ignore[arg-type]
                    correct=correct,  # type: ignore[arg-type]
                    explanation=str(item.get("explanation", "")),
                    topic=str(item.get("topic", "General")),
                    sources=item.get("sources") or sources[:2],
                )
            )
        return questions
