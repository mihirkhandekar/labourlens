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
    """Identifies the corpus a process serves.

    `passage_set_sha256` hashes the sorted passage ids; ids embed a text hash, so it changes when passage text changes but NOT when only
    a quality flag or the chunk text changes. `content_sha256` additionally covers each passage's quality flag and each chunk's id and
    text hash, so a re-flag (corpus v3.1) is visible in /healthz.
    """
    digest = hashlib.sha256()
    for pid in sorted(passages_by_id):
        digest.update(str(pid).encode())
        digest.update(b"\n")
    content = hashlib.sha256()
    for pid in sorted(passages_by_id):
        p = passages_by_id[pid]
        content.update(f"p|{pid}|{p.get('quality_flag', '') if isinstance(p, dict) else ''}\n".encode())
    for cid in sorted(chunks_by_id):
        content.update(f"c|{cid}|{getattr(chunks_by_id[cid], 'text_sha256', '')}\n".encode())
    return {"passage_set_sha256": digest.hexdigest()[:12], "content_sha256": content.hexdigest()[:12],
            "passages": len(passages_by_id), "chunks": len(chunks_by_id)}


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


def load_search_world():
    """For the MCP server: (retriever, chunks_by_id, passages_by_id, corpus fingerprint). Unlike load_world it never embeds anything,
    whatever LABOURLENS_ALLOW_EMBED says (the server has no API key and must not need one): a chunk without a cached vector is an error.
    Only passages a chunk cites are kept (the answer path never reads the others); the fingerprint is taken over all of them first, so it
    equals the one load_world's callers compute."""
    passages = ck.load_passages()
    chunks = ck.build_chunks(ck.CONFIGS[CHUNK_CONFIG], passages)
    chunks_by_id = {c.chunk_id: c for c in chunks}
    corpus = corpus_fingerprint({p["passage_id"]: p for p in passages}, chunks_by_id)
    cited = {pid for c in chunks for pid in c.source_passage_ids}
    passages_by_id = {p["passage_id"]: p for p in passages if p["passage_id"] in cited}
    del passages
    retr = dn.HybridIndex(BM25Index.build(chunks, BM25Config()), dn.DenseIndex.from_cache(chunks, dn.DenseConfig(EMBEDDING_MODEL)))
    return retr, chunks_by_id, passages_by_id, corpus
