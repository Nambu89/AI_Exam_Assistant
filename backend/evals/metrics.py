"""Pure, deterministic scoring functions for the offline evaluation gate.

These metrics need **no LLM and no network**, so they run in CI on every push
and act as the hard quality gate for the AI Exam Assistant agent.  Every
function here is a pure function of its inputs: same input -> same output.
They are exercised by ``test_metrics.py`` in the normal backend test suite.

Design notes
------------
The offline gate is intentionally *lexical*.  It cannot judge nuance the way an
LLM judge can, but it is cheap, reproducible and impossible to game with an
empty or off-topic answer.  It answers two blunt questions:

* **groundedness_lexical** -- of the content words the agent actually said, what
  fraction is backed by a trusted reference (the retrieved source text and/or
  the gold ``ground_truth``)?  This is a *precision*-style score that punishes
  hallucinated, unsupported prose.
* **keyword_recall** -- of the salient keywords in the gold answer, what
  fraction did the agent actually mention?  This is a *recall*-style score that
  punishes vague, incomplete answers.

Both live in ``[0, 1]``.  Together they bracket an answer: it must be both
supported (groundedness) and complete (recall) to score well.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

__all__ = [
    "STOPWORDS",
    "tokenize",
    "content_tokens",
    "extract_salient_keywords",
    "groundedness_lexical",
    "keyword_recall",
]

# A small, fixed English stopword list.  Kept inline (no NLTK download) so the
# metric stays deterministic and offline.  Deliberately conservative: we only
# drop words that carry no topical signal.
STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
        "at", "by", "for", "with", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below", "to", "from",
        "up", "down", "in", "out", "on", "off", "over", "under", "again",
        "further", "is", "are", "was", "were", "be", "been", "being", "have",
        "has", "had", "having", "do", "does", "did", "doing", "will", "would",
        "should", "could", "can", "may", "might", "must", "shall", "this",
        "that", "these", "those", "of", "as", "such", "which", "who", "whom",
        "what", "where", "why", "how", "it", "its", "they", "them", "their",
        "you", "your", "we", "our", "he", "she", "his", "her", "not", "no",
        "so", "than", "too", "very", "just", "also", "more", "most", "some",
        "any", "each", "both", "other", "only", "own", "same", "there", "here",
        "one", "two", "i", "me", "my",
    }
)

# Minimum length for a token to count as a "content" token.  Acronyms in the
# Azure/cloud domain (VM, AI, ML, RBAC, IAM, SLA...) are short but meaningful,
# so short tokens are rescued below when they look like acronyms.
_MIN_CONTENT_LEN = 3

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
_ACRONYM_RE = re.compile(r"^[A-Z0-9]{2,}$")


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, keep intra-token ``.``/``-``.

    Keeping ``.`` and ``-`` inside a token preserves domain terms like
    ``az-900``, ``gpt-5-mini`` or ``pay-as-you-go`` as single units.
    """

    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())


def content_tokens(text: str) -> set[str]:
    """Set of meaningful tokens: stopwords and trivial tokens removed.

    Short tokens (< ``_MIN_CONTENT_LEN``) are dropped **unless** they appear in
    the original text as an uppercase acronym (e.g. ``VM``, ``AI``), which is
    common and load-bearing in this cloud-certification domain.
    """

    if not text:
        return set()

    # Acronyms are detected on the raw (cased) text, then lowercased to match.
    acronyms = {w.lower() for w in re.findall(r"\b[A-Z0-9]{2,}\b", text) if _ACRONYM_RE.match(w)}

    out: set[str] = set()
    for tok in tokenize(text):
        if tok in STOPWORDS:
            continue
        if len(tok) >= _MIN_CONTENT_LEN or tok in acronyms:
            out.add(tok)
    return out


def extract_salient_keywords(text: str) -> list[str]:
    """Ordered, de-duplicated list of salient keywords from a reference answer.

    Salient == content tokens (see :func:`content_tokens`) in first-seen order.
    Order is preserved and duplicates removed so the result is stable and human
    readable in the report, while :func:`keyword_recall` treats it as a set.
    """

    if not text:
        return []
    salient = content_tokens(text)
    seen: dict[str, None] = {}
    for tok in tokenize(text):
        if tok in salient and tok not in seen:
            seen[tok] = None
    return list(seen)


def _flatten(reference: str | Iterable[str] | None) -> str:
    if reference is None:
        return ""
    if isinstance(reference, str):
        return reference
    return " ".join(str(r) for r in reference if r)


def groundedness_lexical(answer: str, reference: str | Iterable[str] | None) -> float:
    """Fraction of the answer's content tokens supported by the reference.

    Formula (precision of the answer against trusted text)::

        groundedness = | content(answer) ∩ content(reference) | / | content(answer) |

    where ``content(x)`` is the set of non-stopword tokens of ``x`` and
    ``reference`` is the concatenation of the retrieved source text and/or the
    gold ``ground_truth``.

    * Returns ``0.0`` if the answer has no content tokens (empty / junk answer).
    * Returns ``0.0`` if there is no reference to ground against (we cannot
      certify an ungrounded answer — fail closed).
    * Result is always in ``[0, 1]``.
    """

    ans = content_tokens(answer)
    if not ans:
        return 0.0
    ref = content_tokens(_flatten(reference))
    if not ref:
        return 0.0
    overlap = len(ans & ref)
    return overlap / len(ans)


def keyword_recall(answer: str, ground_truth: str) -> float:
    """Fraction of the gold answer's salient keywords present in the answer.

    Formula (recall of expected keywords)::

        keyword_recall = | keywords(ground_truth) ∩ content(answer) |
                         / | keywords(ground_truth) |

    * Returns ``1.0`` vacuously if the ground truth has no salient keywords
      (nothing to recall), so a degenerate gold row cannot sink the score.
    * Returns ``0.0`` if the answer is empty.
    * Result is always in ``[0, 1]``.
    """

    keywords = set(extract_salient_keywords(ground_truth))
    if not keywords:
        return 1.0
    ans = content_tokens(answer)
    if not ans:
        return 0.0
    hit = len(keywords & ans)
    return hit / len(keywords)


def clamp01(x: float) -> float:
    """Utility: clamp a float into ``[0, 1]`` (guards against fp drift)."""

    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x
