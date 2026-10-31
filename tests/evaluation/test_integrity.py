import hashlib

import pytest

from labourlens.agent.experiments import _calc_correct
from labourlens.evaluation import harness as h
from labourlens.evaluation.provenance import snapshot


@pytest.fixture
def pair():
    return ({"case_id": "test", "question": "How changed?", "expected_behavior": "answer", "reference_facts": ["fell"]},
            {"answer": {"status": "answered", "summary": "A change", "claims": [{"text": "It fell", "citations": [{"label": "P1"}]}]}, "evidence_text": {"P1": "evidence"}})


@pytest.mark.parametrize("field", ["question", "reference_facts", "expected_behavior", "summary", "claim", "evidence", "model", "prompt"])
def test_cache_inputs_invalidate(pair, monkeypatch, tmp_path, field):
    case, rec = pair
    original = h.judgement_hash(case, rec)
    if field in case:
        case[field] = ["changed"] if field == "reference_facts" else "changed"
    elif field == "summary":
        rec["answer"]["summary"] = "changed"
    elif field == "claim":
        rec["answer"]["claims"][0]["text"] = "changed"
    elif field == "evidence":
        rec["evidence_text"]["P1"] = "changed"
    elif field == "model":
        monkeypatch.setattr(h, "JUDGE_MODEL", "changed")
    else:
        monkeypatch.setattr(h, "file_hash", lambda p: "changed")
    assert h.judgement_hash(case, rec) != original


@pytest.mark.parametrize("source", ["owner_manual", "agreed_with_ai_suggestion"])
def test_review_metadata_does_not_change_judge_inputs(pair, source):
    case, rec = pair
    original = h.judgement_hash(case, rec)
    case.update(
        review_status="owner_reviewed", reviewed_by="Mihir",
        owner_review={"reviewer": "Mihir", "decision_source": source, "date": "2026-10-31"},
    )
    assert h.judgement_hash(case, rec) == original


def test_evaluation_report_records_owner_assisted_count(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(h.ev, "load_cases", lambda split, path=None: [
        {"case_id": "DEV-001", "review_status": "owner_reviewed"},
        {"case_id": "DEV-002", "review_status": "draft"},
    ])
    monkeypatch.setattr(h.paths, "DATA", tmp_path / "data")
    monkeypatch.setattr(h.paths, "EXPERIMENTS", tmp_path / "experiments")
    h.run("empty", judge=False)
    report = capsys.readouterr().out
    assert "1/2 cases record per-card owner review" in report
    assert "not independent inter-rater evidence" in report
    assert "nothing here is human-reviewed" not in report

def test_stale_cache_rejudged_and_strict_mode_fails(pair, monkeypatch):
    case, rec = pair
    cache = {"test": {"claims": [], "facts": []}}
    with pytest.raises(ValueError, match="Stale judgment"):
        h.cached_judgement(case, rec, cache, judge=False, rejudge_stale=False)
    assert h.cached_judgement(case, rec, cache, judge=False) is None
    result = {"claims": [], "facts": [], "cost_usd": 0}
    monkeypatch.setattr(h, "judge_one", lambda c, r: result)
    assert h.cached_judgement(case, rec, cache, judge=True) == result
    monkeypatch.setattr(h, "judge_one", lambda *args: pytest.fail("valid cache must be reused"))
    assert h.cached_judgement(case, rec, cache, judge=True) == result
    rec["answer"]["summary"] = "new answer"
    with pytest.raises(ValueError, match="Stale judgment"):
        h.cached_judgement(case, rec, cache, judge=True, rejudge_stale=False)


def test_false_answer_claim_support_but_no_fact_coverage(pair, monkeypatch):
    case, rec = pair
    case.update(reference_facts=[], expected_behavior="abstain", family="ambiguity")
    assert h.judge_eligible(rec)
    monkeypatch.setattr(h.agx, "score_run", lambda *args: dict(behavior_ok=False, expected="abstained", status="answered", valid=True,
        operational_failure=False, n_ungrounded_numbers=0, seconds=1, cost_usd=0, tool_errors=0))
    row = h.case_metrics(case, rec, {"claims": [{"verdict": "unsupported", "note": "wrong"}],
        "facts": [{"status": "covered", "note": "stale"}], "cost_usd": 0})
    assert row["claims_unsupported"] == 1
    assert row["facts_total"] == row["facts_covered"] == 0
    agg = h.aggregate([row])
    assert agg["fact_coverage"]["n"] == 0
    assert agg["answers_contradicting_a_reference_fact"]["n"] == 0
    assert agg["cases_with_ungrounded_numbers"] == agg["answers_with_ungrounded_numbers"]


@pytest.fixture
def calculation():
    case = {"calculation": {"inputs": ["b", "a"], "formula": "difference", "expected_value": -0.3, "unit": "percentage points"},
            "evidence_data": [{"period": "2025-Q1", "observation_ids": ["a"]}, {"period": "2025-Q2", "observation_ids": ["b"]}]}
    cid = "calc:" + hashlib.sha256(b"a|b|difference").hexdigest()[:12]
    rec = {"answer": {"summary": "", "claims": [{"text": "It decreased by 0.3 percentage points", "citations": [{"label": "C1"}]}]},
           "evidence": [{"label": "C1", "id": cid}, {"label": "D1", "id": "a"}, {"label": "D2", "id": "b"}],
           "evidence_text": {"D1": "series | 2% | release stage: final", "D2": "series | 1.7% | release stage: final",
                             "C1": "Calculated difference of rate from 2025-Q1 to 2025-Q2: 1.7 - 2 = -0.3 percentage points. Inputs D1 (2025-Q1) and D2 (2025-Q2)."}}
    return case, rec


@pytest.mark.parametrize("text,correct", [("It decreased by 0.3 percentage points", True),
    ("Change: -0.3 percentage points", True), ("It increased by 0.3 percentage points", False),
    ("Magnitude was 0.3 percentage points", False), ("The 0.3 percentage points threshold is incidental", False),
    ("The threshold is -0.3 percentage points", False)])
def test_calculation_requires_direction(calculation, text, correct):
    case, rec = calculation
    rec["answer"]["claims"][0]["text"] = text
    assert _calc_correct(case, rec) is correct


@pytest.mark.parametrize("old,new", [("1.7 - 2", "2 - 1.7"), ("= -0.3", "= 0.3"),
    ("percentage points", "percent"), ("from 2025-Q1 to 2025-Q2", "from 2025-Q2 to 2025-Q1"),
    ("Inputs D1", "Inputs D2"), ("Calculated difference", "Calculated percent change")])
def test_calculation_record_integrity(calculation, old, new):
    case, rec = calculation
    rec["evidence_text"]["C1"] = rec["evidence_text"]["C1"].replace(old, new)
    assert not _calc_correct(case, rec)


def test_incidental_number_without_calculation_fails(calculation):
    case, rec = calculation
    rec["evidence"] = []
    assert not _calc_correct(case, rec)


def test_provenance_fingerprints():
    p = snapshot("planner=model|answer=model|planner_v2|answer_v3|retrieval=r3", 235, 237)
    assert p["eligible_n"] == 235 and p["available_n"] == 237
    assert all(p["prompt_sha256"].values())
    assert len(p["gold_sha256"]) == len(p["price_table_sha256"]) == 64
    assert p["git_head"]


def test_snapshot_uses_separate_gold(tmp_path):
    gold = tmp_path / "heldout_v2.jsonl"
    gold.write_text('{"case_id":"HO-V2-001"}\n')
    result = snapshot("planner_v1|answer_v3", 1, 1, gold_path=gold)
    assert result["gold_sha256"] == hashlib.sha256(gold.read_bytes()).hexdigest()


@pytest.mark.parametrize("command", ["agent-exp", "eval"])
def test_cli_routes_separate_gold(command, tmp_path, monkeypatch):
    from labourlens import cli
    from labourlens.agent import experiments

    gold = tmp_path / "heldout_v2.jsonl"
    received = {}
    target = experiments if command == "agent-exp" else h
    monkeypatch.setattr(target, "run", lambda *args, **kwargs: received.update(kwargs))
    assert cli.main([command, "--gold", str(gold), "--split", "heldout"]) == 0
    assert received["gold_path"] == gold


@pytest.mark.parametrize("unit,first,second", [("hours_per_week", "43.3", "43.0"), ("index_2015_100", "93.9", "90.3")])
def test_calculation_scorer_accepts_non_legacy_units(unit, first, second):
    from labourlens.agent.tools import compute_change

    result, shown, label, formula = compute_change(first, second, "difference", unit)
    cid = "calc:" + hashlib.sha256(b"a|b|difference").hexdigest()[:12]
    case = {"calculation": {"inputs": ["a", "b"], "formula": "difference", "expected_value": float(result), "unit": unit},
            "evidence_data": [{"period": "2025-Q1", "observation_ids": ["a"]}, {"period": "2026-Q2", "observation_ids": ["b"]}]}
    rec = {"answer": {"summary": "", "claims": [{"text": f"It fell by {abs(result)} in the period", "citations": [{"label": "C1"}]}]},
           "evidence": [{"label": "C1", "id": cid}, {"label": "D1", "id": "a"}, {"label": "D2", "id": "b"}],
           "evidence_text": {"D1": f"series | {first} {unit} | release stage: dataset_snapshot", "D2": f"series | {second} {unit} | release stage: dataset_snapshot",
                             "C1": f"Calculated difference of x (all; employees, unspecified) from 2025-Q1 to 2026-Q2: {formula} = {shown} {label}. Inputs D1 (2025-Q1) and D2 (2026-Q2)."}}
    assert _calc_correct(case, rec) is True
    rec["evidence_text"]["D2"] = f"series | {second} wrong_unit | release stage: dataset_snapshot"
    assert _calc_correct(case, rec) is False
