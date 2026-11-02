"""Pure logic behind the MCP tools the live agent uses besides `get_statistic` (server started with `--agent-tools`): report search,
the two exact calculations and the corpus identity. No MCP types here, so tests compare each function with the in-process tool.

Trust and secrets
- No API key and no network. The server cannot embed anything: the caller embeds the query and sends the vector (base64 float32); the
  chunk vectors come from the on-disk cache only (retrieval.runtime.load_search_world). Reranking calls a model, so it stays in the caller.
- Read-only: the passages, the BM25 index and the matrix are loaded once and never written.
- Report text leaves this process only inside search_reports results, which are marked untrusted; the client sanitises and scans them.
- The calculations take ids, not numbers: calculate_change recomputes from the server's own observations table, and
  calculate_from_text_values checks every figure against the passage text this server holds before computing.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np

from labourlens.agent.tools import StatsData, TextChange, ToolResult, observation_change, text_change
from labourlens.mcp.analysis import AnalysisError
from labourlens.mcp.models import (EMBEDDING_DIMENSION, MAX_K, MAX_QUERY_CHARS, CalculateChangeResult, ChunkHit, CorpusInfo, DescribeCorpusResult,
                                   PassageHit, SearchHints, SearchReportsResult, SearchTrace, TextChangeResult)
from labourlens.retrieval import candidates
from labourlens.retrieval.runtime import CHUNK_CONFIG, EMBEDDING_MODEL, load_search_world
from labourlens.security.guards import injection_flags, sanitize_text


@dataclass
class World:
    retriever: object
    chunks: dict
    passages: dict
    corpus: dict

    @property
    def dimension(self) -> int:
        return int(self.retriever.dense.matrix.shape[1])


def load() -> World:
    retriever, chunks, passages, corpus = load_search_world()
    w = World(retriever, chunks, passages, corpus)
    if w.dimension != EMBEDDING_DIMENSION:
        raise RuntimeError(f"embedding matrix has {w.dimension} columns, expected {EMBEDDING_DIMENSION}")
    return w


def _fail(res: ToolResult):
    raise AnalysisError(res.error_kind or "invalid_arguments", res.message)


def decode_vector(b64: str) -> np.ndarray:
    """The query vector: exactly EMBEDDING_DIMENSION finite float32 values with an L2 norm of 1 (as retrieval.dense.embed returns them)."""
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise AnalysisError("invalid_arguments", "query_vector_b64 is not valid base64") from None
    if len(raw) != EMBEDDING_DIMENSION * 4:
        raise AnalysisError("invalid_arguments", f"query_vector_b64 must hold {EMBEDDING_DIMENSION} float32 values")
    vec = np.frombuffer(raw, dtype="<f4").astype(np.float32)
    if not np.isfinite(vec).all() or abs(float(np.linalg.norm(vec)) - 1.0) > 1e-3:
        raise AnalysisError("invalid_arguments", "query vector must be finite and L2-normalised")
    return vec


def search_reports(w: World, query: str, question: str, retrieval: str, k: int, query_vector_b64: str) -> SearchReportsResult:
    q = (query or "").strip()
    if not q or len(q) > MAX_QUERY_CHARS:
        raise AnalysisError("invalid_arguments", f"query must be 1 to {MAX_QUERY_CHARS} characters")
    if retrieval not in ("hybrid", "r3", "r3w"):
        raise AnalysisError("invalid_arguments", "retrieval must be hybrid, r3 or r3w")
    if not isinstance(k, int) or not 1 <= k <= MAX_K:
        raise AnalysisError("invalid_arguments", f"k must be an integer from 1 to {MAX_K}")
    vec = decode_vector(query_vector_b64)
    retr = w.retriever
    if retrieval == "hybrid":
        ranked, trace = retr.search_vector(q, vec, k), None
    else:
        ranked, trace = candidates.select(retr, w.chunks, q, question or "", retrieval, lambda depth: retr.dense.search_vector(vec, depth))
        ranked = ranked[:max(candidates.POOL, k)]  # the rerank pool; the caller reranks it and keeps the best k
    hits, seen, passages = [], set(), []
    for cid, score in ranked:
        c = w.chunks[cid]
        derivable = all(pid in w.passages for pid in c.source_passage_ids) and c.text == "\n".join(w.passages[pid]["text"] for pid in c.source_passage_ids)
        hits.append(ChunkHit(chunk_id=cid, score=score, source_id=c.source_id, document_title=c.document_title, publication_date=c.publication_date,
                             release_stage=c.release_stage, locator=c.locator, text=None if derivable else c.text, source_passage_ids=list(c.source_passage_ids)))
        for pid in c.source_passage_ids:
            p = w.passages.get(pid)
            if p and pid not in seen:
                seen.add(pid)
                passages.append(PassageHit(passage_id=pid, source_id=p["source_id"], document_title=p["document_title"], publication_date=p["publication_date"],
                                           release_stage=p["release_stage"], locator=p["locator"], text=p["text"]))
    shown = None if trace is None else SearchTrace(
        retrieval=trace["retrieval"], hints=SearchHints(**trace["hints"]), filter_applied=trace["filter_applied"],
        filtered_documents=trace["filtered_documents"], filtered_chunks=trace["filtered_chunks"], widened=trace["widened"])
    return SearchReportsResult(retrieval=retrieval, trace=shown, chunks=hits, passages=passages)


def calculate_change(stats: StatsData, observation_id_a: str, observation_id_b: str, kind: str) -> CalculateChangeResult:
    rows = []
    for oid in (observation_id_a, observation_id_b):
        g = stats.obs[stats.obs.observation_id == oid]
        if g.empty:
            raise AnalysisError("not_found", f"unknown observation_id {oid!r}")
        r = next(g.itertuples())
        rows.append({"id": oid, "source_id": r.source_id, "indicator_id": r.indicator_id, "population": r.population, "adjustment": r.adjustment,
                     "dimension": r.dimension, "unit": r.unit, "period": r.period, "value": None if r.value != r.value else float(r.value)})
    a, b = rows
    out = observation_change(a, b, kind)
    if isinstance(out, ToolResult):
        _fail(out)
    _, shown, unit, formula = out
    return CalculateChangeResult(kind=kind, observation_id_a=a["id"], observation_id_b=b["id"], indicator_id=a["indicator_id"], dimension=a["dimension"],
                                 population=a["population"], adjustment=a["adjustment"], series_unit=a["unit"], period_a=a["period"], period_b=b["period"],
                                 value_a=a["value"], value_b=b["value"], value=shown, unit=unit, formula=formula)


def calculate_from_text_values(w: World, passage_a: str, passage_id_a: str | None, value_a: str, unit_a: str, basis_a: str, period_a: str,
                               passage_b: str, passage_id_b: str | None, value_b: str, unit_b: str, basis_b: str, period_b: str,
                               kind: str) -> TextChangeResult:
    ids = {"a": passage_id_a, "b": passage_id_b}

    def resolve(side: str, label: str):
        pid = ids[side]
        p = w.passages.get(pid) if pid else None
        if p is None:
            return None
        text = sanitize_text(p["text"])
        return SimpleNamespace(text=text, flags=tuple(injection_flags(text)), label=label, passage_id=pid, source_id=p["source_id"],
                               stage=p["release_stage"], title=p["document_title"])

    out = text_change(resolve, passage_a, value_a, unit_a, basis_a, period_a, passage_b, value_b, unit_b, basis_b, period_b, kind)
    if isinstance(out, ToolResult):
        _fail(out)
    assert isinstance(out, TextChange)
    return TextChangeResult(kind=kind, passage_id_a=out.ia.passage_id, passage_id_b=out.ib.passage_id, value_a=str(out.va), value_b=str(out.vb),
                            unit_in=out.unit_in, basis=out.basis, period_a=out.period_a, period_b=out.period_b, value=out.shown, unit=out.unit, formula=out.formula)


def describe_corpus(w: World) -> DescribeCorpusResult:
    return DescribeCorpusResult(corpus=CorpusInfo(**w.corpus), chunk_config=CHUNK_CONFIG, embedding_model=EMBEDDING_MODEL, embedding_dimension=w.dimension)
