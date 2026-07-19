"""Deterministic unit tests for the offline eval metrics.

No network, no LLM, no orchestrator import -- these run in the normal backend
test suite (``pytest backend``) and protect the CI gate itself from regressing.
"""

from __future__ import annotations

import math

import pytest

from evals.metrics import (
    content_tokens,
    extract_salient_keywords,
    groundedness_lexical,
    keyword_recall,
    tokenize,
)

# --------------------------------------------------------------------------- #
# tokenize / content_tokens
# --------------------------------------------------------------------------- #

def test_tokenize_lowercases_and_splits():
    assert tokenize("Vertical Scaling, up!") == ["vertical", "scaling", "up"]


def test_tokenize_preserves_domain_terms():
    # Intra-token '.' and '-' are kept so domain terms survive as one unit.
    assert tokenize("az-900 and gpt-5-mini") == ["az-900", "and", "gpt-5-mini"]


def test_tokenize_empty():
    assert tokenize("") == []
    assert tokenize(None) == []  # type: ignore[arg-type]


def test_content_tokens_drops_stopwords():
    toks = content_tokens("the scaling of a virtual machine")
    assert "scaling" in toks
    assert "virtual" in toks
    assert "machine" in toks
    assert "the" not in toks
    assert "of" not in toks
    assert "a" not in toks


def test_content_tokens_rescues_acronyms():
    toks = content_tokens("A VM runs AI workloads")
    # 'vm' and 'ai' are length 2 but uppercase acronyms in the source -> kept.
    assert "vm" in toks
    assert "ai" in toks


def test_content_tokens_drops_short_non_acronyms():
    # lowercase two-letter noise words that are not acronyms are dropped
    toks = content_tokens("go to hq")
    assert "go" not in toks


# --------------------------------------------------------------------------- #
# extract_salient_keywords
# --------------------------------------------------------------------------- #

def test_salient_keywords_order_and_dedup():
    kws = extract_salient_keywords("Scaling scaling virtual machine machine")
    assert kws == ["scaling", "virtual", "machine"]


def test_salient_keywords_empty():
    assert extract_salient_keywords("") == []
    assert extract_salient_keywords("the of a an") == []


# --------------------------------------------------------------------------- #
# groundedness_lexical
# --------------------------------------------------------------------------- #

def test_groundedness_full_support():
    # Every content token of the answer appears in the reference -> 1.0
    answer = "Horizontal scaling adds instances"
    reference = "Horizontal scaling adds or removes instances behind a load balancer"
    assert groundedness_lexical(answer, reference) == pytest.approx(1.0)


def test_groundedness_partial():
    answer = "scaling instances teleportation"  # 3 content tokens
    reference = "scaling adds instances"  # supports 2 of 3
    assert groundedness_lexical(answer, reference) == pytest.approx(2 / 3)


def test_groundedness_empty_answer_is_zero():
    assert groundedness_lexical("", "some reference text") == 0.0
    assert groundedness_lexical("the a of", "reference") == 0.0


def test_groundedness_no_reference_fails_closed():
    assert groundedness_lexical("real content here", "") == 0.0
    assert groundedness_lexical("real content here", None) == 0.0


def test_groundedness_accepts_iterable_reference():
    answer = "capex opex"
    refs = ["capex is upfront", "opex is ongoing"]
    assert groundedness_lexical(answer, refs) == pytest.approx(1.0)


def test_groundedness_in_unit_interval():
    val = groundedness_lexical("some partly grounded answer text", "grounded answer")
    assert 0.0 <= val <= 1.0


# --------------------------------------------------------------------------- #
# keyword_recall
# --------------------------------------------------------------------------- #

def test_keyword_recall_full():
    gt = "vertical scaling increases resources"
    answer = "vertical scaling increases the resources of one instance"
    assert keyword_recall(answer, gt) == pytest.approx(1.0)


def test_keyword_recall_partial():
    gt = "capex opex depreciation"  # 3 keywords
    answer = "capex and opex explained"  # hits 2
    assert keyword_recall(answer, gt) == pytest.approx(2 / 3)


def test_keyword_recall_empty_answer_is_zero():
    assert keyword_recall("", "capex opex") == 0.0


def test_keyword_recall_empty_ground_truth_is_vacuous_one():
    assert keyword_recall("anything", "") == 1.0
    assert keyword_recall("anything", "the a of an") == 1.0


def test_keyword_recall_in_unit_interval():
    val = keyword_recall("partial answer", "several important expected keywords here")
    assert 0.0 <= val <= 1.0
    assert not math.isnan(val)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
