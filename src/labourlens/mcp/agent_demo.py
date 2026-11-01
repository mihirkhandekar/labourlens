"""One recorded agent run whose statistics lookups go through the MCP client (demo scenario 8).

The live web app does the same since D-053 (`Settings.mcp_enabled`). This script plugs `SyncStatsBackend` into `Shared.stats_backend`, so the
agent's `get_series` tool is an MCP `get_statistic` call to the stdio server, then writes `artifacts/mcp-agent-demo.md`.
It makes paid model calls (a few thousand tokens). The record holds the question, the MCP calls, the structured answer and a
deterministic comparison with the direct lookup. It is one question, one run: a demonstration, not an evaluation.
Only dataset rows and the model's own answer are written; no passage text.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from labourlens import paths

QUESTION = "How did the number of retrenched employees change from 2025-Q4 to 2026-Q1?"
OUT = paths.ROOT / "artifacts" / "mcp-agent-demo.md"


def run(question: str = QUESTION) -> int:
    from dotenv import load_dotenv

    load_dotenv(paths.ROOT / ".env", override=False)
    from labourlens.agent.graph import AgentConfig, run_agent
    from labourlens.agent.tools import Shared
    from labourlens.mcp.client import SyncStatsBackend

    cfg = AgentConfig()
    shared = Shared(retrieval=cfg.retrieval)
    backend = SyncStatsBackend()
    shared.stats_backend = backend
    calls: list[dict] = []
    original = backend.query

    def recording_query(*args, **kwargs):  # keeps the arguments next to the timing the backend already records
        keys = ("source_id", "period_from", "period_to", "dimension", "adjustment", "indicator_id")
        calls.append({**dict(zip(keys, args)), **kwargs})
        return original(*args, **kwargs)

    backend.query = recording_query
    try:
        res = run_agent(question, shared, cfg, save_trace=False)
    finally:
        backend.close()
    for call, timing in zip(calls, backend.calls):
        call.update(timing)
    OUT.write_text(render(question, cfg, res, calls, shared))
    print(f"wrote {OUT.relative_to(paths.ROOT)}")
    return 0


def _direct_check(shared, calls: list[dict]) -> list[tuple[str, str, str, bool]]:
    """Re-run each successful MCP query against the local table (no model, no MCP) and compare the rows."""
    rows = []
    for c in calls:
        if not c.get("ok"):
            continue
        direct, err = shared.stats.query(c["source_id"], c["period_from"], c["period_to"], c.get("dimension"), c.get("adjustment"), c.get("indicator_id"))
        if err is not None:
            rows.append((c["source_id"], "-", f"direct lookup refused: {err.message}", False))
            continue
        for r in direct:
            rows.append((c["source_id"], r["period"], r["display"], True))
    return rows


def render(question: str, cfg, res: dict, calls: list[dict], shared) -> str:
    answer = res.get("answer") or {}
    texts = " ".join([answer.get("summary", "")] + [cl.get("text", "") for cl in answer.get("claims", [])])
    direct = _direct_check(shared, calls)
    numbers_in_answer = {n.replace(",", "") for n in re.findall(r"\d[\d,]*\.?\d*", texts)}
    confirmed = [d for d in direct if re.sub(r"[^\d.]", "", d[2].split()[0]) in numbers_in_answer]
    mcp_nodes = [e["node"] for e in res["trace"]]
    L = ["# MCP-backed agent answer (demo scenario 8)", "",
         f"Recorded {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `uv run labourlens mcp-agent-demo`. "
         "One question, one run: a demonstration that the agent can use the statistics server over MCP, not an evaluation. "
         "The live web app routes `get_series` the same way; the accuracy evaluations called the tools directly.", "",
         "## Setup", "",
         f"- Question: {question}",
         f"- Models: planner `{cfg.planner_model}`, answer `{cfg.answer_model}`; prompts `{cfg.planner_prompt}` and `{cfg.answer_prompt}`; retrieval `{cfg.retrieval}`.",
         "- Statistics backend: `SyncStatsBackend` over stdio to `labourlens.mcp.server` (allow-listed server `labourlens-stats`, name, version and tool list verified at connect).",
         "- Everything else (retrieval, planner, answer, validator) is the normal agent path.", "",
         "## MCP calls made by the agent", "",
         "| # | tool | source | period | dimension | ok | ms | quarantined rows |", "|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(calls, 1):
        L.append(f"| {i} | get_statistic | `{c['source_id']}` | {c['period_from']} to {c['period_to']} | {c.get('dimension') or 'all'} | {c.get('ok')} | {c.get('ms')} | {c.get('quarantined', '-')} |")
    if not calls:
        L.append("| - | none | | | | | | |")
    L += ["", "## Agent result", "",
          f"- Outcome: `{res['outcome']}`; {res['rounds']} planning round(s), {res['tool_calls']} tool call(s); {res['seconds']} s; {res['usage']['calls']} model calls; cost ${res['usage']['cost_usd']}.",
          f"- Graph nodes visited: {' -> '.join(dict.fromkeys(mcp_nodes))}.", "", "Structured answer as returned:", "", "```json",
          json.dumps(answer, indent=2, ensure_ascii=False), "```", "",
          "## Deterministic check against the direct lookup", "",
          "Each successful MCP query was repeated against the local observations table with no model and no MCP, and the figures compared with the answer text.", "",
          "| source | period | value (direct) | appears in the answer |", "|---|---|---|---|"]
    for src, per, disp, ok in direct:
        L.append(f"| `{src}` | {per} | {disp} | {'yes' if (src, per, disp, ok) in confirmed else 'no'} |")
    L += ["", f"Evidence items the agent held: {', '.join(e['label'] + '=' + e['source_id'] for e in res['evidence']) or 'none'}. "
          f"Cited labels: {', '.join(res.get('cited_ids') or []) or 'none'}.", "",
          "## Limits", "",
          "- One question and one run; no claim about reliability or about MCP versus direct accuracy. The paired direct-versus-MCP latency comparison is section 17 of `docs/mcp-demo-transcript.md`.",
          "- The agent uses the MCP path for `get_series` only; the other eight server tools are not wired into the agent.",
          "- Model output is not deterministic; a rerun can word the answer differently."]
    return "\n".join(L) + "\n"
