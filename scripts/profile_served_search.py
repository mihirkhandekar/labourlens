"""Offline profile of the served annual search internals; writes experiments/served_search_profile.json.

Network boundary: rerank (LLM) and cold query embedding are NETWORK stages. This script never calls them and records them as
"network_not_measured"; the cache-hit rows show only avoided local orchestration, not real network savings. BM25, cosine, RRF and the
process cache are LOCAL and measured with the real local index when its embedding cache is complete (no key, no API), else skipped.
"""
from __future__ import annotations

import json
import statistics
import time

import numpy as np

from labourlens import paths
from labourlens.retrieval import dense, served_cache

OUT = paths.ROOT / "experiments" / "served_search_profile.json"
QUERY = "2025-Q4 retrenchment reasons"


def timed(fn, n=30):
    xs = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        xs.append((time.perf_counter() - t) * 1000)
    return {"median_ms": round(statistics.median(xs), 4), "max_ms": round(max(xs), 4), "runs": n}


def main() -> None:
    rows = {"rerank_llm": {"boundary": "network", "status": "network_not_measured"},
            "cold_query_embedding": {"boundary": "network", "status": "network_not_measured"}}
    cache = served_cache.SingleflightLRU(64)
    rows["process_cache_hit"] = {"boundary": "local", **timed(lambda: cache.get_or_compute("k", lambda: [1]))}
    try:
        from labourlens.retrieval import runtime

        retr, chunks, _, corpus = runtime.load_search_world()
        vec = dense.VectorCache(runtime.EMBEDDING_MODEL).get(dense._h(runtime.EMBEDDING_MODEL, QUERY))
        rows["bm25"] = {"boundary": "local", **timed(lambda: retr.bm25.search(QUERY, retr.depth))}
        label = "disk_vector_cache_cosine"
        if vec is None:  # the matrix product does not depend on vector content; a random unit vector avoids a network embed
            vec = np.random.default_rng(0).standard_normal(retr.dense.matrix.shape[1]).astype(np.float32)
            vec /= np.linalg.norm(vec)
            label = "cosine_synthetic_query_vector"
        rows[label] = {"boundary": "local", **timed(lambda: retr.dense.search_vector(vec, retr.depth))}
        rows["hybrid_rrf"] = {"boundary": "local", **timed(lambda: retr.search_vector(QUERY, vec, retr.depth))}
        rows["corpus"] = corpus
    except Exception as e:  # incomplete local index is a legitimate offline environment
        rows["local_index"] = {"boundary": "local", "status": f"skipped: {type(e).__name__}: {str(e)[:120]}"}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "query": QUERY, "stages": rows}, indent=2, default=str))
    print(json.dumps(rows, indent=2, default=str))


if __name__ == "__main__":
    main()
