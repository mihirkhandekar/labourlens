import numpy as np
import pytest

from labourlens import paths
from labourlens.retrieval import dense as dn


def test_rrf_rewards_agreement_over_single_list_rank():
    a = [("x", 9.0), ("y", 8.0), ("z", 7.0)]
    b = [("y", 0.9), ("w", 0.8), ("x", 0.7)]
    fused = [cid for cid, _ in dn.rrf([a, b], k=4)]
    assert fused[:2] == ["y", "x"]  # present in both lists, so ahead of z and w which are in one
    assert set(fused) == {"x", "y", "z", "w"}


def test_rrf_is_scale_free():
    a = [("x", 1000.0), ("y", 1.0)]
    b = [("y", 0.5), ("x", 0.4)]
    assert dn.rrf([a, b]) == dn.rrf([[(c, s * 1e-6) for c, s in a], b])


@pytest.fixture
def fake_api(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INDEX", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    calls: list[list[str]] = []

    def call(client, model, inputs, key):
        calls.append(list(inputs))
        return [[float(len(t)), 1.0, 0.0] for t in inputs], 7 * len(inputs)

    monkeypatch.setattr(dn, "_call", call)
    return calls


def test_cache_serves_repeats_and_reembeds_changed_text(fake_api):
    v1 = dn.embed("m", ["alpha", "beta"], "chunks")
    assert len(fake_api) == 1 and v1.shape == (2, 3)
    assert np.allclose(np.linalg.norm(v1, axis=1), 1.0)  # normalised, so dot product is cosine
    dn.embed("m", ["alpha", "beta"], "chunks")
    assert len(fake_api) == 1  # fully cached, no second call
    dn.embed("m", ["alpha", "beta changed"], "chunks")
    assert fake_api[-1] == ["beta changed"]  # only the changed text is sent
    assert dn.usage_totals("m")["tokens"] == 7 * 3


def test_cache_is_per_model(fake_api):
    dn.embed("m1", ["alpha"], "chunks")
    dn.embed("m2", ["alpha"], "chunks")
    assert len(fake_api) == 2


def test_missing_key_with_incomplete_cache_fails_loudly(fake_api, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(dn.EmbeddingError, match="OPENAI_API_KEY"):
        dn.embed("m", ["never seen"], "chunks")
