"""Exam agent — composes the generator and the validator, and grades results.

Generation pattern (a real, non-decorative multi-agent step):
    QuestionGeneratorAgent → ValidatorAgent (drop invalid) → top-up if short.
"""

from __future__ import annotations

from collections import defaultdict

from app.agents import exam_builder
from app.agents.question_generator_agent import QuestionGeneratorAgent
from app.agents.validator_agent import ValidatorAgent
from app.models.schemas import (
    Answer,
    Difficulty,
    Exam,
    GradeResult,
    PerQuestionResult,
    Question,
)


class ExamAgent:
    def __init__(self) -> None:
        self._generator = QuestionGeneratorAgent()
        self._validator = ValidatorAgent()

    async def generate_exam(
        self,
        subject: str,
        topics: list[str],
        num_questions: int,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> Exam:
        exam = await self._generator.generate(subject, topics, num_questions, difficulty)

        valid: list[Question] = []
        for q in exam.questions:
            verdict = await self._validator.validate(q)
            if verdict.valid:
                valid.append(q)

        # Top up deterministically if validation dropped some questions.
        if len(valid) < num_questions:
            backup = exam_builder.build_questions(
                subject, topics, num_questions - len(valid), difficulty, seed=len(valid) + 7
            )
            existing = {q.stem for q in valid}
            for q in backup.questions:
                if q.stem not in existing:
                    valid.append(q)

        # Renumber ids for a clean sequence.
        for i, q in enumerate(valid[:num_questions], start=1):
            q.id = f"q{i}"
        exam.questions = valid[:num_questions]
        return exam

    @staticmethod
    def grade(questions: list[Question], answers: list[Answer]) -> GradeResult:
        answer_by_id = {a.question_id: a.choice for a in answers}
        per_question: list[PerQuestionResult] = []
        topic_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [correct, total]

        for q in questions:
            chosen = answer_by_id.get(q.id)
            is_correct = chosen == q.correct
            topic_totals[q.topic][1] += 1
            if is_correct:
                topic_totals[q.topic][0] += 1
            per_question.append(
                PerQuestionResult(
                    question_id=q.id,
                    your_choice=chosen,
                    correct=q.correct,
                    is_correct=is_correct,
                    explanation=q.explanation,
                    topic=q.topic,
                )
            )

        total = len(questions)
        correct_count = sum(1 for p in per_question if p.is_correct)
        weak_topics = [
            topic for topic, (c, t) in topic_totals.items() if t and (c / t) < 0.6
        ]
        recommendations = [
            f"Review '{topic}': you scored below 60% there." for topic in weak_topics
        ] or ["Great job — keep practising to reinforce your strong topics."]

        return GradeResult(
            score=round(correct_count / total, 4) if total else 0.0,
            correct_count=correct_count,
            total=total,
            per_question=per_question,
            weak_topics=weak_topics,
            recommendations=recommendations,
        )
