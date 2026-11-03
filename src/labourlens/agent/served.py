"""The web and experiment entry point share orchestration and tool transport."""
from __future__ import annotations

import logging
import time

# How the agent's tools reach their data (D-066):
#   direct     all three tools run in this process (the evaluated configuration of every frozen experiment);
#   mcp_stats  only get_series goes over MCP (D-053), to the plain `labourlens-stats` server;
#   mcp_all    get_series, search_reports and calculate_change (and calculate_from_text_values) go over MCP, to the same server
#              started with --agent-tools. The live app default.
TRANSPORTS = ("direct", "mcp_stats", "mcp_all")
DEFAULT_TRANSPORT = "mcp_stats"
AGENT_SERVER = "labourlens-stats-agent"
MCP_ALL_ROUTED = frozenset({"search_reports", "calculate_change", "calculate_from_text_values"})


# What the web app ships (D-077, D-078): the 2020-Q1 to 2026-Q2 prompts, and the native function-calling planner. Every frozen experiment kept its own
# prompt files and the structured-output planner; nothing here changes AgentConfig() or make_runner() defaults, so those runs reproduce as before.
SHIPPED_PROMPTS = {"planner": "planner_v4", "answer": "answer_v6", "triage": "triage_v2", "contextualise": "contextualise_v2"}


def shipped_config(run_deadline_s: float | None = 80.0):
    """The AgentConfig of the served app. Same models, retrieval (r3), bounds and tools as the evaluated agent; different planner mode and prompts."""
    from labourlens.agent.graph import AgentConfig

    return AgentConfig(planner_prompt=SHIPPED_PROMPTS["planner"], answer_prompt=SHIPPED_PROMPTS["answer"], planner_mode="tools", run_deadline_s=run_deadline_s)


def make_shared(transport: str = DEFAULT_TRANSPORT):
    """Shared read-only state for one process. `transport` is one of TRANSPORTS.

    mcp_all does not load the report corpus here: the MCP server holds the passages, the index and the vectors, so this process keeps the
    observations table (the planner schema and unknown-dimension help read it), the API key and the query embedding. A server that is not
    reachable at startup is logged and retried by the first tool call; it never switches the agent to the in-process tools."""
    from labourlens.agent.tools import Shared

    if transport not in TRANSPORTS:
        raise ValueError(f"transport must be one of {TRANSPORTS}")
    if transport == "direct":
        return Shared()
    from labourlens.mcp.client import SyncStatsBackend

    all_tools = transport == "mcp_all"
    sh = Shared(world=(None, {}, {})) if all_tools else Shared()
    sh.tool_transport = transport
    sh.stats_backend = backend = SyncStatsBackend(AGENT_SERVER if all_tools else "labourlens-stats")
    if all_tools:
        sh.mcp_routed = MCP_ALL_ROUTED
        sh.corpus = None  # the server owns the corpus; filled in below once it answers
    try:
        backend._run(backend._connect(), backend.connect_timeout_s + 10)  # query reconnects once; persistent faults become tool failures
        if all_tools:
            sh.corpus = backend.call_tool("describe_corpus").result.corpus.model_dump()
    except Exception as e:
        logging.getLogger(__name__).warning("MCP server not reachable at startup: %s", type(e).__name__)
    return sh


def make_runner(config=None, *, contextualise_enabled=True, triage_enabled=True, web_steps=True,
                save_trace=True, observer=None, triage_prompt=None, contextualise_prompt=None):
    """Preserve the web's small-talk-first order; optional observer records step usage, never changes routing.

    The returned runner takes an optional `emit(event: dict)` that receives live progress events (the web stream); it only observes.
    `triage_prompt` / `contextualise_prompt` override the prompt file names (None keeps the frozen defaults of those modules)."""
    from labourlens.agent.graph import AgentConfig, run_agent
    from labourlens.agent.smalltalk import run_smalltalk
    from labourlens.agent.triage import classify, run_with_triage
    from labourlens.agent.contextualise import attach, audit_block, contextualise, passthrough

    cfg = config or AgentConfig(run_deadline_s=80.0)

    def note(step, seconds, usage=None, **extra):
        if observer is not None:
            observer(step, {"seconds": seconds, "cost_usd": (usage or {}).get("cost_usd", 0.0), **extra})

    def runner(question, shared, audit=None, history=None, emit=None):
        def tell(event):
            if emit is not None:
                try:
                    emit(event)
                except Exception:  # noqa: BLE001 - an observer never changes a run
                    pass

        if web_steps:
            start = time.perf_counter()
            quick = run_smalltalk(question, shared, audit, save_trace=save_trace)
            note("smalltalk", time.perf_counter() - start, diverted=quick is not None)
            if quick is not None:
                return quick
        start = time.perf_counter()
        if web_steps and contextualise_enabled:
            tell({"type": "stage", "stage": "contextualise", "state": "running"})
            info = contextualise(question, history, **({"prompt": contextualise_prompt} if contextualise_prompt else {}))
        else:
            info = passthrough(question)
        if web_steps and contextualise_enabled:
            note("contextualise", time.perf_counter() - start, info["usage"], called=info["called"], error=info["error"], changed=info["changed"])
            tell({"type": "stage", "stage": "contextualise", "state": "done", "changed": bool(info["changed"])})
        q = info["question"]
        if info["called"] and audit is not None:
            audit = {**audit, "extra": {**(audit.get("extra") or {}), "contextualise": audit_block(info)}}

        def agent(a):
            start = time.perf_counter()
            res = run_agent(q, shared, cfg, save_trace=save_trace, audit=a, **({"on_event": emit} if emit is not None else {}))
            note("agent", time.perf_counter() - start, res.get("usage"))
            return res

        def classifier(message):
            start = time.perf_counter()
            tell({"type": "stage", "stage": "triage", "state": "running"})
            result = classify(message, **({"prompt": triage_prompt} if triage_prompt else {}))
            tell({"type": "stage", "stage": "triage", "state": "done", "route": result["route"]})
            note("triage", time.perf_counter() - start, result["usage"], route=result["route"], error=result["error"], diverted=result["route"] != "in_scope")
            return result

        if web_steps and triage_enabled:
            res = run_with_triage(q, shared, audit, agent, save_trace=save_trace, classifier=classifier)
        else:
            res = agent(audit)
        return attach(res, info)

    return runner
