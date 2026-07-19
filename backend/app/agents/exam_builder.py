"""Deterministic, corpus-grounded MCQ builder.

Powers offline exam generation and acts as the safety net when the LLM path
fails to return valid JSON. It mines "<Concept> is/are/provides ..." definition
sentences from the corpus and turns them into multiple-choice questions whose
correct answer is a real sentence from the material and whose distractors are
definitions of *other* concepts — so every question is grounded and traceable.
"""

from __future__ import annotations

import random
import re
import uuid

from app.knowledge.local_corpus import corpus_dir
from app.models.schemas import Choice, Difficulty, Exam, Question

_DEF_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z0-9][A-Za-z0-9]+){0,4})\s+"
    r"(is|are|refers to|provides|enables|allows|represents|defines)\s+(.+?)(?:\.|;)",
)
_LETTERS: list[Choice] = ["A", "B", "C", "D"]


def _file_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("-", " ").title()


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[0].upper() + s[1:] if s else s


class DefinitionPair:
    __slots__ = ("concept", "definition", "topic", "source")

    def __init__(self, concept: str, definition: str, topic: str, source: str):
        self.concept = concept
        self.definition = definition
        self.topic = topic
        self.source = source


def extract_definitions(subject: str) -> list[DefinitionPair]:
    root = corpus_dir()
    subject_dir = root / subject
    files = (
        sorted(subject_dir.rglob("*.md")) if subject_dir.exists() else sorted(root.rglob("*.md"))
    )
    pairs: list[DefinitionPair] = []
    for md in files:
        if md.name.lower() == "readme.md":
            continue
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(root).as_posix()
        topic = _file_title(text, md.stem)
        for m in _DEF_RE.finditer(text):
            concept = _clean(m.group(1))
            verb = m.group(2)
            body = _clean(m.group(3))
            if len(body) < 20 or len(body) > 200:
                continue
            definition = f"{verb.capitalize()} {body}."
            pairs.append(DefinitionPair(concept, definition, topic, f"{rel}#{topic}"))
    # De-duplicate by concept, keep first (usually the primary definition).
    seen: set[str] = set()
    unique: list[DefinitionPair] = []
    for p in pairs:
        key = p.concept.lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def build_questions(
    subject: str,
    topics: list[str],
    num_questions: int,
    difficulty: Difficulty = Difficulty.MEDIUM,
    seed: int = 42,
) -> Exam:
    rng = random.Random(seed)
    pairs = extract_definitions(subject)

    wanted = {t.strip().lower() for t in topics if t.strip()}
    if wanted:
        pool = [p for p in pairs if p.topic.lower() in wanted]
        if not pool:  # topic strings didn't match titles; fall back to all
            pool = pairs
    else:
        pool = pairs

    if len(pool) < 4:
        pool = pairs  # need at least 4 distinct definitions for distractors

    rng.shuffle(pool)
    selected = pool[: max(0, num_questions)]
    all_defs = [p.definition for p in pairs]

    questions: list[Question] = []
    for i, pair in enumerate(selected, start=1):
        distractor_pool = [d for d in all_defs if d != pair.definition]
        distractors = rng.sample(distractor_pool, k=min(3, len(distractor_pool)))
        options_text = [pair.definition, *distractors]
        rng.shuffle(options_text)
        correct_idx = options_text.index(pair.definition)
        options = {
            letter: _truncate(text) for letter, text in zip(_LETTERS, options_text, strict=False)
        }
        questions.append(
            Question(
                id=f"q{i}",
                stem=f"Which statement best describes {pair.concept}?",
                options=options,  # type: ignore[arg-type]
                correct=_LETTERS[correct_idx],
                explanation=(
                    f"{pair.concept} {pair.definition[0].lower()}{pair.definition[1:]} "
                    f"(source: {pair.source})."
                ),
                topic=pair.topic,
                sources=[pair.source],
            )
        )

    return Exam(exam_id=str(uuid.uuid4()), subject=subject, questions=questions)


def _truncate(s: str, n: int = 160) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"
