"""Offline argument-boundary regressions for report search, with no retrieval calls."""

from types import SimpleNamespace

import pytest

from labourlens.agent import tools as tl


@pytest.mark.parametrize("query,needle", [
    (None, "query must be a string"),
    (42, "query must be a string"),
    (True, "query must be a string"),
    (["unemployment"], "query must be a string"),
    ({"topic": "unemployment"}, "query must be a string"),
    ("", "empty or whitespace-only"),
    (" \n\t ", "empty or whitespace-only"),
    ("x" * (tl.MAX_QUERY_CHARS + 1), "maximum is"),
])
def test_search_reports_rejects_invalid_query_before_retrieval(monkeypatch, query, needle):
    tools = tl.Tools(SimpleNamespace())

    def unexpected(*args):
        pytest.fail("invalid arguments must not reach retrieval")

    monkeypatch.setattr(tools, "_search", unexpected)
    result = tools.search_reports(query)
    assert not result.ok and result.error_kind == "invalid_arguments"
    assert needle in result.message
    assert not tools.items


@pytest.mark.parametrize("k,needle", [
    (True, "not a boolean"),
    (False, "not a boolean"),
    ("8", "not a boolean, string"),
    (8.0, "other type"),
    (None, "other type"),
    (0, "k=0 is outside"),
    (-1, "k=-1 is outside"),
    (tl.MAX_K + 1, "outside the allowed range"),
    (86030615, "k=86030615 is outside"),
])
def test_search_reports_rejects_invalid_k_with_actionable_correction(monkeypatch, k, needle):
    tools = tl.Tools(SimpleNamespace())

    def unexpected(*args):
        pytest.fail("invalid arguments must not reach retrieval")

    monkeypatch.setattr(tools, "_search", unexpected)
    result = tools.search_reports("2021-Q3 retrenchment reasons", k=k)
    assert not result.ok and result.error_kind == "invalid_arguments"
    assert needle in result.message and "use k=8" in result.message.lower()
    assert not tools.items


@pytest.mark.parametrize("k", [1, 8, tl.MAX_K])
def test_search_reports_trims_query_and_preserves_valid_k(monkeypatch, k):
    tools = tl.Tools(SimpleNamespace())
    calls = []

    def search(query, depth):
        calls.append((query, depth))
        return [], {}, {}, {}, {}

    monkeypatch.setattr(tools, "_search", search)
    result = tools.search_reports("  " + "x" * tl.MAX_QUERY_CHARS + " \n", k=k)
    assert result.ok and calls == [("x" * tl.MAX_QUERY_CHARS, k)]


def test_search_reports_keeps_default_depth(monkeypatch):
    tools = tl.Tools(SimpleNamespace())
    calls = []

    def search(query, depth):
        calls.append((query, depth))
        return [], {}, {}, {}, {}

    monkeypatch.setattr(tools, "_search", search)
    assert tools.search_reports("2021-Q3 retrenchment reasons").ok
    assert calls == [("2021-Q3 retrenchment reasons", 8)]
