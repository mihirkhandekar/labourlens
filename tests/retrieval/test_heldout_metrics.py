"""Synthetic-only tests for the pre-registered retrieval diagnostics."""
import json
from types import SimpleNamespace

import pytest

from labourlens.retrieval import heldout_metrics as hm


def fixture_world():
    passages = {}
    for i in range(12):
        passages[f"p{i}"] = {"passage_id": f"p{i}", "source_id": "synthetic", "snapshot_id": "v1",
                               "document_title": "Synthetic report", "publication_date": None,
                               "release_stage": "final", "locator": str(i), "text": f"Constructed passage {i}"}
    chunks = {"merged": SimpleNamespace(source_passage_ids=tuple(f"p{i}" for i in range(10))),
              "tail": SimpleNamespace(source_passage_ids=("p10", "p11"))}
    return SimpleNamespace(chunks=chunks, passages_by_id=passages)


def case(pid="p9"):
    return {"case_id": "synthetic-1", "family": "factual_lookup", "question": "Synthetic question?",
            "expected_behavior": "answer", "evidence_text": [{"passage_ids": [pid]}]}


def test_merged_chunk_hit_is_not_strict_first_eight_passages():
    row = hm.score(case(), ["merged", "tail"], fixture_world())
    assert row["first_relevant_rank"] == 1
    assert row["strict_passage_hit@8"] is False
    metrics = hm.aggregate([row])
    assert metrics["chunk_hit@8"] == {"mean": 1.0, "ci95": [1.0, 1.0]}
    assert metrics["strict_passage_hit@8"] == {"mean": 0.0, "ci95": [0.0, 0.0]}
    assert metrics["mrr@10"]["mean"] == 1.0


def test_context_uses_same_snapshot_text_deduplication():
    world = fixture_world()
    world.passages_by_id["p1"]["text"] = world.passages_by_id["p0"]["text"]
    # p8 moves from ninth to eighth after the application context builder deduplicates p1.
    row = hm.score(case("p8"), ["merged"], world)
    assert row["strict_passage_hit@8"] is True
    assert row["context_first8_ids"] == ["p0", "p2", "p3", "p4", "p5", "p6", "p7", "p8"]


def test_mrr_cutoff_and_reproducible_case_bootstrap():
    rows = [{"case_id": str(i), "first_relevant_rank": rank, "strict_passage_hit@8": strict}
            for i, (rank, strict) in enumerate(((2, True), (10, False), (None, False), (11, False)))]
    a = hm.aggregate(rows)
    assert a == hm.aggregate(rows)
    assert a["chunk_hit@8"]["mean"] == 0.25
    assert a["mrr@10"]["mean"] == 0.15
    assert a["mrr@10"]["ci95"][0] <= 0.15 <= a["mrr@10"]["ci95"][1]
    p = hm.paired(rows, rows)
    assert p["mrr@10"] == {"mean_difference": 0.0, "ci95": [0.0, 0.0], "better": 0, "worse": 0}
    with pytest.raises(ValueError, match="identical IDs"):
        hm.paired(rows, rows[::-1])
    with pytest.raises(ValueError, match="empty"):
        hm.aggregate([])


def test_rerank_cache_never_calls_model_and_rejects_corruption(tmp_path, monkeypatch):
    monkeypatch.setattr(hm.rr, "load_prompt", lambda: ("synthetic", "{question}", "hash"))
    candidates = [SimpleNamespace(chunk_id="a"), SimpleNamespace(chunk_id="b")]
    key = hm.rerank_key("Synthetic?", candidates)
    assert hm.cached_rerank("Synthetic?", candidates, [tmp_path]) is None
    result = hm.rr.RerankResult([1, 0])
    (tmp_path / f"{key}.json").write_text(json.dumps({"result": result.__dict__}))
    assert hm.cached_rerank("Synthetic?", candidates, [tmp_path]).cached
    result.order = [1, 1]
    (tmp_path / f"{key}.json").write_text(json.dumps({"result": result.__dict__}))
    with pytest.raises(ValueError, match="invalid cached"):
        hm.cached_rerank("Synthetic?", candidates, [tmp_path])


def test_audit_and_offline_miss_are_network_free(tmp_path, monkeypatch):
    world = fixture_world()
    world.cache_dir = tmp_path / "v31"
    world.qv_file = tmp_path / "absent.json"
    world.query_vector = lambda q: None
    world.full_rankings = lambda q: pytest.fail("missing vector should prevent ranking")
    monkeypatch.setattr(hm.paths, "ROOT", tmp_path)
    monkeypatch.setattr(hm.paths, "EXPERIMENTS", tmp_path / "experiments")
    monkeypatch.setattr(hm.exp, "World", lambda *a, **k: world)
    monkeypatch.setattr(hm.exp, "provenance", lambda *a: {"corpus_version": "v3.1", "corpus_hash": "synthetic"})
    monkeypatch.setattr(hm, "load_sets", lambda: ({"test": [case()]}, {"test": {"text_n": 1}}))
    monkeypatch.setattr(hm.dn, "VectorCache", lambda *a: SimpleNamespace(get=lambda key: None))
    monkeypatch.setattr(hm.dn, "embed", lambda *a, **k: pytest.fail("audit must not embed"))
    monkeypatch.setattr(hm.rr, "rerank", lambda *a, **k: pytest.fail("audit must not rerank"))
    monkeypatch.setattr(hm, "digest", lambda p: "synthetic-hash")
    monkeypatch.setattr(hm.rr, "render", lambda chunks: "Synthetic candidates")
    audit = hm.execute("audit")
    assert audit["missing_unique_query_count"] == 1
    assert audit["missing_query_embeddings"][0]["case_id"] == "synthetic-1"
    assert "question" not in audit["missing_query_embeddings"][0]
    assert audit["rerank_audit_complete"] is False
    assert audit["embedding_estimated_cost_usd"] > 0
    assert not (tmp_path / "experiments/eval/audit/metrics.json").exists()
    with pytest.raises(ValueError, match="already exists"):
        hm.execute("audit")
    with pytest.raises(ValueError, match="offline cache incomplete"):
        hm.execute("offline", run=True)
    assert (tmp_path / "experiments/eval/offline/audit.json").exists()


def test_invalid_id_and_paid_audit_refused():
    with pytest.raises(ValueError, match="invalid experiment"):
        hm.execute("../overwrite")
    with pytest.raises(ValueError, match="requires"):
        hm.execute("test", allow_paid=True)


def test_complete_offline_run_writes_every_arm_without_calls(tmp_path, monkeypatch):
    world = fixture_world()
    world.cache_dir = tmp_path / "v31"
    world.qv_file = tmp_path / "vectors.json"
    world.qv_file.write_text(json.dumps({hm.hashlib.sha256(case()["question"].encode()).hexdigest(): [1.0]}))
    monkeypatch.setattr(hm.paths, "ROOT", tmp_path)
    monkeypatch.setattr(hm.paths, "EXPERIMENTS", tmp_path / "experiments")
    monkeypatch.setattr(hm.exp, "World", lambda *a, **k: world)
    monkeypatch.setattr(hm.exp, "provenance", lambda *a: {"corpus_version": "v3.1", "corpus_hash": "synthetic"})
    monkeypatch.setattr(hm, "load_sets", lambda: ({"test": [case()]}, {"test": {"text_n": 1}}))
    monkeypatch.setattr(hm.dn, "VectorCache", lambda *a: SimpleNamespace(get=lambda key: None))
    monkeypatch.setattr(hm.dn, "embed", lambda *a, **k: pytest.fail("offline must not embed"))
    monkeypatch.setattr(hm.rr, "rerank", lambda *a, **k: pytest.fail("offline must not rerank"))
    monkeypatch.setattr(hm, "digest", lambda p: "synthetic-hash")
    monkeypatch.setattr(hm, "pools", lambda *a: {m: ["merged", "tail"] for m in hm.METHODS if m not in ("R2", "R3")})
    monkeypatch.setattr(hm, "cached_rerank", lambda *a: hm.rr.RerankResult([0, 1], cached=True))
    result = hm.execute("offline-complete", run=True)
    assert set(result["results"]["test"]["metrics"]) == set(hm.METHODS)
    assert result["new_rerank_cost_usd"] == 0
    assert result["results"]["test"]["rerank_failures"] == {"R2": 0, "R3": 0}
    output = tmp_path / "experiments/eval/offline-complete"
    assert len((output / "scores.jsonl").read_text().splitlines()) == len(hm.METHODS)
    assert (output / "metrics.json").exists()
