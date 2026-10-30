"""Persisted BM25 index (D-012). The directory name carries the corpus hash and configuration hash; loading
checks the corpus hash against the current chunks and raises StaleIndexError on mismatch instead of silently
serving old text.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import bm25s

from labourlens import paths
from labourlens.retrieval.chunk import Chunk, corpus_hash
from labourlens.retrieval.tokenize import TokConfig, tokenize


class StaleIndexError(RuntimeError):
    """The index was built from a different corpus than the chunks now on disk."""


@dataclass(frozen=True)
class BM25Config:
    k1: float = 1.5
    b: float = 0.75
    tok: TokConfig = TokConfig()

    def key(self) -> str:
        return f"k{self.k1}-b{self.b}-{self.tok.key()}"


class BM25Index:
    def __init__(self, retriever: bm25s.BM25, chunk_ids: list[str], cfg: BM25Config, corpus_hash_: str) -> None:
        self._r, self.chunk_ids, self.cfg, self.corpus_hash = retriever, chunk_ids, cfg, corpus_hash_

    @classmethod
    def build(cls, chunks: list[Chunk], cfg: BM25Config) -> "BM25Index":
        toks = [tokenize(c.text, cfg.tok) for c in chunks]
        r = bm25s.BM25(k1=cfg.k1, b=cfg.b, method="lucene")
        r.index(toks, show_progress=False)
        return cls(r, [c.chunk_id for c in chunks], cfg, corpus_hash(chunks))

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        q = tokenize(query, self.cfg.tok)
        if not q:
            return []
        k = min(k, len(self.chunk_ids))
        ids, scores = self._r.retrieve([q], k=k, show_progress=False)
        return [(self.chunk_ids[int(i)], float(s)) for i, s in zip(ids[0], scores[0]) if s > 0]

    def dir_name(self, chunk_config: str) -> str:
        h = hashlib.sha256(json.dumps({"c": asdict(self.cfg)}, sort_keys=True, default=str).encode()).hexdigest()[:8]
        return f"{chunk_config}-{self.corpus_hash[:12]}-{h}"

    def save(self, chunk_config: str) -> Path:
        d = paths.INDEX / "bm25" / self.dir_name(chunk_config)
        d.mkdir(parents=True, exist_ok=True)
        self._r.save(str(d), show_progress=False)
        (d / "meta.json").write_text(json.dumps({
            "corpus_hash": self.corpus_hash, "chunk_ids": self.chunk_ids, "bm25_config": asdict(self.cfg),
            "bm25s_version": bm25s.__version__}, indent=1, default=str))
        return d

    @classmethod
    def load(cls, d: Path, chunks: list[Chunk]) -> "BM25Index":
        meta = json.loads((d / "meta.json").read_text())
        now = corpus_hash(chunks)
        if meta["corpus_hash"] != now:
            raise StaleIndexError(f"index {d.name} built from corpus {meta['corpus_hash'][:12]}, current corpus is {now[:12]}; rebuild")
        c = meta["bm25_config"]
        cfg = BM25Config(c["k1"], c["b"], TokConfig(**c["tok"]))
        return cls(bm25s.BM25.load(str(d), load_corpus=False), meta["chunk_ids"], cfg, now)


def reference_scores(docs: list[list[str]], query: list[str], k1: float, b: float) -> list[float]:
    """Plain BM25 for the correctness check against bm25s. Not used in retrieval.

Uses the Lucene form that bm25s implements: idf = ln(1 + (N-df+0.5)/(df+0.5)) and tf/(tf + k1*(1-b+b*dl/avgdl)).
The textbook Okapi form multiplies the tf term by (k1+1); that is a constant factor, so it changes scores but
not the ranking. The correctness test found this difference (see docs/decisions.md D-018 notes).
"""
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / n
    df = Counter(t for d in docs for t in set(d))
    out = []
    for d in docs:
        tf = Counter(d)
        s = 0.0
        for t in query:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))
        out.append(s)
    return out
