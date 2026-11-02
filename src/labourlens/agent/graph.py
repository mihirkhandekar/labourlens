"""Bounded LangGraph research agent (ADR-002): validate_question -> plan_research -> execute_tool -> assess_evidence ->
generate_answer -> validate_answer -> finalize.

Bounds (initial defaults, measured later): at most 2 evidence-gathering rounds, 6 tool calls (3 per round), one retry for a
transient tool failure, one repair of an invalid answer, 10 s per tool call. The planner sees evidence labels and sources,
never passage text (least exposure to injected text). Evidence content lives in the per-run Tools registry; graph state
holds counters, decisions and the activity trace, not documents (ADR-002 item 3). No hidden reasoning is stored: `note`
fields are short statements written for the activity log.
"""

from __future__ import annotations

import hashlib
import os
import json
import operator
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from labourlens import paths, prices
from labourlens.agent.tools import (TEXT_CALC_ARGS, TEXT_CALC_REQUIRED, TEXT_UNITS, TOOL_SETS, Shared, ToolResult, Tools, TransientToolError,
                                    figure_snippets, is_unknown_dimension)
from labourlens.answer import context as cx
from labourlens.answer import llm, validate
from labourlens.answer.pipeline import PROMPTS, _parse, load_prompt
from labourlens.mcp.redact import redact, secret_values
from labourlens.security.guards import injection_flags, scan_output

MAX_ROUNDS, MAX_CALLS, MAX_CALLS_PER_ROUND, TOOL_TIMEOUT_S, MAX_QUESTION_CHARS = 2, 6, 3, 10.0, 1000
# Tool set v2 (D-046): one extra evidence round is granted, once per run, after an unknown-dimension error, so the corrected retry
# does not consume the round a later calculation needs. The call budget (MAX_CALLS) is unchanged.
BONUS_ROUNDS = 1
V2_PROMPTS = ("planner_v3", "answer_v5")


@dataclass(frozen=True)
class AgentConfig:
    planner_model: str = "gpt-6-luna"
    answer_model: str = "gpt-6-luna"
    planner_prompt: str = "planner_v1"
    answer_prompt: str = "answer_v3"
    tool_timeout_s: float = TOOL_TIMEOUT_S
    retrieval: str = "r3"  # D-030: period/release filter then rerank; "hybrid" is the earlier default, kept for comparison
    # "base" is every earlier experiment, byte for byte. "v2" (D-046) adds calculate_from_text_values, an actionable unknown-dimension
    # error with one bonus round, and passage figure snippets in the planner's evidence list. It needs planner_v3 and answer_v5.
    tool_set: str = "base"
    # Total wall-clock budget for the planner and answer LLM calls of one run (None = unbounded, as in the evaluated runs).
    # The web app sets it so an abandoned run releases its slot; it is not part of key() and changes no model setting.
    run_deadline_s: float | None = None

    def __post_init__(self) -> None:
        if self.retrieval not in ("hybrid", "r3", "r3w"):
            raise ValueError("retrieval must be hybrid, r3 or r3w")
        if self.tool_set not in TOOL_SETS:
            raise ValueError(f"tool_set must be one of {TOOL_SETS}")
        if (self.tool_set == "v2") != (self.planner_prompt == V2_PROMPTS[0] and self.answer_prompt == V2_PROMPTS[1]):
            raise ValueError("tool_set v2 and the prompts planner_v3 + answer_v5 go together: use both or neither")

    def key(self) -> str:
        base = f"planner={self.planner_model}|answer={self.answer_model}|{self.planner_prompt}|{self.answer_prompt}"
        base = base if self.retrieval == 'hybrid' else f'{base}|retrieval={self.retrieval}'
        return base if self.tool_set == "base" else f"{base}|tools={self.tool_set}"


def _nullable(t: str) -> dict:
    return {"type": [t, "null"]}


def plan_schema(shared: Shared, tool_set: str = "base") -> dict:
    """Planner output schema. source_id, indicator_id, adjustment and kind are enums built from the catalogue, so the model
    cannot invent them (it did, and one model looped on a long made-up indicator_id until truncated). The tools still
    validate every argument; the enum is a convenience for the model, not the safety boundary."""
    def enum(vals):
        return {"type": ["string", "null"], "enum": sorted(vals) + [None]}

    from labourlens.agent.tools import ADJUSTMENTS, CHANGE_KINDS

    base = {
        "type": "object", "additionalProperties": False, "required": ["decision", "note", "calls"],
        "properties": {
            "decision": {"type": "string", "enum": ["gather", "finish"]},
            "note": {"type": "string"},
            "calls": {"type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "required": ["tool", "query", "k", "source_id", "period_from", "period_to", "dimension", "adjustment", "indicator_id", "obs_a", "obs_b", "kind"],
                "properties": {"tool": {"type": "string", "enum": ["search_reports", "get_series", "calculate_change"]},
                               "query": _nullable("string"), "k": _nullable("integer"), "source_id": enum(set(shared.obs.source_id)),
                               "period_from": _nullable("string"), "period_to": _nullable("string"), "dimension": _nullable("string"),
                               "adjustment": enum(ADJUSTMENTS), "indicator_id": enum(set(shared.obs.indicator_id)), "obs_a": _nullable("string"),
                               "obs_b": _nullable("string"), "kind": enum(CHANGE_KINDS)}}}}}
    if tool_set == "v2":
        item = base["properties"]["calls"]["items"]
        item["properties"]["tool"]["enum"].append("calculate_from_text_values")
        for side in "ab":
            item["properties"].update({f"passage_{side}": _nullable("string"), f"value_{side}": _nullable("string"), f"unit_{side}": enum(TEXT_UNITS),
                                       f"basis_{side}": _nullable("string"), f"period_{side}": _nullable("string")})
        item["required"] = item["required"] + [a for a in TEXT_CALC_ARGS if a != "kind"]
    return base


ARGS = {"search_reports": ("query", "k"), "get_series": ("source_id", "period_from", "period_to", "dimension", "adjustment", "indicator_id"),
        "calculate_change": ("obs_a", "obs_b", "kind"), "calculate_from_text_values": TEXT_CALC_ARGS}
REQUIRED = {"search_reports": ("query",), "get_series": ("source_id", "period_from", "period_to"), "calculate_change": ("obs_a", "obs_b"),
            "calculate_from_text_values": TEXT_CALC_REQUIRED}


class State(TypedDict, total=False):
    question: str
    round: int
    calls_used: int
    planned: list[dict]
    bonus_rounds: int
    tool_errors: list[str]
    tool_ops_failures: int
    messages: list[dict]
    attempts: int
    answer: dict | None
    errors: list[str]
    outcome: str
    usage: dict
    source_conflicts: list[dict]
    trace: Annotated[list[dict], operator.add]


def _ev(node: str, event: str, **detail) -> list[dict]:
    return [{"t": round(time.time(), 3), "node": node, "event": event, "detail": detail}]


def _usage(state: State, model: str, r: llm.LLMResult) -> dict:
    u = dict(state.get("usage") or {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0})
    u["calls"] += 1
    u["prompt_tokens"] += r.prompt_tokens
    u["completion_tokens"] += r.completion_tokens
    u["cost_usd"] = round(u["cost_usd"] + prices.chat_cost(model, r.prompt_tokens, r.completion_tokens), 6)
    u["llm_seconds"] = round(u["llm_seconds"] + r.seconds, 2)
    return u


def build_graph(shared: Shared, tools: Tools, cfg: AgentConfig):
    tools.retrieval, tools.tool_timeout_s, tools.tool_set = cfg.retrieval, cfg.tool_timeout_s, cfg.tool_set
    planner_sys, planner_user, _ = load_prompt(cfg.planner_prompt)
    planner_sys = planner_sys.format(catalogue=shared.catalogue_text())
    answer_sys, answer_user, _ = load_prompt(cfg.answer_prompt)
    pool = ThreadPoolExecutor(max_workers=2)
    schema = plan_schema(shared) if cfg.tool_set == "base" else plan_schema(shared, cfg.tool_set)
    clock = {"start": None}

    def llm_budget() -> float | None:
        """Seconds left for the next LLM call under cfg.run_deadline_s (never negative), or None when unbounded."""
        if cfg.run_deadline_s is None:
            return None
        if clock["start"] is None:
            clock["start"] = time.perf_counter()
        return max(0.0, cfg.run_deadline_s - (time.perf_counter() - clock["start"]))

    def deadline() -> dict:
        """chat() keyword for the remaining budget; empty when unbounded, so unbounded runs call chat exactly as the evaluated runs did."""
        left = llm_budget()
        return {} if left is None else {"timeout_s": left}

    def validate_question(s: State):
        q = (s.get("question") or "").strip()
        if not q or len(q) > MAX_QUESTION_CHARS:
            return {"outcome": "rejected_input", "errors": [f"question must be 1 to {MAX_QUESTION_CHARS} characters"],
                    "trace": _ev("validate_question", "rejected", length=len(q))}
        tools.question = q
        clock["start"] = time.perf_counter()
        return {"question": q, "trace": _ev("validate_question", "accepted", length=len(q), input_flags=injection_flags(q))}

    def after_validate(s: State):
        return "finalize" if s.get("outcome") == "rejected_input" else "plan_research"

    def evidence_summary() -> str:
        if not tools.items:
            return "(none yet)"
        lines = []
        for it in tools.items:
            # passages: label and source only (no text); statistics and calculations are our own computed lines
            lines.append(f"{it.label}: {it.text}" if it.label[0] in "OC" else f"{it.label}: passage from {it.source_id} ({it.stage}), {it.locator}")
            if cfg.tool_set == "v2" and it.label[0] == "P" and not it.flags:
                # Tool set v2: a few short word windows around the figures, so the planner can choose inputs for calculate_from_text_values.
                # Untrusted text; the tool re-checks every chosen value against the full passage. Flagged passages never get snippets.
                lines += [f'  figure: "{snippet}"' for snippet in figure_snippets(it.text)]
        return "\n".join(lines)

    def plan_research(s: State):
        rnd, used = s.get("round", 0), s.get("calls_used", 0)
        if rnd >= MAX_ROUNDS + s.get("bonus_rounds", 0) or used >= MAX_CALLS:
            return {"planned": [], "trace": _ev("plan_research", "budget_exhausted", round=rnd, calls_used=used)}
        user = planner_user.format(question=s["question"], round=rnd + 1, calls_used=used, evidence=evidence_summary(),
                                   errors="\n".join(s.get("tool_errors") or []) or "(none)")
        plan, r, last = None, None, ""
        for attempt in range(2):  # one retry for malformed planner output (ADR-002 item 6)
            try:
                r = llm.chat(cfg.planner_model, [{"role": "system", "content": planner_sys}, {"role": "user", "content": user}],
                             max_completion_tokens=1500, schema=schema, schema_name="plan", **deadline())
                plan = json.loads(r.content)
                if not isinstance(plan, dict) or not {"decision", "calls", "note"} <= plan.keys():
                    plan, last = None, "MalformedPlan"
                break
            except json.JSONDecodeError:
                last = "JSONDecodeError"
            except Exception as e:  # LLMError, or a provider/shape failure: operational, never an escaped exception
                last = type(e).__name__
                break
        if plan is None:
            return {"planned": [], "outcome": "operational_failure", "errors": [f"operational failure: planner: {last}"],
                    "trace": _ev("plan_research", "operational_failure", error=last)}
        calls = plan["calls"][: min(MAX_CALLS_PER_ROUND, MAX_CALLS - used)] if plan["decision"] == "gather" else []
        return {"planned": calls, "usage": _usage(s, cfg.planner_model, r), "tool_errors": [],
                "trace": _ev("plan_research", plan["decision"], round=rnd + 1, note=plan["note"][:200], n_calls=len(calls),
                             dropped=max(0, len(plan["calls"]) - len(calls)) if plan["decision"] == "gather" else 0)}

    def after_plan(s: State):
        if s.get("outcome") == "operational_failure":
            return "finalize"
        return "execute_tool" if s.get("planned") else "assess_evidence"

    def _run_one(call: dict) -> tuple[ToolResult | None, str | None]:
        name = call["tool"]
        if name == "calculate_from_text_values" and cfg.tool_set != "v2":
            return ToolResult(False, message="tool not available", error_kind="invalid_arguments"), None
        missing = [a for a in REQUIRED[name] if call.get(a) in (None, "")]
        if missing:
            return ToolResult(False, message=f"missing required argument(s): {missing}", error_kind="invalid_arguments"), None
        kwargs = {a: call[a] for a in ARGS[name] if call.get(a) is not None}
        from labourlens.retrieval.dense import embedding_deadline

        def invoke(child):
            with embedding_deadline(cfg.tool_timeout_s):
                result = getattr(child, name)(**kwargs)
            return result, child

        for attempt in range(2):  # retry only failures whose worker has finished
            fut = pool.submit(invoke, tools.fork())
            try:
                result, child = fut.result(timeout=cfg.tool_timeout_s)
                tools.commit(child)
                return result, None
            except FutureTimeout as e:
                fut.cancel()
                return None, f"{type(e).__name__}: tool {name} did not complete"
            except TransientToolError as e:
                if attempt == 1:
                    return None, f"{type(e).__name__}: tool {name} did not complete"
            except Exception as e:  # tool bug or unexpected failure: operational, never reported as missing evidence
                return None, f"{type(e).__name__}: tool {name} failed"
        return None, "unreachable"

    def execute_tool(s: State):
        events, errors, ops, bonus = [], [], s.get("tool_ops_failures", 0), 0
        usage = dict(s.get("usage") or {})
        for call in s["planned"]:
            t0 = time.perf_counter()
            res, ops_err = _run_one(call)
            dt = round(time.perf_counter() - t0, 3)
            args = {k: v for k, v in call.items() if k != "tool" and v is not None}
            if ops_err:
                ops += 1
                errors.append(f"{call['tool']}: operational failure, tool unavailable")
                events += _ev("execute_tool", "operational_failure", tool=call["tool"], args=args, error=ops_err, seconds=dt,
                              **({"transport": "mcp"} if tools.routed(call["tool"]) else {}))
            elif res.ok:
                events += _ev("execute_tool", "ok", tool=call["tool"], args=args, result=res.message[:300], new_items=[i.label for i in res.items], seconds=dt,
                              **({"transport": res.transport} if res.transport else {}),
                              **res.retrieval_trace)
                for key, value in res.usage.items():
                    usage[key] = usage.get(key, 0) + value
                if res.usage:
                    usage["rerank_cost_usd"] = round(usage.get("rerank_cost_usd", 0) + res.usage["cost_usd"], 6)
            else:
                errors.append(f"{call['tool']}({args}): {res.error_kind}: {res.message}")
                events += _ev("execute_tool", "error", tool=call["tool"], args=args, error_kind=res.error_kind, message=res.message[:300], seconds=dt,
                              **({"transport": res.transport} if res.transport else {}))
                if cfg.tool_set == "v2" and is_unknown_dimension(res) and not s.get("bonus_rounds"):
                    bonus = BONUS_ROUNDS
                    events += _ev("execute_tool", "bonus_round_granted", reason="unknown_dimension", rounds_allowed=MAX_ROUNDS + bonus)
        return {"round": s.get("round", 0) + 1, "calls_used": s.get("calls_used", 0) + len(s["planned"]), "tool_errors": errors,
                "tool_ops_failures": ops, "trace": events, **({"usage": usage} if usage else {}),
                **({"bonus_rounds": bonus} if bonus else {})}

    def after_execute(s: State):
        return "plan_research" if s["round"] < MAX_ROUNDS + s.get("bonus_rounds", 0) and s["calls_used"] < MAX_CALLS else "assess_evidence"

    def assess_evidence(s: State):
        if not tools.items and s.get("tool_ops_failures", 0) > 0:
            return {"outcome": "operational_failure", "errors": ["operational failure: evidence tools unavailable"],
                    "trace": _ev("assess_evidence", "operational_failure")}
        from labourlens.answer import crosscheck

        enabled = os.environ.get("LABOURLENS_GUARDS") != "off" and os.environ.get("LABOURLENS_CROSSCHECK") != "off"
        conflicts = crosscheck.annotate(tools) if enabled else []
        n = {k: sum(1 for i in tools.items if i.label[0] == k) for k in "POC"}
        return {"source_conflicts": conflicts, "trace": _ev("assess_evidence", "evidence_ready" if tools.items else "no_evidence", passages=n["P"], observations=n["O"], calculations=n["C"], data_quality_notes=list(tools.notes),
                             crosscheck_enabled=enabled, source_conflicts=conflicts, unresolved_tool_errors=len(s.get("tool_errors") or []))}

    def after_assess(s: State):
        return "finalize" if s.get("outcome") == "operational_failure" else "generate_answer"

    def generate_answer(s: State):
        msgs = s.get("messages")
        if not msgs:
            msgs = [{"role": "system", "content": answer_sys},
                    {"role": "user", "content": answer_user.format(context=cx.render(tools.items, tools.notes) if tools.items else "(no evidence items were collected)", question=s["question"])}]
        try:
            r = llm.chat(cfg.answer_model, msgs, 6000, **deadline())
        except Exception as e:  # LLMError, or a provider/shape failure: operational, never an escaped exception
            return {"outcome": "operational_failure", "errors": [f"operational failure: {type(e).__name__}: {e}"], "trace": _ev("generate_answer", "operational_failure")}
        ans, perr = _parse(r.content)
        return {"messages": msgs + [{"role": "assistant", "content": r.content or "{}"}], "attempts": s.get("attempts", 0) + 1,
                "answer": ans.model_dump() if ans else None, "errors": [r.refusal or perr or "empty output"] if ans is None else [],
                "usage": _usage(s, cfg.answer_model, r), "trace": _ev("generate_answer", "generated", attempt=s.get("attempts", 0) + 1, parsed=ans is not None)}

    def after_generate(s: State):
        return "finalize" if s.get("outcome") == "operational_failure" else "validate_answer"

    def validate_answer(s: State):
        errs = list(s.get("errors") or [])
        extra: dict = {}
        if s.get("answer"):
            from labourlens.answer.schema import Answer

            from labourlens.answer import crosscheck

            original = Answer.model_validate(s["answer"])
            enabled = os.environ.get("LABOURLENS_GUARDS") != "off" and os.environ.get("LABOURLENS_CROSSCHECK") != "off"
            conflicts = crosscheck.annotate(tools, original) if enabled else []
            checked = crosscheck.enforce(original, tools.items, conflicts)
            rep = validate.check(checked, tools.items)
            extra["answer"] = checked.model_dump()
            errs = rep.errors
            extra.update({"cited_ids": rep.cited_passage_ids, "ungrounded_numbers": rep.ungrounded_numbers, "source_conflicts": conflicts})
        checked_answer = extra.pop("answer", None)
        update = {"errors": errs, "trace": _ev("validate_answer", "valid" if not errs else "invalid", attempt=s.get("attempts"), n_errors=len(errs), **extra)}
        if checked_answer is not None:
            update["answer"] = checked_answer
        if errs and s.get("attempts", 0) < 2:
            update["messages"] = s["messages"] + [{"role": "user", "content": (PROMPTS / "repair_v1.md").read_text().format(errors="\n".join(f"- {e}" for e in errs))}]
        return update

    def after_validate_answer(s: State):
        return "generate_answer" if s.get("errors") and s.get("attempts", 0) < 2 else "finalize"

    def finalize(s: State):
        pool.shutdown(wait=False, cancel_futures=True)
        ev: list[dict] = []
        update: dict = {}
        if s.get("outcome") in ("rejected_input", "operational_failure"):
            outcome = s["outcome"]
        elif s.get("errors") or not s.get("answer"):
            outcome = "invalid"
        else:
            a = s["answer"]
            text = " ".join([a["summary"], a["reason"], a["clarification_question"], *a["caveats"], *[c["text"] for c in a["claims"]]])
            hits = scan_output(text, secret_values())
            if hits:  # output guard: a secret or the system prompt must never reach a user
                outcome, update["answer"] = "blocked_output", None
                ev += _ev("finalize", "output_blocked", findings=hits)
            else:
                outcome = a["status"]
        return {**update, "outcome": outcome, "trace": ev + _ev("finalize", outcome)}

    g = StateGraph(State)
    for fn in (validate_question, plan_research, execute_tool, assess_evidence, generate_answer, validate_answer, finalize):
        g.add_node(fn.__name__, fn)
    g.add_edge(START, "validate_question")
    g.add_conditional_edges("validate_question", after_validate, ["plan_research", "finalize"])
    g.add_conditional_edges("plan_research", after_plan, ["execute_tool", "assess_evidence", "finalize"])
    g.add_conditional_edges("execute_tool", after_execute, ["plan_research", "assess_evidence"])
    g.add_conditional_edges("assess_evidence", after_assess, ["generate_answer", "finalize"])
    g.add_conditional_edges("generate_answer", after_generate, ["validate_answer", "finalize"])
    g.add_conditional_edges("validate_answer", after_validate_answer, ["generate_answer", "finalize"])
    g.add_edge("finalize", END)
    return g.compile()


def run_agent(question: str, shared: Shared, cfg: AgentConfig = AgentConfig(), save_trace: bool = True, audit: dict | None = None) -> dict:
    """`audit`, if given, is {channel, session, ip, extra}: the run is appended to the audit log (labourlens.audit)."""
    tools = Tools(shared, cfg.retrieval, question, cfg.tool_timeout_s)
    graph = build_graph(shared, tools, cfg)
    t0 = time.perf_counter()
    final = graph.invoke({"question": question, "round": 0, "calls_used": 0, "attempts": 0, "trace": []}, {"recursion_limit": 40})
    run_id = uuid.uuid4().hex[:12]
    u = final.get("usage") or {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0}
    cited = next((e["detail"].get("cited_ids", []) for e in reversed(final["trace"]) if e["node"] == "validate_answer"), [])
    res = {"run_id": run_id, "question": question, "config": cfg.key(), "outcome": final["outcome"], "answer": final.get("answer"),
           "errors": final.get("errors") or [], "rounds": final.get("round", 0), "tool_calls": final.get("calls_used", 0),
           "crosscheck_enabled": os.environ.get("LABOURLENS_GUARDS") != "off" and os.environ.get("LABOURLENS_CROSSCHECK") != "off",
           "evidence": [{"label": i.label, "id": i.passage_id, "source_id": i.source_id} for i in tools.items],
           "evidence_text": {i.label: i.text for i in tools.items}, "cited_ids": cited, "usage": u,
           "seconds": round(time.perf_counter() - t0, 2), "trace": final["trace"],
           "corpus": shared.corpus if isinstance(getattr(shared, "corpus", None), dict) else None}
    if save_trace:
        d = paths.DATA / "runs" / "agent"
        d.mkdir(parents=True, exist_ok=True)
        saved = dict(res)
        saved["evidence"] = [{**item, "sha256": hashlib.sha256(res["evidence_text"][item["label"]].encode()).hexdigest()}
                             for item in res["evidence"]]
        if os.environ.get("LABOURLENS_DEBUG_EVIDENCE", "").lower() != "true":
            saved.pop("evidence_text", None)
        (d / f"{run_id}.json").write_text(redact(json.dumps(saved, indent=1, default=str)))
    if audit is not None:
        from labourlens.audit.log import log_run

        log_run(res, audit.get("channel", "api"), audit.get("session"), audit.get("ip"), audit.get("extra"))
    return res
