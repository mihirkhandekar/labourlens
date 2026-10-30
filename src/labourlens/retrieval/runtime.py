"""Shared retrieval runtime for the answer pipeline, the agent and the MCP server: hybrid RRF over merge200 chunks with
text-embedding-3-large (candidate default from M3 dev experiments, not frozen)."""

from __future__ import annotations

from labourlens.retrieval import chunk as ck
from labourlens.retrieval import dense as dn
from labourlens.retrieval.bm25_index import BM25Config, BM25Index

CHUNK_CONFIG = "merge200"
EMBEDDING_MODEL = "text-embedding-3-large"


def load_world():
    """Returns (retriever, chunks_by_id, passages_by_id)."""
    passages = ck.load_passages()
    chunks = ck.build_chunks(ck.CONFIGS[CHUNK_CONFIG], passages)
    retr = dn.HybridIndex(BM25Index.build(chunks, BM25Config()), dn.DenseIndex(chunks, dn.DenseConfig(EMBEDDING_MODEL)))
    return retr, {c.chunk_id: c for c in chunks}, {p["passage_id"]: p for p in passages}
