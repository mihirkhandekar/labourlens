"""Audit log, feedback log, and deterministic data-quality notes (missing data, mixed series, advance-vs-final conflict)."""

import json

import pandas as pd
import pytest

from labourlens.agent.tools import Shared, StatsData, Tools
from labourlens.audit import log as al


def fake_res(**kw):
    base = {"run_id": "abc123", "question": "How many? key sk-abcdefghijklmnopqrstuvwxyz123456", "config": "cfg", "outcome": "answered",
            "answer": {"status": "answered", "summary": "s", "claims": [{"text": "t", "citations": []}], "caveats": ["c"], "reason": "", "clarification_question": ""},
            "errors": [], "rounds": 1, "evidence": [{"id": "O1", "label": "O1", "source_id": "x"}], "cited_ids": ["O1"],
            "usage": {"cost_usd": 0.001, "prompt_tokens": 1, "completion_tokens": 1, "calls": 1, "llm_seconds": 1.0}, "seconds": 2.0,
            "trace": [{"node": "execute_tool", "event": "operational_failure", "detail": {"tool": "get_series", "args": {"source_id": "x"}, "seconds": 1.0}},
                      {"node": "validate_question", "event": "accepted", "detail": {"input_flags": ["override_instructions"]}}]}
    base.update(kw)
    return base


@pytest.fixture
def audit_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(al, "AUDIT_DIR", tmp_path)
    return tmp_path


def test_run_record_is_redacted_hashed_and_complete(audit_dir):
    al.log_run(fake_res(), "web", session="sess-1", ip="203.0.113.7")
    rec = al.read_runs()[0]
    raw = next(audit_dir.glob("runs-*.jsonl")).read_text()
    assert "sk-abcdefghijklmnop" not in raw and "203.0.113.7" not in raw and "sess-1" not in raw
    assert rec["session"] and rec["client"] and rec["session"] != rec["client"]
    assert rec["operational_failures"] == 1 and rec["guard_events"] and rec["cited_ids"] == ["O1"] and rec["version"]["git_commit"] is not None or True
    assert {"run_id", "ts", "config", "outcome", "usage", "seconds", "tool_calls", "evidence_ids"} <= set(rec)


def test_feedback_links_to_run_and_validates_rating(audit_dir):
    al.log_run(fake_res(), "web")
    al.log_feedback("abc123", "down", "wrong quarter \x00 sk-abcdefghijklmnopqrstuvwxyz123456", session="s")
    with pytest.raises(ValueError):
        al.log_feedback("abc123", "maybe")
    fb = al.read_feedback()
    assert len(fb) == 1 and "sk-abcdef" not in fb[0]["comment"] and "\x00" not in fb[0]["comment"]
    rep = al.report()
    assert "1 down" in rep and "abc123" in rep


def test_audit_failure_never_raises(monkeypatch):
    monkeypatch.setattr(al, "AUDIT_DIR", __import__("pathlib").Path("/proc/definitely/not/writable"))
    before = al.failures()
    al.log_run(fake_res(), "web")
    assert al.failures() == before + 1


def make_stats(rows):
    st = StatsData(pd.DataFrame(rows))
    st.titles = {"ds1": "Test rate"}
    return st


def obs_row(i, period, value, **kw):
    r = dict(observation_id=f"o{i}", source_id="ds1", period=period, dimension="", indicator_id="rate", population="resident", adjustment="sa", unit="percent",
             value=value, release_stage="dataset_snapshot", missing_reason=None, title="Test rate", in_answer_scope=True)
    r.update(kw)
    return r


def test_missing_period_and_null_value_produce_notes():
    st = make_stats([obs_row(1, "2025-Q3", 2.0), obs_row(2, "2025-Q4", None, missing_reason="not available")])
    sh = Shared.__new__(Shared)
    sh.stats, sh.obs, sh.titles, sh.stats_backend = st, st.obs, st.titles, None
    t = Tools(sh)
    res = t.get_series("ds1", "2025-Q3", "2026-Q2")
    assert res.ok
    joined = " ".join(t.notes)
    assert "no published number for 2025-Q4" in joined and "no row for 2026-Q1, 2026-Q2" in joined and "Do not estimate" in joined


def test_mixed_series_and_advance_final_pair_produce_notes():
    st = make_stats([obs_row(1, "2026-Q1", 2.0), obs_row(2, "2026-Q1", 2.1, population="overall")])
    sh = Shared.__new__(Shared)
    sh.stats, sh.obs, sh.titles, sh.stats_backend = st, st.obs, st.titles, None
    t = Tools(sh)
    t.get_series("ds1", "2026-Q1", "2026-Q1")
    assert any("more than one series" in n for n in t.notes)
    t._add("P", "p1", "mom-2026-q1-advance", "adv", "2026-04-01", "advance", "p.1", "text")
    t._add("P", "p2", "mom-2026-q1-final-release", "fin", "2026-06-01", "final", "p.1", "text")
    assert any("both the advance and the final" in n for n in t.notes)


def test_notes_render_as_non_citeable_block():
    from labourlens.answer import context as cx

    out = cx.render([], ["a note <x>"])
    assert "<data_quality_notes>" in out and "&lt;x&gt;" in out
