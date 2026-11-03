"""Embed the chunks of the current corpus that have no cached vector (D-080). The only paid step after adding documents.

`labourlens embed-corpus` prints what is missing and a token estimate and spends nothing. `--yes` calls the embeddings API for exactly the
missing chunks (the cache is keyed by model and text, so existing vectors are never recomputed) and writes data/index/embeddings/<model>/cache.npz.
Needs OPENAI_API_KEY; ship the updated cache.npz as deploy/runtime-data.txt describes."""

from __future__ import annotations

from labourlens.retrieval import chunk as ck
from labourlens.retrieval import dense as dn
from labourlens.retrieval.runtime import CHUNK_CONFIG, EMBEDDING_MODEL

PRICE_PER_MILLION_TOKENS_USD = 0.13  # text-embedding-3-large list price; an estimate printed for the owner, not a measurement


def missing_chunks() -> tuple[list[ck.Chunk], int]:
    chunks = ck.build_chunks(ck.CONFIGS[CHUNK_CONFIG], ck.load_passages())
    cfg, cache = dn.DenseConfig(EMBEDDING_MODEL), dn.VectorCache(EMBEDDING_MODEL)
    missing = {dn._h(cfg.model, dn.embed_text(c, cfg.header)): c for c in chunks if cache.get(dn._h(cfg.model, dn.embed_text(c, cfg.header))) is None}
    return list(missing.values()), len(chunks)


def run(execute: bool = False) -> dict:
    todo, total = missing_chunks()
    cfg = dn.DenseConfig(EMBEDDING_MODEL)
    chars = sum(len(dn.embed_text(c, cfg.header)) for c in todo)
    tokens = chars // 4  # rough: four characters per token
    report = {"model": EMBEDDING_MODEL, "chunks_total": total, "chunks_without_vector": len(todo), "estimated_tokens": tokens,
              "estimated_cost_usd": round(tokens / 1e6 * PRICE_PER_MILLION_TOKENS_USD, 4), "executed": False}
    if execute and todo:
        dn.embed(cfg.model, [dn.embed_text(c, cfg.header) for c in todo], purpose="corpus-2020-2022")
        report["executed"] = True
        report["chunks_without_vector_after"] = len(missing_chunks()[0])
    return report
