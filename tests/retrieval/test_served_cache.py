"""Offline tests for the served annual search cache. Network stages are replaced by counters; nothing here calls an API."""
import threading
import time
from types import SimpleNamespace

import numpy as np
import pytest

from labourlens.agent import tools as tl
from labourlens.retrieval import dense, served_cache as sc


@pytest.fixture(autouse=True)
def fresh_caches(monkeypatch):
    monkeypatch.setattr(sc, "SEARCHES", sc.SingleflightLRU(8))
    monkeypatch.setattr(sc, "QUERY_VECTORS", sc.SingleflightLRU(8))


def make_tools(corpus=None, *, annual=True, flag=True, question="Q", retrieval="r3w"):
    corpus = {"content_sha256": "a"} if corpus is None else corpus
    chunk = SimpleNamespace(chunk_id="c1", source_passage_ids=["p1"])
    passage = {"source_id": "mom-2025-q1-final", "document_title": "T", "publication_date": "2025-06-01",
               "release_stage": "final", "locator": "p.1", "text": "Figure 1.0%"}
    sh = SimpleNamespace(corpus=corpus, served_search_cache=flag, stats_backend=None, mcp_routed=frozenset(),
                         retriever=SimpleNamespace(dense=SimpleNamespace(cfg=SimpleNamespace(model="m"))),
                         chunks_by_id={"c1": chunk}, passages_by_id={"p1": passage})
    t = tl.Tools(sh, retrieval=retrieval, question=question)
    t.tool_set = "annual" if annual else "base"
    calls = []

    def uncached(query, k):
        calls.append((query, k))
        return ([("c1", 1.0)], {"reranked": True, "rerank_fallback": False, "rerank_seconds": 1.0, "rerank_cost_usd": 0.01},
                {"calls": 1, "prompt_tokens": 5, "completion_tokens": 1, "cost_usd": 0.01, "llm_seconds": 1.0}, sh.chunks_by_id, sh.passages_by_id)

    t._search_uncached = uncached
    return t, calls


def test_hit_costs_nothing_and_marks_trace():
    t, calls = make_tools()
    first = t._search("2025-Q1 retrenchment", 5)
    second = t._search("2025-Q1   retrenchment", 5)
    assert len(calls) == 1
    assert first[2]["cost_usd"] == 0.01 and second[2] == {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0}
    assert second[1]["search_cache_hit"] is True and first[1]["search_cache_hit"] is False and second[1]["rerank_cost_usd"] == 0.0


@pytest.mark.parametrize("other", [("2025-Q2 retrenchment", 5, "Q"), ("2025-q1 retrenchment", 5, "Q"),
                                   ("2025-Q1 retrenchment", 6, "Q"), ("2025-Q1 retrenchment", 5, "Q2")])
def test_meaning_changes_do_not_share(other):
    t, calls = make_tools()
    t._search("2025-Q1 retrenchment", 5)
    t.question = other[2]
    t._search(other[0], other[1])
    assert len(calls) == 2


def test_corpus_change_invalidates_and_question_whitespace_shares():
    a, calls_a = make_tools({"content_sha256": "a"}, question="why  up")
    b, calls_b = make_tools({"content_sha256": "b"}, question="why up")
    a._search("x", 5)
    b._search("x", 5)
    assert len(calls_a) == len(calls_b) == 1
    c, calls_c = make_tools({"content_sha256": "a"}, question="why up")
    c._search("x", 5)
    assert calls_c == []


def test_legacy_and_disabled_paths_never_cache():
    for kw in ({"annual": False}, {"flag": False}, {"corpus": {}}):
        corpus = kw.pop("corpus", None)
        t, calls = make_tools(corpus, **kw)
        t._search("x", 5), t._search("x", 5)
        assert len(calls) == 2


def test_fallback_and_errors_are_not_retained():
    cache = sc.SingleflightLRU(2)
    n = []

    def boom():
        n.append(1)
        raise RuntimeError("transient")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            cache.get_or_compute("k", boom)
    assert len(n) == 2
    cache.get_or_compute("f", lambda: {"fallback": True}, eligible=lambda v: not v["fallback"])
    assert cache.get_or_compute("f", lambda: {"fallback": False})[1] is False


def test_lru_eviction_and_ttl():
    cache = sc.SingleflightLRU(2, ttl_s=0.05)
    for k in "abc":
        cache.get_or_compute(k, lambda k=k: k)
    assert cache.get_or_compute("a", lambda: "new")[1] is False  # evicted
    assert cache.get_or_compute("c", lambda: "new")[0] == "c"
    time.sleep(0.07)
    assert cache.get_or_compute("c", lambda: "new") == ("new", False)


def test_identical_concurrent_requests_share_one_computation():
    cache = sc.SingleflightLRU(4)
    gate, started, count = threading.Event(), threading.Event(), []

    def compute():
        count.append(1)
        started.set()
        gate.wait(2)
        return "v"

    out = []
    threads = [threading.Thread(target=lambda: out.append(cache.get_or_compute("k", compute))) for _ in range(4)]
    threads[0].start()
    started.wait(2)
    for th in threads[1:]:
        th.start()
    time.sleep(0.05)
    gate.set()
    for th in threads:
        th.join(2)
    assert len(count) == 1 and sorted(h for _, h in out) == [False, True, True, True]


def test_query_vector_reuses_disk_embed_once(monkeypatch):
    calls = []
    monkeypatch.setattr(dense, "embed", lambda model, texts, purpose: calls.append(texts) or np.ones((1, 2), dtype=np.float32))
    corpus = {"content_sha256": "a"}
    sc.query_vector(corpus, "m", "Retrenchment  2025-Q1", 1.0)
    sc.query_vector(corpus, "m", "Retrenchment 2025-Q1", 1.0)
    sc.query_vector(corpus, "m", "retrenchment 2025-Q1", 1.0)  # case may change embedding: separate
    assert calls == [["Retrenchment 2025-Q1"], ["retrenchment 2025-Q1"]]
