import hashlib
import json

import pytest

from labourlens.agent import experiments as agx
from labourlens.evaluation import harness as h
from labourlens.evaluation import paired
from labourlens import paths

ARCHIVE = paths.EXPERIMENTS / "gold" / "archive"
ARCHIVED = {"gold-v3.2.jsonl": "647b26a2f0faa86be30ad897840bc1887b54f55c27268d141565b94cb22998e8",
            "gold-v3.3.jsonl": "96ec51baf05d9fb998efd3ed37762cb8cedd27b2bf329996d7251adcb01b597e",
            "gold-v3.4.jsonl": "050bb40b4863cf3a00682da0edc305dc4d9c7de1c35b3098989e8afdd50899b9",
            "gold-v3.5.jsonl": "aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09"}


@pytest.mark.parametrize("name,digest", ARCHIVED.items())
def test_archived_gold_hashes(name, digest):
    assert hashlib.sha256((ARCHIVE / name).read_bytes()).hexdigest() == digest


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    for mod in (h.paths, agx.paths):
        monkeypatch.setattr(mod, "DATA", tmp_path / "data")
        monkeypatch.setattr(mod, "EXPERIMENTS", tmp_path / "experiments")
    return tmp_path


def test_agent_exp_refuses_existing_run_without_force(sandbox, monkeypatch):
    raw = sandbox / "data" / "runs" / "agent-dev-A3"
    raw.mkdir(parents=True)
    (raw / f"{next(iter(agx.MODEL_PAIRS))}.jsonl").write_text("{}\n")
    monkeypatch.setattr(agx.ev, "load_cases", lambda split, path=None: [])
    with pytest.raises(FileExistsError, match="--force"):
        agx.run("dev", tag="A3")
    assert not (sandbox / "experiments").exists()
    # a new tag is fine (no cases, so nothing is generated)
    assert agx.existing_outputs("agent-dev-A9", list(agx.MODEL_PAIRS)) == []


def test_agent_exp_force_flag_accepted(sandbox, monkeypatch):
    (sandbox / "experiments" / "runs").mkdir(parents=True)
    (sandbox / "experiments" / "runs" / "agent-dev-A3-SUMMARY.md").write_text("old")
    monkeypatch.setattr(agx.ev, "load_cases", lambda split, path=None: [])
    monkeypatch.setattr(agx, "Shared", lambda: None)
    monkeypatch.setattr(agx, "MODEL_PAIRS", {})
    agx.run("dev", tag="A3", force=True)


def make_run(sandbox, gold_hash_in_metrics, gen_hash=None):
    raw = sandbox / "data" / "runs" / "agent-dev-T"
    raw.mkdir(parents=True)
    rec = {"case_id": "DEV-001", "question": "q", "config": "c"}
    if gen_hash:
        rec["generation_provenance"] = {"gold_sha256": gen_hash}
    (raw / "m.jsonl").write_text(json.dumps(rec) + "\n")
    if gold_hash_in_metrics:
        pub = sandbox / "experiments" / "eval" / "agent-dev-T"
        pub.mkdir(parents=True)
        (pub / "m.metrics.json").write_text(json.dumps({"provenance": {"gold_sha256": gold_hash_in_metrics}}))
    gold = sandbox / "gold.jsonl"
    gold.write_text(json.dumps({"case_id": "DEV-001", "question": "q", "split": "dev", "reference_facts": [], "expected_behavior": "answer"}) + "\n")
    return gold


def test_eval_refuses_gold_mismatch_and_writes_nothing(sandbox, monkeypatch):
    gold = make_run(sandbox, "0" * 64)
    with pytest.raises(h.GoldMismatch):
        h.run("agent-dev-T", judge=False, gold_path=gold)
    assert not (sandbox / "experiments" / "eval" / "agent-dev-T-REPORT.md").exists()
    assert not (sandbox / "experiments" / "eval" / "agent-dev-T" / "m.cases.jsonl").exists()


def test_eval_generation_hash_checked_when_never_scored(sandbox):
    gold = make_run(sandbox, None, gen_hash="1" * 64)
    with pytest.raises(h.GoldMismatch):
        h.run("agent-dev-T", judge=False, gold_path=gold)


def test_eval_allow_mismatch_warns_and_writes_gold_hash(sandbox, monkeypatch, capsys):
    gold = make_run(sandbox, "0" * 64)
    monkeypatch.setattr(h, "cached_judgement", lambda *a, **k: None)
    monkeypatch.setattr(h, "case_metrics", lambda case, rec, judged: {"seconds": 1.0, "cost_usd": 0.0, "family": None, "behavior_ok": True})
    monkeypatch.setattr(h, "aggregate", lambda rows: {"n_cases": len(rows)})
    monkeypatch.setattr(h, "by_family", lambda rows: {})
    h.run("agent-dev-T", judge=False, gold_path=gold, allow_gold_mismatch=True)
    assert "WARNING" in capsys.readouterr().out
    metrics = json.loads((sandbox / "experiments" / "eval" / "agent-dev-T" / "m.metrics.json").read_text())
    assert metrics["provenance"]["gold_sha256"] == hashlib.sha256(gold.read_bytes()).hexdigest()


def test_eval_without_raw_runs_keeps_committed_report(sandbox):
    report = sandbox / "experiments" / "eval" / "agent-dev-T-REPORT.md"
    report.parent.mkdir(parents=True)
    report.write_text("committed")
    with pytest.raises(FileNotFoundError):
        h.run("agent-dev-T", judge=False)
    assert report.read_text() == "committed"


def test_p95_is_nearest_rank():
    values = [float(i) for i in range(1, 21)]
    assert h.nearest_rank(values, 0.95) == 19.0
    values = [float(i) for i in range(1, 190)]  # ceil(0.95 * 189) = 180
    assert h.nearest_rank(values, 0.95) == 180.0
    assert h.nearest_rank([5.0], 0.95) == 5.0


def test_paired_checks_gold_hash(sandbox):
    gold = sandbox / "gold.jsonl"
    gold.write_text("{}\n")
    good = hashlib.sha256(gold.read_bytes()).hexdigest()
    arms = {}
    for name, digest in (("a", good), ("b", "2" * 64)):
        path = sandbox / f"{name}.metrics.json"
        path.write_text(json.dumps({"provenance": {"gold_sha256": digest}}))
        arms[name] = path
    with pytest.raises(paired.GoldMismatch, match="b:"):
        paired.check_gold(gold, arms)
    paired.check_gold(gold, {"a": arms["a"]})
    paired.check_gold(gold, arms, allow_mismatch=True)
    with pytest.raises(paired.GoldMismatch):
        paired.check_gold(gold, {"missing": sandbox / "nope.metrics.json"})
