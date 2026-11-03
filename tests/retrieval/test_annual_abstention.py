"""Incomplete annual rates must name the missing quarters, without a further model call (D-092)."""
from .test_parallel_tools import _cfg, _shared, script, tc

from labourlens.agent import graph
from labourlens.agent.tools import ToolResult, Tools
from labourlens.answer.schema import Answer
from labourlens.answer.validate import annual_missing_quarter_abstention


ARGS = dict(year=2026, source_id="resident_unemployment_rate", indicator_id="unemployment_rate", population="resident",
            adjustment="seasonally_adjusted", dimension=None)
MESSAGE = "annual_average requires four in-scope published quarters; missing quarters: 2026-Q3, 2026-Q4"


def abstention(status="abstained"):
    return Answer(status=status, summary="", reason="I cannot determine this from the supplied evidence.", claims=[], caveats=[], clarification_question="")


def event(kind="error", error_kind="not_found", message=MESSAGE):
    return {"node": "execute_tool", "event": kind, "detail": {"tool": "annual_average", "args": ARGS, "error_kind": error_kind, "message": message}}


def test_generic_model_abstention_names_quarters_from_stubbed_tool(monkeypatch):
    monkeypatch.setattr(Tools, "annual_average", lambda self, **kw: ToolResult(False, message=MESSAGE, error_kind="not_found"))
    script(monkeypatch, [[tc("annual_average", ARGS, "annual")], []])
    result = graph.run_agent("What is the annual-average resident unemployment rate for 2026?", _shared(), _cfg(), save_trace=False)
    reason = result["answer"]["reason"]
    assert result["outcome"] == "abstained" and "2026-Q3" in reason and "2026-Q4" in reason
    assert "until those quarterly rates are published" in reason and "partial-year average is not used" in reason
    assert len([e for e in result["trace"] if e["node"] == "generate_answer" and e["event"] == "generated"]) == 1
    assert result["tool_calls"] == 1


def test_only_missing_quarter_annual_not_found_is_rewritten():
    original = abstention()
    for trace in ([], [event(error_kind="invalid_arguments")], [event(message="no rows match these series filters")],
                  [{"node": "execute_tool", "event": "error", "detail": {"tool": "get_series", "error_kind": "not_found", "message": MESSAGE}}]):
        assert annual_missing_quarter_abstention(original, trace) is original
    for status in ("answered", "clarify", "refused"):
        other = abstention(status)
        assert annual_missing_quarter_abstention(other, [event()]) is other


def test_successful_retry_supersedes_missing_quarters_and_multiple_errors_deduplicate():
    original = abstention()
    assert annual_missing_quarter_abstention(original, [event(), event("ok")]) is original
    result = annual_missing_quarter_abstention(original, [event(), event()])
    assert result.reason.count("2026-Q3") == result.reason.count("2026-Q4") == 1
