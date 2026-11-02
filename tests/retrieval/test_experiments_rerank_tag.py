"""Tagged retrieval outputs are isolated without model calls or local corpus data."""
import json
from types import SimpleNamespace

import pytest

from labourlens.retrieval import experiments_rerank as exp


def test_output_paths_preserve_legacy_and_isolate_tag(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "RUNS", tmp_path)
    old, new = exp.RunPaths(), exp.RunPaths("V31")
    for name in ("R0", "R1a", "R1b", "R1b_x0.5", "R1b_x2", "R2", "R3"):
        assert old.config(name) == tmp_path / f"dev-{name}"
        assert new.config(name) == tmp_path / f"dev-R-V31-{name}"
        assert old.config(name) != new.config(name)
    assert old.summary() == tmp_path / "dev-R-summary.json"
    assert old.summary(True) == tmp_path / "dev-R-SUMMARY.md"
    assert new.summary() == tmp_path / "dev-R-V31" / "summary.json"
    assert new.summary(True) == tmp_path / "dev-R-V31" / "SUMMARY.md"
    assert new.cache("corpus-a") != new.cache("corpus-b")
    before = new.cache("corpus-a")
    monkeypatch.setattr(exp.rt, "EMBEDDING_MODEL", "another-model")
    assert new.cache("corpus-a") != before


@pytest.mark.parametrize("tag", ["", "../R0", "a/b", ".", "x y"])
def test_tag_rejects_path_escape(tag):
    with pytest.raises(ValueError):
        exp.RunPaths(tag)


def test_existing_tag_refused_before_loading_world(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "RUNS", tmp_path)
    exp.RunPaths("V31").config("R0").mkdir()
    monkeypatch.setattr(exp, "World", lambda *args: pytest.fail("must refuse before loading corpus"))
    with pytest.raises(SystemExit, match="already exists"):
        exp.run(tag="V31")


def test_tagged_run_writes_all_outputs_without_touching_frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "RUNS", tmp_path / "runs")
    gold = tmp_path / "gold"
    gold.mkdir()
    (gold / "draft_cases.jsonl").write_text("synthetic gold\n")
    monkeypatch.setattr(exp.ev, "GOLD", gold)
    case = {"case_id": "DEV-TEST", "family": "lookup", "question": "test"}
    monkeypatch.setattr(exp.ev, "load_cases", lambda _: [case])
    monkeypatch.setattr(exp.ev, "text_cases", lambda cases: cases)
    monkeypatch.setattr(exp.ev, "gold_passages", lambda _: {"p"})
    chunk = SimpleNamespace(source_passage_ids=["p"])
    world = SimpleNamespace(chunks={"c": chunk}, n=1, bm25=None, dense=None,
                            full_rankings=lambda _: (([], []), []))
    monkeypatch.setattr(exp, "World", lambda *args: world)
    monkeypatch.setattr(exp.dn, "HybridIndex", lambda *args: SimpleNamespace(search=lambda *args: [("c", 1.0)]))
    monkeypatch.setattr(exp, "fuse", lambda *args: [("c", 1.0)])
    monkeypatch.setattr(exp, "hint_sets", lambda _: (None, None))
    monkeypatch.setattr(exp.pr, "matching_sources", lambda _: None)
    monkeypatch.setattr(exp, "coverage_check", lambda label, *args: {
        "config": label, "gold_in_context_of_top8_chunks": 1.0, "gold_in_first8_context_passages": 1.0})
    monkeypatch.setattr(exp.ck, "corpus_hash", lambda _: "corpus")
    monkeypatch.setattr(exp.time, "time", lambda: 0.0)
    monkeypatch.setattr(exp.time, "perf_counter", lambda: 0.0)
    metadata = {"corpus_version": "v3.1", "chunk_count": 1847, "corpus_hash": "corpus", "code_commit": "commit"}
    monkeypatch.setattr(exp, "provenance", lambda chunks, gold_sha: metadata | {"gold_file_sha256": gold_sha})
    exp.run(rerank_on=False)
    frozen = {p: p.read_bytes() for p in exp.RUNS.rglob("*") if p.is_file()}
    exp.run(rerank_on=False, tag="V31")
    assert all(p.read_bytes() == content for p, content in frozen.items())
    tagged = exp.RunPaths("V31")
    for name in ("R0", "R1a", "R1b", "R1b_x0.5", "R1b_x2"):
        metrics = json.loads((tagged.config(name) / "metrics.json").read_text())
        assert metrics["config"].items() >= metadata.items()
        assert len(metrics["config"]["gold_file_sha256"]) == 64
        assert (tagged.config(name) / "scores.jsonl").is_file()
        legacy = json.loads((exp.RunPaths().config(name) / "metrics.json").read_text())
        assert metrics["metrics"] == legacy["metrics"]
        assert "code_commit" not in legacy["config"]
    assert json.loads(tagged.summary().read_text())["corpus_version"] == "v3.1"
    assert "v3.1 re-run" in tagged.summary(True).read_text()
    assert "Changed versus the frozen R-series" in tagged.summary(True).read_text()


def test_methods_run_is_offline_isolated_and_matches_r0(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "RUNS", tmp_path / "runs")
    r0 = exp.RunPaths("T").config("R0")
    r0.mkdir(parents=True)
    (r0 / "scores.jsonl").write_text(json.dumps({"case_id": "DEV-1", "first_relevant_rank": 2}) + "\n")
    (r0 / "metrics.json").write_text(json.dumps({"metrics": {"hit@8": 1.0}}))
    frozen = {p: p.read_bytes() for p in exp.RUNS.rglob("*") if p.is_file()}
    gold = tmp_path / "gold"
    gold.mkdir()
    (gold / "draft_cases.jsonl").write_text("synthetic gold\n")
    monkeypatch.setattr(exp.ev, "GOLD", gold)
    case = {"case_id": "DEV-1", "family": "lookup", "question": "q"}
    monkeypatch.setattr(exp.ev, "load_cases", lambda _: [case])
    monkeypatch.setattr(exp.ev, "text_cases", lambda cases: cases)
    monkeypatch.setattr(exp.ev, "gold_passages", lambda _: {"p"})
    chunks = {"a": SimpleNamespace(source_passage_ids=["x"]), "b": SimpleNamespace(source_passage_ids=["p"])}
    seen = {}

    def world(run_paths, offline=False):
        seen["offline"] = offline
        return SimpleNamespace(chunks=chunks, n=2, full_rankings=lambda _: (([("a", 1.0), ("b", 0.5)], []), [("b", 0.9), ("a", 0.1)]))
    monkeypatch.setattr(exp, "World", world)
    monkeypatch.setattr(exp, "fuse", lambda *args: [("a", 1.0), ("b", 0.9)])
    monkeypatch.setattr(exp, "provenance", lambda c, sha: {"corpus_version": "v3.1", "chunk_count": 1847, "corpus_hash": "h", "gold_file_sha256": sha, "code_commit": "c"})
    out = exp.run_methods("T")
    assert seen["offline"] is True
    d = exp.methods_dir("T")
    assert d == exp.RUNS / "dev-R-T-methods" and d != exp.RunPaths("T").config("R0")
    assert out["metrics"]["bm25"]["hit@8"] == 1.0 and out["hybrid_matches_R0_first_relevant_rank"]["matching_cases"] == 1
    row = json.loads((d / "scores.jsonl").read_text())
    assert (row["bm25_first_relevant_rank"], row["dense_first_relevant_rank"], row["hybrid_first_relevant_rank"]) == (2, 1, 2)
    assert "Why the early deck figure differs" in (d / "SUMMARY.md").read_text()
    assert all(p.read_bytes() == c for p, c in frozen.items())
    with pytest.raises(SystemExit, match="already exists"):
        exp.run_methods("T")
