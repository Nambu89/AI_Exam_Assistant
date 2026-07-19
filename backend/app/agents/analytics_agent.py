"""Analytics agent — turns per-topic performance into a study plan.

Deterministic by design (works offline and gives reproducible eval results). In
cloud mode the recommendations can be enriched by the ANALYTICS agent, but the
weak-topic detection stays rule-based for transparency.
"""

from __future__ import annotations

from collections import defaultdict

from app.models.schemas import HistoryItem, RecommendationsResponse

_WEAK_THRESHOLD = 0.6


class AnalyticsAgent:
    def recommendations(self, history: list[HistoryItem]) -> RecommendationsResponse:
        if not history:
            return RecommendationsResponse(
                weak_topics=[],
                recommendations=[
                    "Take a diagnostic exam first so I can pinpoint your weak areas."
                ],
                focus_plan=["Start with a short 5-question exam covering all topics."],
            )

        scores: dict[str, list[float]] = defaultdict(list)
        for h in history:
            scores[h.topic].append(h.score)

        averages = {topic: sum(v) / len(v) for topic, v in scores.items()}
        weak = sorted(
            (t for t, avg in averages.items() if avg < _WEAK_THRESHOLD),
            key=lambda t: averages[t],
        )

        recommendations = [
            f"Focus on '{topic}' — current average {averages[topic]:.0%}. "
            "Re-read the relevant section and take a targeted 5-question exam."
            for topic in weak
        ]
        if not recommendations:
            recommendations = [
                "Solid performance across the board. Move to harder questions to stretch further."
            ]

        focus_plan = [f"Day {i + 1}: drill '{topic}'." for i, topic in enumerate(weak[:5])] or [
            "Maintain a spaced-repetition schedule across all topics."
        ]

        return RecommendationsResponse(
            weak_topics=weak, recommendations=recommendations, focus_plan=focus_plan
        )
