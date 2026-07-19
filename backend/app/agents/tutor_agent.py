"""Tutor agent — grounded conversational answers.

Cloud mode: retrieves context (Foundry IQ / GraphRAG), then a GPT-5 agent answers
strictly from that context.
Offline mode: extractive answer synthesised from the retrieved corpus sections —
no LLM, still grounded and cited.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.agents.prompts import TUTOR
from app.clients.agent_factory import make_agent
from app.config import get_settings
from app.knowledge.base import RetrievalResult, SearchMode
from app.knowledge.factory import get_retriever


@dataclass(slots=True)
class TutorAnswer:
    text: str
    sources: list[str]
    mode: SearchMode
    backend: str


def _extractive_answer(question: str, result: RetrievalResult) -> str:
    """Offline synthesis: stitch the most relevant sentences into a short answer."""
    if result.is_empty:
        return (
            "I couldn't find this in the study material. Try rephrasing, or study the "
            "related topic and ask again."
        )
    sentences: list[str] = []
    for chunk in result.chunks[:3]:
        body = re.sub(r"^##.*\n", "", chunk.text).strip()
        for sent in re.split(r"(?<=[.!?])\s+", body):
            if 30 <= len(sent) <= 320:
                sentences.append(sent.strip())
            if len(sentences) >= 5:
                break
        if len(sentences) >= 5:
            break
    body = " ".join(sentences)
    return f"Based on the study material:\n\n{body}"


class TutorAgent:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._retriever = get_retriever()
        self._agent = make_agent(name="tutor", instructions=TUTOR, model=self._settings.chat_model)

    async def answer(self, message: str, mode: SearchMode = SearchMode.DRIFT) -> TutorAnswer:
        result = await self._retriever.search(message, mode)

        if self._settings.is_offline:
            text = _extractive_answer(message, result)
        else:
            prompt = (
                f"CONTEXT (the only source you may use):\n{result.context}\n\n"
                f"QUESTION: {message}\n\n"
                "Answer using only the context above. If it is insufficient, say so."
            )
            run = await self._agent.run(prompt)
            text = run.text

        return TutorAnswer(
            text=text, sources=result.sources, mode=result.mode, backend=result.backend
        )
