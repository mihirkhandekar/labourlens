"""D-093: entity-tolerant quotes and served-only recovery from unverifiable quotes. Stubbed; no model calls."""
import json


from .test_parallel_tools import _cfg, _shared, tc

from labourlens.agent import graph
from labourlens.agent import tools as tl
from labourlens.answer import llm
from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer
from labourlens.answer.validate import check, quote_in, recover_quote_errors, rights_tokens

TEXT = "Sector A rose, Information & Communications rose too, and Financial Services also rose"


def passage(label="P1", text=TEXT, flags=()):
    return ContextPassage(label, f"id-{label}", "mom", "t", None, "final", "p1", text, tuple(flags))


def answer(claims, summary="Retrenchments rose.", caveats=()):
    return Answer(status="answered", summary=summary, reason="", claims=claims, caveats=list(caveats), clarification_question="")


def claim(text, *quotes):
    return {"text": text, "citations": [{"label": lab, "quote": q} for lab, q in quotes]}


def test_entity_form_quote_is_verbatim_both_directions():
    assert quote_in("Information &amp; Communications", TEXT)
    assert quote_in("Information & Communications", TEXT.replace("&", "&amp;"))
    assert not quote_in("Information and Communications", TEXT)


def test_rights_tokens_decode_entities_and_keep_offsets_whole():
    tokens = rights_tokens("Information &amp; Communications")
    assert [t[0] for t in tokens] == ["information", "communications"]
    assert tokens[1][1] == len("Information &amp; ")


def test_recovery_drops_bad_citation_keeps_claim_and_adds_caveat():
    ctx = [passage()]
    a = answer([claim("Sectors named.", ("P1", "Financial Services"), ("P1", "invented words here"))])
    rep = check(a, ctx)
    out = recover_quote_errors(a, ctx, rep.errors)
    assert [c.quote for c in out.claims[0].citations] == ["Financial Services"]
    assert "Some supporting quotes could not be verified and were removed." in out.caveats


def test_recovery_drops_claim_without_valid_citation_or_stays_invalid():
    ctx = [passage()]
    a = answer([claim("Good.", ("P1", "Financial Services")), claim("Bad.", ("P1", "nonsense quote"))])
    out = recover_quote_errors(a, ctx, check(a, ctx).errors)
    assert [c.text for c in out.claims] == ["Good."]
    only_bad = answer([claim("Bad.", ("P1", "nonsense quote"))])
    assert recover_quote_errors(only_bad, ctx, check(only_bad, ctx).errors) is None


def test_recovery_never_loosens_other_errors():
    ctx = [passage(), passage("P2", flags=("injection",))]
    flagged = answer([claim("x", ("P2", "Financial Services"), ("P1", "nonsense"))])
    assert recover_quote_errors(flagged, ctx, check(flagged, ctx).errors) is None
    bad_label = answer([claim("x", ("P9", "Financial Services"), ("P1", "nonsense"))])
    assert recover_quote_errors(bad_label, ctx, check(bad_label, ctx).errors) is None
    ungrounded = answer([claim("Rose by 999.", ("P1", "Financial Services"), ("P1", "nonsense"))])
    assert recover_quote_errors(ungrounded, ctx, check(ungrounded, ctx).errors) is None
    abstain = Answer(status="abstained", summary="", reason="r", claims=[], caveats=[], clarification_question="")
    assert recover_quote_errors(abstain, ctx, ["claim 1 quote is not verbatim in P1"]) is None


# Graph level: a stubbed planner and answerer, two bad drafts.
def run(monkeypatch, annual):
    bad = {"status": "answered", "summary": "Retrenchments rose in some sectors.", "reason": "", "caveats": [], "clarification_question": "",
           "claims": [claim("Financial Services was named.", ("P1", "Financial Services"), ("P1", "invented words here"))]}
    plans = [[tc("search_reports", {"query": "layoffs"}, "a")], []]

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer", **kw):
        if "tools" in kw:
            return llm.LLMResult("", 10, 5, 0, 0.01, tool_calls=plans.pop(0))
        return llm.LLMResult(json.dumps(bad), 10, 5, 0, 0.01)

    def search_reports(self, query, k=8):
        it = self._add("P", "pid-1", "mom-2026-q2-final", "Report", None, "final", "p1", TEXT)
        return tl.ToolResult(True, [it], f"1 new passages: {it.label}")

    monkeypatch.setattr(llm, "chat", chat)
    monkeypatch.setattr(tl.Tools, "search_reports", search_reports)
    return graph.run_agent("why were the layoffs highest in 2026 Q2?", _shared(), _cfg(annual=annual), save_trace=False)


def test_served_mode_recovers_after_failed_repair(monkeypatch):
    result = run(monkeypatch, annual=True)
    assert result["outcome"] == "answered" and not result["errors"]
    citations = [c["quote"] for cl in result["answer"]["claims"] for c in cl["citations"]]
    assert citations == ["Financial Services"]
    assert "Some supporting quotes could not be verified and were removed." in result["answer"]["caveats"]
    assert any(e["node"] == "validate_answer" and "quote_recovery" in e["detail"] for e in result["trace"])


def test_evaluated_mode_is_unchanged(monkeypatch):
    result = run(monkeypatch, annual=False)
    assert result["outcome"] == "invalid"
    assert any("not verbatim" in e for e in result["errors"])


def test_invalid_outcome_message_is_accurate_and_unleaky():
    from labourlens.report.app import public_result

    out = public_result({"outcome": "invalid", "answer": None, "errors": ["claim 2 quote is not verbatim in P3"]}, None)["answer"]
    assert "citation checks" in out["reason"] and "P3" not in json.dumps(out) and "unavailable" not in out["reason"]
    down = public_result({"outcome": "operational_failure", "answer": None}, None)["answer"]
    assert down["reason"] == "Evidence or service unavailable."
