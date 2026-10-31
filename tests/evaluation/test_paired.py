import hashlib
import json

import pytest

from labourlens.evaluation import paired as p


def gold(n, shared=()):
    """n cases; each has its own evidence id, except cases listed in `shared` which all cite one id."""
    out = []
    for i in range(n):
        ids = ["shared-obs"] if i in shared else [f"obs-{i}"]
        out.append({"case_id": f"HO-V2-{i:03d}", "family": "factual_lookup", "source_group": f"g{i % 4}",
                    "evidence_text": [], "evidence_data": [{"observation_ids": ids}]})
    return out


def rows(cases, ok_fn, false_fn=lambda i: False, contra_fn=lambda i: False):
    return {c["case_id"]: {"case_id": c["case_id"], "behavior_ok": ok_fn(i), "false_answer": false_fn(i), "facts_contradicted": int(contra_fn(i))}
            for i, c in enumerate(sorted(cases, key=lambda c: c["case_id"]))}


def test_components_merge_shared_evidence_and_keep_empty_cases_apart():
    cases = gold(5, shared={0, 1, 2})
    cases.append({"case_id": "HO-V2-900", "family": "adversarial", "evidence_text": [], "evidence_data": []})
    cases.append({"case_id": "HO-V2-901", "family": "adversarial", "evidence_text": [], "evidence_data": []})
    comp = p.components(cases)
    assert comp["HO-V2-000"] == comp["HO-V2-001"] == comp["HO-V2-002"]
    assert comp["HO-V2-003"] != comp["HO-V2-004"] != comp["HO-V2-900"]
    assert comp["HO-V2-900"] != comp["HO-V2-901"]
    assert len(set(comp.values())) == 5


def test_components_follow_passage_ids_too():
    cases = [{"case_id": "A", "evidence_text": [{"passage_ids": ["p1", "p2"]}], "evidence_data": []},
             {"case_id": "B", "evidence_text": [{"passage_ids": ["p2"]}], "evidence_data": []},
             {"case_id": "C", "evidence_text": [{"passage_ids": ["p3"]}], "evidence_data": []}]
    comp = p.components(cases)
    assert comp["A"] == comp["B"] != comp["C"]


@pytest.mark.parametrize("better,worse,expected", [(0, 0, 1.0), (5, 0, 0.0625), (3, 3, 1.0), (1, 6, 0.125)])
def test_mcnemar_exact(better, worse, expected):
    assert p.mcnemar_exact(better, worse) == pytest.approx(expected)


def test_clear_gain_is_demonstrated():
    cases = gold(60)
    cand = rows(cases, lambda i: True)
    base = rows(cases, lambda i: i % 2 == 0)  # candidate better on 30 of 60
    r = p.compare(cand, base, cases, n_boot=2000)
    assert r["better"] == 30 and r["worse"] == 0 and r["paired_difference"] == 0.5
    assert r["case_bootstrap_interval"][0] > 0 and r["component_bootstrap_interval"][0] > 0
    assert r["n_evidence_components"] == 60
    assert r["demonstrated_gain"] is True
    assert p.decide({"gpt-6-luna": r, "m2": r})["demonstrated_gain_primary"] is True


def test_no_difference_is_not_a_gain():
    cases = gold(60)
    same = rows(cases, lambda i: i % 3 != 0)
    r = p.compare(same, dict(same), cases, n_boot=2000)
    assert r["paired_difference"] == 0 and r["mcnemar_exact_p"] == 1.0
    assert r["demonstrated_gain"] is False


def test_small_gain_interval_includes_zero():
    cases = gold(60)
    cand = rows(cases, lambda i: i < 5 or i % 2 == 0)
    base = rows(cases, lambda i: i % 2 == 0)
    r = p.compare(cand, base, cases, n_boot=2000)
    assert r["better"] == 2 and r["worse"] == 0
    assert r["case_bootstrap_interval"][0] <= 0
    assert r["demonstrated_gain"] is False


def test_component_bootstrap_is_wider_when_cases_share_evidence():
    cases = gold(60, shared=set(range(30)))  # 30 cases form one component
    cand = rows(cases, lambda i: True)
    base = rows(cases, lambda i: i >= 30 or i % 3 == 0)  # all wins sit inside the shared component
    r = p.compare(cand, base, cases, n_boot=4000)
    lo_case, _ = r["case_bootstrap_interval"]
    lo_comp, _ = r["component_bootstrap_interval"]
    assert lo_case > 0
    assert lo_comp <= lo_case
    assert r["n_evidence_components"] == 31


def test_too_few_components_blocks_gain():
    cases = gold(60, shared=set(range(55)))
    cand = rows(cases, lambda i: True)
    base = rows(cases, lambda i: i % 2 == 0)
    r = p.compare(cand, base, cases, n_boot=2000, min_components=20)
    assert r["n_evidence_components"] == 6
    assert r["conditions"]["enough_evidence_components"] is False
    assert r["demonstrated_gain"] is False


def test_added_false_answer_blocks_gain():
    cases = gold(60)
    cand = rows(cases, lambda i: True, false_fn=lambda i: i == 0)
    base = rows(cases, lambda i: i % 2 == 0)
    r = p.compare(cand, base, cases, n_boot=2000)
    assert r["conditions"]["no_added_false_answers"] is False
    assert r["demonstrated_gain"] is False


def test_contradicted_answer_is_reported_but_does_not_veto():
    cases = gold(60)
    cand = rows(cases, lambda i: True, contra_fn=lambda i: i == 0)
    base = rows(cases, lambda i: i % 2 == 0)
    r = p.compare(cand, base, cases, n_boot=2000)
    assert "no_added_contradicted_answers" not in r["conditions"]
    assert r["guardrails"]["answers_with_contradicted_fact"] == {"candidate": 1, "baseline": 0}
    assert r["demonstrated_gain"] is True


def test_one_sided_95_bound_is_the_lower_end_of_the_two_sided_90_interval():
    assert p.LEVEL == 0.90


def test_missing_or_extra_case_is_incomplete():
    cases = gold(10)
    cand = rows(cases, lambda i: True)
    base = rows(cases, lambda i: False)
    base.pop("HO-V2-003")
    r = p.compare(cand, base, cases, n_boot=500)
    assert r["complete"] is False and r["demonstrated_gain"] is False and r["missing"]["baseline"] == ["HO-V2-003"]
    base = rows(cases, lambda i: False)
    base["HO-V2-777"] = {"behavior_ok": True}
    assert p.compare(cand, base, cases, n_boot=500)["unexpected"]["baseline"] == ["HO-V2-777"]


def test_bootstrap_is_deterministic_for_fixed_seed():
    cases = gold(40)
    cand = rows(cases, lambda i: i % 5 != 0)
    base = rows(cases, lambda i: i % 2 == 0)
    a = p.compare(cand, base, cases, n_boot=1000)
    b = p.compare(cand, base, cases, n_boot=1000)
    assert a["case_bootstrap_interval"] == b["case_bootstrap_interval"] and a["component_bootstrap_interval"] == b["component_bootstrap_interval"]
    assert a["seed"] == 20261031


def test_primary_model_decides_and_replication_is_reported_only():
    good = {"demonstrated_gain": True}
    bad = {"demonstrated_gain": False}
    d = p.decide({"gpt-6-luna": good, "gpt-5.6-luna": bad})
    assert d["demonstrated_gain_primary"] is True and d["replication_models"] == {"gpt-5.6-luna": False}
    assert p.decide({"gpt-6-luna": bad, "gpt-5.6-luna": good})["demonstrated_gain_primary"] is False
    assert p.decide({"gpt-5.6-luna": good})["demonstrated_gain_primary"] is False
    assert p.decide({})["demonstrated_gain_primary"] is False


def test_run_reads_scored_case_files_and_writes_result(tmp_path, monkeypatch):
    cases = gold(30)
    gold_path = tmp_path / "gold.jsonl"
    gold_path.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    monkeypatch.setattr(p.paths, "EXPERIMENTS", tmp_path / "experiments")
    for exp, ok in (("cand", lambda i: True), ("base", lambda i: i % 2 == 0)):
        d = tmp_path / "experiments" / "eval" / exp
        d.mkdir(parents=True)
        (d / "m.cases.jsonl").write_text("\n".join(json.dumps(r) for r in rows(cases, ok).values()) + "\n")
        (d / "m.metrics.json").write_text(json.dumps({"provenance": {"gold_sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest()}}))
    out = tmp_path / "paired.json"
    result = p.run(gold_path, "cand", "base", ["m"], out, n_boot=500, seed=1)
    assert json.loads(out.read_text())["per_model"]["m"]["paired_difference"] == result["per_model"]["m"]["paired_difference"] == 0.5
    assert result["per_model"]["m"]["n_source_groups"] == 4


def test_sensitivity_exclusions_are_descriptive_and_do_not_change_the_verdict():
    cases = gold(60)
    cand = rows(cases, lambda i: True)
    base = rows(cases, lambda i: i % 2 == 0)
    drop = {c["case_id"] for c in cases[:20]}
    r = p.compare(cand, base, cases, n_boot=1000, exclusions={"without_first_20": drop, "tiny": {c["case_id"] for c in cases[:59]}})
    s = r["sensitivity_descriptive"]
    assert s["without_first_20"]["n"] == 40 and s["without_first_20"]["better"] == 20
    assert s["tiny"] == {"n": 1}
    assert r["demonstrated_gain"] is True
