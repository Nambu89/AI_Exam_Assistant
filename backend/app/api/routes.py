"""HTTP API — conforms to docs/API.md."""

from __future__ import annotations

import asyncio
import json
from functools import lru_cache

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app import __version__
from app.agents.orchestrator import Orchestrator
from app.config import get_settings
from app.knowledge.base import SearchMode
from app.knowledge.concept_graph import build_concept_map, corpus_subjects
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConceptMap,
    ExamGenerateRequest,
    GradeRequest,
    GradeResult,
    RecommendationsRequest,
    RecommendationsResponse,
    SubjectInfo,
    TopicsResponse,
)

router = APIRouter(prefix="/api")


@lru_cache
def get_orchestrator() -> Orchestrator:
    return Orchestrator()


def _mode(value: str | None) -> SearchMode | None:
    return SearchMode(value) if value else None


@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "provider": s.model_provider.value,
        "knowledge_backend": s.knowledge_backend.value,
        "version": __version__,
    }


@router.get("/topics", response_model=TopicsResponse)
async def topics() -> TopicsResponse:
    subjects = [
        SubjectInfo(id=sid, title=title, topics=topics_)
        for sid, title, topics_ in corpus_subjects()
    ]
    return TopicsResponse(subjects=subjects)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    result = await get_orchestrator().chat(req.message, req.session_id, _mode(req.mode))
    return ChatResponse(
        response=result.response,
        agent_used=result.agent_used,
        route=result.route,
        mode=result.mode,
        sources=result.sources,
        session_id=result.session_id,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> EventSourceResponse:
    orch = get_orchestrator()

    async def event_gen():
        result = await orch.chat(req.message, req.session_id, _mode(req.mode))
        yield {"data": json.dumps({"type": "route", "agent": result.agent_used})}
        # Stream the answer in word chunks for a responsive UI.
        words = result.response.split(" ")
        buf: list[str] = []
        for i, word in enumerate(words):
            buf.append(word)
            if len(buf) >= 6 or i == len(words) - 1:
                yield {"data": json.dumps({"type": "token", "text": " ".join(buf) + " "})}
                buf = []
                await asyncio.sleep(0.02)
        yield {"data": json.dumps({"type": "sources", "sources": result.sources})}
        yield {"data": json.dumps({"type": "done", "session_id": result.session_id})}

    return EventSourceResponse(event_gen())


@router.post("/exam/generate")
async def exam_generate(req: ExamGenerateRequest) -> dict:
    exam = await get_orchestrator().generate_exam(
        req.subject, req.topics, req.num_questions, req.difficulty
    )
    return exam.model_dump()


@router.post("/exam/grade", response_model=GradeResult)
async def exam_grade(req: GradeRequest) -> GradeResult:
    return get_orchestrator().grade_exam(req.questions, req.answers)


@router.get("/concept-map", response_model=ConceptMap)
async def concept_map(subject: str = "az-900", level: int = 1) -> ConceptMap:
    return build_concept_map(subject, level)


@router.post("/analytics/recommendations", response_model=RecommendationsResponse)
async def recommendations(req: RecommendationsRequest) -> RecommendationsResponse:
    return get_orchestrator().recommendations(req.history)
