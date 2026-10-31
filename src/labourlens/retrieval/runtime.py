"""Shared retrieval runtime for the answer pipeline, the agent and the MCP server: hybrid RRF over merge200 chunks with
text-embedding-3-large (candidate default from M3 dev experiments, not frozen)."""

from __future__ import annotations

import hashlib
import os

from labourlens.retrieval import chunk as ck
from labourlens.retrieval import dense as dn
from labourlens.retrieval.bm25_index import BM25Config, BM25Index

CHUNK_CONFIG = "merge200"
EMBEDDING_MODEL = "text-embedding-3-large"


def corpus_fingerprint(passages_by_id: dict, chunks_by_id: dict) -> dict:
    """Identifies the corpus a process serves. Passage ids embed a content hash, so any change to the passage set changes it."""
    digest = hashlib.sha256()
    for pid in sorted(passages_by_id):
        digest.update(str(pid).encode())
        digest.update(b"\n")
    return {"passage_set_sha256": digest.hexdigest()[:12], "passages": len(passages_by_id), "chunks": len(chunks_by_id)}


def embedding_allowed() -> bool:
    """LABOURLENS_ALLOW_EMBED=0 (the container default) forbids embedding chunks at startup."""
    return os.environ.get("LABOURLENS_ALLOW_EMBED", "1") != "0"


def require_complete_cache(chunks) -> None:
    """Fail fast when a chunk has no cached vector and startup embedding is forbidden."""
    cfg = dn.DenseConfig(EMBEDDING_MODEL)
    cache = dn.VectorCache(EMBEDDING_MODEL)
    missing = sum(1 for c in chunks if cache.get(dn._h(cfg.model, dn.embed_text(c, cfg.header))) is None)
    if missing:
        raise dn.EmbeddingError(
            f"embedding cache incomplete: {missing} of {len(chunks)} chunks have no cached vector, and LABOURLENS_ALLOW_EMBED=0 "
            "forbids calling the embeddings API at startup. Upload data/index/embeddings/*/cache.npz (deploy/runtime-data.txt).")


def load_world():
    """Returns (retriever, chunks_by_id, passages_by_id)."""
    passages = ck.load_passages()
    chunks = ck.build_chunks(ck.CONFIGS[CHUNK_CONFIG], passages)
    if not embedding_allowed():
        require_complete_cache(chunks)
    retr = dn.HybridIndex(BM25Index.build(chunks, BM25Config()), dn.DenseIndex(chunks, dn.DenseConfig(EMBEDDING_MODEL)))
    return retr, {c.chunk_id: c for c in chunks}, {p["passage_id"]: p for p in passages}
