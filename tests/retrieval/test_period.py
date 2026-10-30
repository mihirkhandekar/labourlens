from datetime import date

import pytest

from labourlens.retrieval import period as pd_

Q = pd_.Hints


def qs(text):
    return pd_.parse(text).quarters


@pytest.mark.parametrize("text,expected", [
    ("What was the unemployment rate in 1Q 2026?", {(2026, 1)}),
    ("unemployment in 1Q2026", {(2026, 1)}),
    ("Q1 2026 retrenchments", {(2026, 1)}),
    ("retrenchments in Q4-2025", {(2025, 4)}),
    ("2025 Q3 vacancies", {(2025, 3)}),
    ("In the first quarter of 2026, how many were retrenched?", {(2026, 1)}),
    ("the 4th quarter 2025 headline", {(2025, 4)}),
    ("2Q'26 advance estimate", {(2026, 2)}),
    ("What happened in September 2025?", {(2025, 3)}),
    ("In Dec 2025 and Jan. 2026", {(2025, 4), (2026, 1)}),
])
def test_period_forms(text, expected):
    assert qs(text) == expected


@pytest.mark.parametrize("text", [
    "How did unemployment change?",
    "What did Q2 show?",  # quarter without year
    "What was the rate in September?",  # month without year
    "Compare the 2025 annual figures",  # bare year
    "Is the 3 Q ratio rising?",
    "Retrenchments of 12 000 in 2026 were high",
])
def test_no_period_hint(text):
    assert qs(text) == frozenset()


def test_month_after_publication_word_is_not_a_reference_period():
    assert qs("What did the report published in December 2025 say?") == frozenset()
    assert qs("the release issued on March 2026 shows 2Q 2026 data") == {(2026, 2)}


def test_ranges_expand_and_lists_do_not():
    assert qs("trend from 3Q 2025 to 2Q 2026") == {(2025, 3), (2025, 4), (2026, 1), (2026, 2)}
    assert qs("change between 1Q 2025 and 1Q 2026") == {(2025, 1), (2026, 1)}  # 'and' names endpoints only
    assert qs("Q4 2025 - Q2 2026") == {(2025, 4), (2026, 1), (2026, 2)}
    assert len(qs("1Q 2010 to 1Q 2026")) == 2  # implausibly long range is not expanded


def test_overlapping_patterns_count_once():
    assert qs("Q1 2026 (1Q 2026)") == {(2026, 1)}


@pytest.mark.parametrize("text,stage,conflict", [
    ("What did the advance release say?", "advance", False),
    ("preliminary estimate of unemployment", "advance", False),
    ("What does the final report say?", "final", False),
    ("full report headline", "final", False),
    ("According to the Labour Market Report, ...", "final", False),
    ("Labour Market Advance Release 1Q 2026", "advance", False),
    ("Did the advance figure differ from the final figure?", None, True),
    ("What was the unemployment rate?", None, False),
])
def test_stage_hints(text, stage, conflict):
    h = pd_.parse(text)
    assert (h.stage, h.stage_conflict) == (stage, conflict)


DOCS = (
    pd_.Doc("adv-q1", "advance", date(2026, 1, 1), date(2026, 3, 31)),
    pd_.Doc("fin-q1", "final", date(2026, 1, 1), date(2026, 3, 31)),
    pd_.Doc("fin-q4", "final", date(2025, 10, 1), date(2025, 12, 31)),
    pd_.Doc("annual-2025", "annual", date(2025, 1, 1), date(2025, 12, 31)),
)


def ms(text):
    r = pd_.matching_sources(pd_.parse(text), DOCS)
    return None if r is None else set(r)


def test_matching_conjunction_and_fallbacks():
    assert ms("the advance release for 1Q 2026") == {"adv-q1"}
    assert ms("1Q 2026 final report") == {"fin-q1"}
    assert ms("1Q 2026") == {"adv-q1", "fin-q1"}
    assert ms("4Q 2025") == {"fin-q4", "annual-2025"}  # an annual document covers the whole year
    assert ms("advance") == {"adv-q1"}  # stage only
    assert ms("how did unemployment change") is None  # no hint, no filter
    assert ms("3Q 2023") is None  # hinted period with no document: no filter
    assert ms("the advance release for 4Q 2025") is None  # no document satisfies both hints: no filter


def test_conflicting_stage_hints_restrict_period_only():
    assert ms("advance versus final figures for 1Q 2026") == {"adv-q1", "fin-q1"}


def test_conflicting_period_and_stage_in_one_question():
    assert ms("1Q 2026 and 4Q 2025 final") == {"fin-q1", "fin-q4"}


def test_catalogue_matches_real_sources():
    ids = {d.source_id for d in pd_.catalogue()}
    assert {"mom-2026-q1-advance", "mom-2026-q1-final", "mom-2025-q4-final-release"} <= ids
    h = pd_.parse("What did the advance release for 1Q 2026 report?")
    assert pd_.matching_sources(h) == {"mom-2026-q1-advance"}
    h = pd_.parse("final 4Q 2025")
    assert pd_.matching_sources(h) == {"mom-2025-q4-final", "mom-2025-q4-final-release"}  # annual documents are not stage final


def test_catalogue_includes_expansion_batch_documents():
    ids = {d.source_id for d in pd_.catalogue()}
    assert {"mom-2025-q1-final", "mom-2024-q3-advance"} <= ids  # defined in specs/sources.d, not specs/sources.yaml
    assert pd_.matching_sources(pd_.parse("advance release 3Q 2024")) == {"mom-2024-q3-advance"}
