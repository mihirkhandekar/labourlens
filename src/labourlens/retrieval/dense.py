"""Dense retrieval with hosted OpenAI embeddings (D-021, D-022) and hybrid fusion.

Vectors are cached on disk (data/index/embeddings/<model>/), keyed by sha256(model + exact embedded text), so a
rerun costs nothing and a changed chunk text is re-embedded rather than served stale. Every API call appends its
token usage to usage.jsonl; cost is computed from measured tokens, never estimated. The API key is read from the
OPENAI_API_KEY environment variable only and is never written to disk or logs.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np

from labourlens import paths
from labourlens.retrieval.chunk import Chunk

API = "https://api.openai.com/v1/embeddings"
BATCH = 128
MAX_RETRIES = 5
TIMEOUT_S = 60.0


class EmbeddingError(RuntimeError):
    pass


@dataclass(frozen=True)
class DenseConfig:
    model: str = "text-embedding-3-small"
    header: bool = False  # prepend document title and section heading to the embedded text

    def key(self) -> str:
        return f"{self.model}{'+hdr' if self.header else ''}"


def embed_text(c: Chunk, header: bool) -> str:
    if not header:
        return c.text
    return f"{c.document_title} | {c.section_heading}\n{c.text}"


def _h(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\x00{text}".encode()).hexdigest()


class VectorCache:
    """Append-only cache: one .npy shard per write plus a key list. Small corpus, so simple beats clever."""

    def __init__(self, model: str) -> None:
        self.dir = paths.INDEX / "embeddings" / model
        self.dir.mkdir(parents=True, exist_ok=True)
        self.keys: dict[str, int] = {}
        self.vecs: list[np.ndarray] = []
        kf, vf = self.dir / "keys.json", self.dir / "vectors.npy"
        if kf.exists() and vf.exists():
            ks = json.loads(kf.read_text())
            m = np.load(vf)
            if len(ks) == len(m):
                self.keys = {k: i for i, k in enumerate(ks)}
                self.vecs = list(m)

    def get(self, key: str) -> np.ndarray | None:
        i = self.keys.get(key)
        return None if i is None else self.vecs[i]

    def put_many(self, items: list[tuple[str, np.ndarray]]) -> None:
        for k, v in items:
            if k not in self.keys:
                self.keys[k] = len(self.vecs)
                self.vecs.append(v)
        np.save(self.dir / "vectors.npy", np.vstack(self.vecs).astype(np.float32))
        (self.dir / "keys.json").write_text(json.dumps(list(self.keys)))

    def log_usage(self, n_inputs: int, tokens: int, seconds: float, purpose: str) -> None:
        with (self.dir / "usage.jsonl").open("a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "inputs": n_inputs, "tokens": tokens,
                                "seconds": round(seconds, 2), "purpose": purpose}) + "\n")


def _call(client: httpx.Client, model: str, inputs: list[str], key: str) -> tuple[list[list[float]], int]:
    for attempt in range(MAX_RETRIES):
        try:
            r = client.post(API, json={"model": model, "input": inputs}, headers={"Authorization": f"Bearer {key}"})
        except httpx.TransportError:
            r = None
        if r is not None and r.status_code == 200:
            d = r.json()
            data = sorted(d["data"], key=lambda x: x["index"])
            return [x["embedding"] for x in data], int(d["usage"]["total_tokens"])
        if r is not None and r.status_code not in (429, 500, 502, 503, 504):
            raise EmbeddingError(f"embeddings API returned {r.status_code}: {r.text[:200]}")
        time.sleep(2 ** attempt)
    raise EmbeddingError(f"embeddings API failed after {MAX_RETRIES} attempts")


def embed(model: str, texts: list[str], purpose: str) -> np.ndarray:
    """Return L2-normalised vectors for texts, using the cache and calling the API only for misses."""
    key = os.environ.get("OPENAI_API_KEY")
    cache = VectorCache(model)
    hashes = [_h(model, t) for t in texts]
    missing = list(dict.fromkeys(h for h in hashes if cache.get(h) is None))
    if missing:
        if not key:
            raise EmbeddingError("OPENAI_API_KEY is not set and the embedding cache is incomplete")
        text_of = dict(zip(hashes, texts))
        with httpx.Client(timeout=TIMEOUT_S) as client:
            for i in range(0, len(missing), BATCH):
                part = missing[i:i + BATCH]
                t0 = time.perf_counter()
                vs, tokens = _call(client, model, [text_of[h] for h in part], key)
                cache.log_usage(len(part), tokens, time.perf_counter() - t0, purpose)
                arr = np.asarray(vs, dtype=np.float32)
                arr /= np.linalg.norm(arr, axis=1, keepdims=True)
                cache.put_many(list(zip(part, arr)))
    return np.vstack([cache.get(h) for h in hashes])


class DenseIndex:
    def __init__(self, chunks: list[Chunk], cfg: DenseConfig) -> None:
        self.cfg, self.chunk_ids = cfg, [c.chunk_id for c in chunks]
        self.matrix = embed(cfg.model, [embed_text(c, cfg.header) for c in chunks], purpose="chunks")

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        q = embed(self.cfg.model, [query], purpose="queries")[0]
        s = self.matrix @ q
        top = np.argsort(-s)[:k]
        return [(self.chunk_ids[int(i)], float(s[i])) for i in top]


def rrf(rankings: list[list[tuple[str, float]]], k: int = 10, c: int = 60) -> list[tuple[str, float]]:
    """Reciprocal rank fusion: score = sum 1/(c + rank). Rank-based, so BM25 and cosine scores need no calibration."""
    score: dict[str, float] = {}
    for r in rankings:
        for rank, (cid, _) in enumerate(r, 1):
            score[cid] = score.get(cid, 0.0) + 1.0 / (c + rank)
    return sorted(score.items(), key=lambda x: -x[1])[:k]


class HybridIndex:
    def __init__(self, bm25, dense: DenseIndex, depth: int = 50, c: int = 60) -> None:
        self.bm25, self.dense, self.depth, self.c = bm25, dense, depth, c

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        return rrf([self.bm25.search(query, self.depth), self.dense.search(query, self.depth)], k, self.c)


def usage_totals(model: str) -> dict:
    f = paths.INDEX / "embeddings" / model / "usage.jsonl"
    rows = [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []
    return {"tokens": sum(r["tokens"] for r in rows), "calls": len(rows), "inputs": sum(r["inputs"] for r in rows)}
