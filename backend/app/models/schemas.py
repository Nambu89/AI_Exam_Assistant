"""Pydantic models shared by the API and the agents. Mirrors docs/API.md."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

Choice = Literal["A", "B", "C", "D"]


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ---------- Chat ----------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    mode: Literal["local", "global", "drift"] | None = None


class ChatResponse(BaseModel):
    response: str
    agent_used: str
    route: str
    mode: str
    sources: list[str] = Field(default_factory=list)
    session_id: str


# ---------- Exam ----------
class ExamGenerateRequest(BaseModel):
    subject: str = "az-900"
    topics: list[str] = Field(default_factory=list)
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Difficulty = Difficulty.MEDIUM


class Question(BaseModel):
    id: str
    stem: str
    options: dict[Choice, str]
    correct: Choice
    explanation: str
    topic: str
    sources: list[str] = Field(default_factory=list)


class Exam(BaseModel):
    exam_id: str
    subject: str
    questions: list[Question]


class Answer(BaseModel):
    question_id: str
    choice: Choice | None = None


class GradeRequest(BaseModel):
    exam_id: str | None = None
    questions: list[Question]
    answers: list[Answer]


class PerQuestionResult(BaseModel):
    question_id: str
    your_choice: Choice | None
    correct: Choice
    is_correct: bool
    explanation: str
    topic: str


class GradeResult(BaseModel):
    score: float
    correct_count: int
    total: int
    per_question: list[PerQuestionResult]
    weak_topics: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ---------- Concept map ----------
class ConceptNode(BaseModel):
    id: str
    label: str
    community: int = 0
    size: float = 1.0


class ConceptEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0


class Community(BaseModel):
    id: int
    title: str
    summary: str = ""


class ConceptMap(BaseModel):
    subject: str
    backend: str
    nodes: list[ConceptNode]
    edges: list[ConceptEdge]
    communities: list[Community] = Field(default_factory=list)


# ---------- Analytics ----------
class HistoryItem(BaseModel):
    subject: str = "az-900"
    topic: str
    score: float = Field(ge=0.0, le=1.0)


class RecommendationsRequest(BaseModel):
    history: list[HistoryItem] = Field(default_factory=list)


class RecommendationsResponse(BaseModel):
    weak_topics: list[str]
    recommendations: list[str]
    focus_plan: list[str] = Field(default_factory=list)


# ---------- Topics ----------
class SubjectInfo(BaseModel):
    id: str
    title: str
    topics: list[str]


class TopicsResponse(BaseModel):
    subjects: list[SubjectInfo]
