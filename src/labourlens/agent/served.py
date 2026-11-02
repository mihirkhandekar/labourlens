"""The web and experiment entry point share orchestration and statistics transport."""
from __future__ import annotations

import logging
import time


def make_shared(mcp_enabled=True):
    from labourlens.agent.tools import Shared

    sh = Shared()
    if mcp_enabled:
        from labourlens.mcp.client import SyncStatsBackend

        sh.stats_backend = backend = SyncStatsBackend()
        try:
            backend._run(backend._connect(), 30)
        except Exception as e:  # query reconnects once; persistent faults become tool failures
            logging.getLogger(__name__).warning("MCP statistics server not reachable at startup: %s", type(e).__name__)
    return sh


def make_runner(config=None, *, contextualise_enabled=True, triage_enabled=True, web_steps=True,
                save_trace=True, observer=None):
    """Preserve the web's small-talk-first order; optional observer records step usage, never changes routing."""
    from labourlens.agent.graph import AgentConfig, run_agent
    from labourlens.agent.smalltalk import run_smalltalk
    from labourlens.agent.triage import classify, run_with_triage
    from labourlens.agent.contextualise import attach, audit_block, contextualise, passthrough

    cfg = config or AgentConfig(run_deadline_s=80.0)

    def note(step, seconds, usage=None, **extra):
        if observer is not None:
            observer(step, {"seconds": seconds, "cost_usd": (usage or {}).get("cost_usd", 0.0), **extra})

    def runner(question, shared, audit=None, history=None):
        if web_steps:
            start = time.perf_counter()
            quick = run_smalltalk(question, shared, audit, save_trace=save_trace)
            note("smalltalk", time.perf_counter() - start, diverted=quick is not None)
            if quick is not None:
                return quick
        start = time.perf_counter()
        info = contextualise(question, history) if web_steps and contextualise_enabled else passthrough(question)
        if web_steps and contextualise_enabled:
            note("contextualise", time.perf_counter() - start, info["usage"], called=info["called"], error=info["error"], changed=info["changed"])
        q = info["question"]
        if info["called"] and audit is not None:
            audit = {**audit, "extra": {**(audit.get("extra") or {}), "contextualise": audit_block(info)}}

        def agent(a):
            start = time.perf_counter()
            res = run_agent(q, shared, cfg, save_trace=save_trace, audit=a)
            note("agent", time.perf_counter() - start, res.get("usage"))
            return res

        def classifier(message):
            start = time.perf_counter()
            result = classify(message)
            note("triage", time.perf_counter() - start, result["usage"], route=result["route"], error=result["error"], diverted=result["route"] != "in_scope")
            return result

        if web_steps and triage_enabled:
            res = run_with_triage(q, shared, audit, agent, save_trace=save_trace, classifier=classifier)
        else:
            res = agent(audit)
        return attach(res, info)

    return runner
