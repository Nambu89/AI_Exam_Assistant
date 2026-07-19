"""Coordinator / router agent.

Cloud mode: a cheap model (``gpt-5-nano``) classifies the message.
Offline mode: deterministic keyword routing (also used as the fallback when the
model returns something unexpected).
"""

from __future__ import annotations

from app.agents.prompts import COORDINATOR
from app.clients.agent_factory import make_agent
from app.config import get_settings

VALID_ROUTES = ("tutor", "exam", "analytics")

_EXAM_KW = ("exam", "test", "quiz", "practice", "question", "practise")
_ANALYTICS_KW = (
    "progress", "weak", "improve", "recommend", "advice", "statistic", "score", "how am i",
)


def keyword_route(message: str) -> str:
    m = message.lower()
    if any(k in m for k in _EXAM_KW):
        return "exam"
    if any(k in m for k in _ANALYTICS_KW):
        return "analytics"
    return "tutor"


class CoordinatorAgent:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._agent = make_agent(
            name="coordinator",
            instructions=COORDINATOR,
            model=self._settings.router_model,
            offline_fn=lambda msg: keyword_route(msg),
        )

    async def route(self, message: str) -> str:
        result = await self._agent.run(message)
        route = result.text.strip().lower().replace(".", "").replace(",", "")
        route = route.split()[0] if route else "tutor"
        return route if route in VALID_ROUTES else keyword_route(message)
