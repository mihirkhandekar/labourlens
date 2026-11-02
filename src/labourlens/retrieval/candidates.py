"""Candidate selection for the agent's search_reports tool (config r3 / r3w), before the rerank step: parse the period and release
hints of the planner query and of the original question, filter by them, fuse BM25 and dense rankings with RRF.

One function serves both routes so they cannot drift: the in-process tool (agent.tools.Tools) and the MCP server's `search_reports`
tool (mcp.server). The only difference is where the dense ranking comes from: `dense_search(depth)` embeds the query and ranks (in
process) or ranks an already embedded query vector (server). Nothing here calls a model.
"""

from __future__ import annotations

from collections.abc import Callable

from labourlens.retrieval import dense, period

POOL = 30  # candidates the rerank step sees; equals retrieval.rerank.POOL (checked by a test), repeated so the server need not import the LLM client


def select(retr, chunks: dict, query: str, question: str, retrieval: str, dense_search: Callable[[int], list]) -> tuple[list, dict]:
    """Returns (ranked [(chunk_id, rrf_score)], trace). Quarters are unioned; conflicting stages disable the stage restriction.
    r3w widens when fewer than 8 fused chunks survive or the best filtered BM25 score is below 0.5 times the unfiltered best positive
    BM25 score (fixed thresholds, not tuned on dev cases)."""
    a, b = period.parse(query), period.parse(question)
    stages = {h.stage for h in (a, b) if h.stage}
    conflict = a.stage_conflict or b.stage_conflict or len(stages) > 1
    hints = period.Hints(a.quarters | b.quarters, next(iter(stages)) if stages and not conflict else None, conflict)
    allowed = period.matching_sources(hints)
    n = len(chunks)
    bm = retr.bm25.search(query, n if allowed else retr.depth)
    de = dense_search(n if allowed else retr.depth)
    filtered_bm = [x for x in bm if chunks[x[0]].source_id in allowed] if allowed else bm
    filtered_de = [x for x in de if chunks[x[0]].source_id in allowed] if allowed else de
    ranked = dense.rrf([filtered_bm[:retr.depth], filtered_de[:retr.depth]], n, retr.c)
    trace = {"retrieval": retrieval,
             "hints": {"quarters": [f"{y}-Q{q}" for y, q in sorted(hints.quarters)], "stage": hints.stage, "stage_conflict": conflict},
             "filter_applied": allowed is not None,
             "filtered_documents": len({chunks[cid].source_id for cid, _ in filtered_bm + filtered_de}),
             "filtered_chunks": len(ranked), "widened": False}
    if retrieval == "r3w" and allowed and (
        len(ranked) < 8 or (bm and bm[0][1] > 0 and (not filtered_bm or filtered_bm[0][1] < 0.5 * bm[0][1]))
    ):
        # Search BM25 at its original depth: tied scores can depend on requested k.
        ranked = dense.rrf([retr.bm25.search(query, retr.depth), de[:retr.depth]], n, retr.c)
        trace["widened"] = True
    return ranked, trace
