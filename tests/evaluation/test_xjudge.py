"""Synthetic labels only: no provider calls or private corpus required."""
import json

import httpx
import pytest

from labourlens.evaluation import xjudge as x


def item(n, model="gpt-6-luna"):
    case = {"case_id": f"C{n:03}", "family": f"f{n % 3}", "question": "Synthetic question?", "reference_facts": ["Synthetic fact"], "expected_behavior": "answer"}
    rec = {"answer": {"status": "answered", "summary": "Synthetic", "claims": [{"text": "Synthetic", "citations": []}]}}
    j = {"claims": [{"index": 0, "verdict": "supported", "note": ""}], "facts": [{"index": 0, "status": "covered", "note": ""}]}
    return {"case": case, "model": model, "set": ("dev", "heldout", "fresh")[n % 3], "gold_sha256": "hash",
            "arms": {a: {"rec": rec, "original": j, "run": f"synthetic-{a}"} for a in ("r3", "hybrid")}}


def test_sampling_deterministic_and_paired():
    candidates = [item(n) for n in range(100)]
    a = x.stratified_sample(candidates)
    b = x.stratified_sample(list(reversed(candidates)))
    assert [i["case"]["case_id"] for i in a] == [i["case"]["case_id"] for i in b]
    assert len(a) == 60
    assert len({i["case"]["case_id"] for i in a}) == 60
    calls = [(a, arm) for a in a for arm in ("r3", "hybrid")]
    assert [i["case"]["case_id"] for i, a in calls if a == "r3"] == [i["case"]["case_id"] for i, a in calls if a == "hybrid"]
    with pytest.raises(x.JudgeError):
        x.stratified_sample(candidates[:3])


def test_hand_computed_kappa():
    # observed .75, expected .5 => kappa .5
    r = x.agreement(["supported", "supported", "partial", "partial"], ["supported", "supported", "partial", "supported"])
    assert r == {"n": 4, "raw_agreement": .75, "kappa": .5}
    assert x.agreement([True], [True])["kappa"] is None
    assert x.agreement([], [])["n"] == 0


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(x.paths, "EXPERIMENTS", tmp_path / "experiments")
    monkeypatch.setattr(x.paths, "DATA", tmp_path / "data")
    monkeypatch.setattr(x, "load_sample", lambda: ([item(1), item(2)], {"synthetic": 2}))
    monkeypatch.setattr(x.h, "judgement_hash", lambda *a: "oldhash")
    return tmp_path


class Stub:
    def __init__(self):
        self.calls = 0

    def call(self, model, system, user, budget):
        self.calls += 1
        reserved = budget.reserve(100, 100)
        usage = {"input_tokens": 10, "output_tokens": 10}
        budget.settle(reserved, usage)
        return {"judgement": item(0)["arms"]["r3"]["original"], "usage": usage}


def test_stub_outputs_cache_collision_summary(sandbox, capsys):
    stub = Stub()
    assert x.run("first", provider=stub) == 0
    # Identical user payloads are reused, even across arms.
    assert stub.calls == 1
    pub = sandbox / "experiments/xjudge/first"
    summary = json.loads((pub / "summary.json").read_text())
    assert summary["analysis"]["agreement"]["claim_labels"]["raw_agreement"] == 1
    assert summary["cached_calls"] == 3
    assert '"note"' not in (pub / "labels.json").read_text()
    with pytest.raises(FileExistsError):
        x.run("first", provider=stub)
    assert x.run("first", summary_only=True) == 0
    assert stub.calls == 1
    assert "claim_labels" in capsys.readouterr().out


def test_cap_aborts_before_call(sandbox):
    stub = Stub()
    assert x.run("capped", provider=stub, max_usd=.000001) == 1
    summary = json.loads((sandbox / "experiments/xjudge/capped/summary.json").read_text())
    assert summary["status"] == "aborted"
    assert summary["new_spend_list_price_usd"] == 0
    assert summary["analysis"] is None


def test_dry_run_no_calls_or_writes(sandbox):
    stub = Stub()
    assert x.run("dry", provider=stub, dry_run=True) == 0
    assert stub.calls == 0
    assert not (sandbox / "experiments/xjudge/dry").exists()


def test_provider_redacts_key_and_body(monkeypatch):
    secret = "synthetic-private-key"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    def post(*args, **kwargs):
        assert kwargs["headers"]["x-api-key"] == secret
        return httpx.Response(401, text=f"Sensitive body {secret}")
    monkeypatch.setattr(x.httpx, "post", post)
    with pytest.raises(x.JudgeError) as caught:
        x.AnthropicProvider().call(x.JUDGE_MODEL, "s", "u", x.Budget(5, (2, 10)))
    assert secret not in str(caught.value)
    assert "Sensitive body" not in str(caught.value)
    assert x.redact(f"key={secret}") == "key=[REDACTED]"


def test_provider_cap_prevents_http(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    def forbidden(*args, **kwargs):
        pytest.fail("Budget must abort before HTTP")
    monkeypatch.setattr(x.httpx, "post", forbidden)
    with pytest.raises(x.CapExceeded):
        x.AnthropicProvider().call(x.JUDGE_MODEL, "s", "u", x.Budget(.001, (2, 10)))


def test_failed_attempt_retains_reservation(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    monkeypatch.setattr(x.time, "sleep", lambda _: None)
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise httpx.ReadTimeout("secret response")
    monkeypatch.setattr(x.httpx, "post", fail)
    budget = x.Budget(.1, (2, 10))
    with pytest.raises(x.CapExceeded):
        x.AnthropicProvider().call(x.JUDGE_MODEL, "s", "u", budget)
    assert len(calls) == 1
    assert budget.charged > .06


def test_validation_indices_and_labels():
    i = item(1)
    j = i["arms"]["r3"]["original"]
    x.validate(j, i["case"], i["arms"]["r3"]["rec"])
    j["claims"][0]["index"] = 1
    with pytest.raises(x.JudgeError):
        x.validate(j, i["case"], i["arms"]["r3"]["rec"])


def test_sign_flip_and_family_disagreement():
    rows = []
    for arm, original, second in (("r3", "supported", "unsupported"), ("hybrid", "partial", "supported")):
        rows.append({"model": "gpt-6-luna", "set": "dev", "case_id": "S1", "family": "synthetic", "arm": arm,
                     "original": {"claims": [original], "facts": ["covered"]},
                     "second": {"claims": [second], "facts": ["covered"]}})
    result = x.analyse(rows)
    assert result["sign_flip_problem"]
    assert len(result["disagreements_by_family"]["synthetic"]) == 2


def test_cli_forwarding(monkeypatch):
    from labourlens.cli import main
    called = {}
    monkeypatch.setattr(x, "run", lambda exp, **kw: called.update(exp=exp, **kw) or 0)
    assert main(["judge-xfamily", "--experiment", "new", "--dry-run", "--max-usd", "5"]) == 0
    assert called == {"exp": "new", "max_usd": 5, "dry_run": True, "summary_only": False}


def test_native_schema_adapter(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    judgement = item(0)["arms"]["r3"]["original"]
    def post(*args, **kwargs):
        body = kwargs["json"]
        assert body["model"] == x.JUDGE_MODEL
        assert body["output_config"]["format"]["schema"] == x.h.JUDGE_SCHEMA
        assert "tools" not in body
        return httpx.Response(200, json={"usage": {"input_tokens": 30, "output_tokens": 20},
                                       "stop_reason": "end_turn", "content": [{"type": "thinking", "thinking": "private"},
                                                                            {"type": "text", "text": json.dumps(judgement)}]})
    monkeypatch.setattr(x.httpx, "post", post)
    budget = x.Budget(5, (2, 10))
    result = x.AnthropicProvider().call(x.JUDGE_MODEL, "unchanged system", "unchanged input", budget)
    assert result["judgement"] == judgement
    assert budget.actual == pytest.approx(.00026)


class OmissionStub(Stub):
    def __init__(self, recover):
        super().__init__()
        self.recover = recover
        self.payloads = []

    def call(self, model, system, user, budget):
        self.payloads.append((model, system, user))
        result = super().call(model, system, user, budget)
        if self.calls == 1 or not self.recover:
            result["judgement"] = json.loads(json.dumps(result["judgement"]))
            result["judgement"]["claims"].append(dict(result["judgement"]["claims"][0]))
        return result


def test_duplicate_indices_retry_same_prompt_preserves_cache(sandbox):
    stub = OmissionStub(recover=True)
    assert x.run("retry-recovered", provider=stub) == 0
    assert stub.calls == 2
    assert stub.payloads[0] == stub.payloads[1]
    cache_dir = sandbox / "data/runs/xjudge"
    originals = list(cache_dir.glob("*.json"))
    assert len(originals) == 2
    before = {p.name: p.read_bytes() for p in originals}
    first = next(p for p in originals if ".retry1." not in p.name)
    assert len(json.loads(first.read_text())["judgement"]["claims"]) == 2
    second_stub = Stub()
    assert x.run("retry-reused", provider=second_stub) == 0
    assert second_stub.calls == 0
    assert {p.name: p.read_bytes() for p in originals} == before
    summary = json.loads((sandbox / "experiments/xjudge/retry-recovered/summary.json").read_text())
    assert summary["analysis"]["omission_problem"] is False
    assert summary["semantic_retries"] == 4
    assert summary["processed_judge_attempts"] == 8
    assert summary["tokens_including_cached_calls"]["output_tokens"] == 80


def test_persistent_invalid_indices_are_reported_not_imputed(sandbox):
    stub = OmissionStub(recover=False)
    assert x.run("retry-omitted", provider=stub) == 0
    assert stub.calls == 2  # one initial and one retry; remaining identical items reuse both
    pub = sandbox / "experiments/xjudge/retry-omitted"
    summary = json.loads((pub / "summary.json").read_text())
    analysis = summary["analysis"]
    assert summary["status"] == "complete"
    assert analysis["omission_problem"] is True
    assert analysis["judge_omitted"]["count"] == 4
    assert analysis["agreement"]["claim_labels"]["n"] == 0
    assert analysis["denominators"]["gpt-6-luna/all"]["analysed_pairs"] == 0
    assert analysis["denominators"]["gpt-6-luna/all"]["excluded_pairs"] == 2
    rows = json.loads((pub / "labels.json").read_text())
    assert all(r["status"] == "judge_omitted" and r["second"] is None for r in rows)
    assert rows[0]["attempts"][0]["diagnostics"]["claims"] == {"expected": 1, "returned": 2, "indices": [0, 0]}
    assert '"note"' not in (pub / "labels.json").read_text()


def test_one_omission_excludes_partner_explicitly():
    good = {"model": "m", "set": "dev", "family": "f", "status": "valid",
            "original": {"claims": ["supported"], "facts": ["covered"]}, "second": {"claims": ["supported"], "facts": ["covered"]}}
    rows = [{**good, "case_id": "1", "arm": a} for a in ("r3", "hybrid")]
    rows += [{**good, "case_id": "2", "arm": "r3"},
             {**good, "case_id": "2", "arm": "hybrid", "status": "judge_omitted", "second": None}]
    out = x.analyse(rows)
    assert out["agreement"]["claim_labels"]["n"] == 2
    assert out["judge_omitted"]["count"] == 1
    assert out["denominators"]["m/dev"] == {"sampled_items": 4, "valid_items": 3, "judge_omitted_items": 1,
                                           "sampled_pairs": 2, "analysed_pairs": 1, "excluded_pairs": 1}
    assert out["excluded_valid_partners"] == [{"model": "m", "set": "dev", "case_id": "2", "arm": "r3", "family": "f"}]


@pytest.mark.parametrize("field", ["claims", "facts"])
def test_missing_labels_and_out_of_range_indices(field):
    i = item(1)
    judgement = json.loads(json.dumps(i["arms"]["r3"]["original"]))
    judgement[field] = []
    with pytest.raises(x.IncompleteJudgement):
        x.validate(judgement, i["case"], i["arms"]["r3"]["rec"])
    judgement = json.loads(json.dumps(i["arms"]["r3"]["original"]))
    judgement[field][0]["index"] = 99
    with pytest.raises(x.IncompleteJudgement):
        x.validate(judgement, i["case"], i["arms"]["r3"]["rec"])
