from concurrent.futures import ThreadPoolExecutor

import httpx
import numpy as np
import pytest

from labourlens.retrieval import dense


def test_concurrent_cache_writers_merge_atomic_snapshots(tmp_path, monkeypatch):
    monkeypatch.setattr(dense.paths, 'INDEX', tmp_path)
    caches = [dense.VectorCache('fixture') for _ in range(12)]
    def put(i):
        caches[i].put_many([(str(i), np.asarray([i, 1], dtype=np.float32))])
        # Every observed snapshot must have consistent key/vector counts.
        current = dense.VectorCache('fixture')
        assert len(current.keys) == len(current.vecs)
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(put, range(12)))
    saved = dense.VectorCache('fixture')
    assert len(saved.keys) == 12
    for i in range(12):
        np.testing.assert_array_equal(saved.get(str(i)), [i, 1])


def test_embedding_retries_cannot_outlive_deadline(monkeypatch):
    calls = []
    class Client:
        def post(self, *args, **kwargs):
            calls.append(kwargs['timeout'])
            return httpx.Response(429)
    monkeypatch.setattr(dense.time, 'sleep', lambda _: pytest.fail('retry sleep exceeds deadline'))
    with dense.embedding_deadline(0.1), pytest.raises(dense.EmbeddingError, match='deadline'):
        dense._call(Client(), 'fixture', ['fixture'], 'not-a-secret')
    assert len(calls) == 1 and 0 < calls[0] < 0.1
