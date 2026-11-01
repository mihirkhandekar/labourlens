"""LLM scope triage for the served web application (D-051).

One short structured call to the primary model decides whether a message that did not take the small-talk fast path (D-050) concerns
the workbench at all. Only a clearly unrelated message (general knowledge, coding, medical or legal advice, personal employment
advice, creative writing, chit-chat beyond the closed list) is answered here, briefly, without searching. Everything else, including
hostile, causal, forecast and out-of-period questions, goes to the unchanged agent so its defences and refusals still run. The user
message is untrusted data: it is passed inside tags and escaped, the prompt says it has no authority, and the model's reply text is
only ever shown, never executed. Any failure (no key, timeout, provider error, invalid output) fails open to the agent.

This module is used only by the web runner. `run_agent`, the experiments and the threat test never call it."""

from __future__ import annotations

import html
import json
import re
import time
import uuid
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from labourlens import paths, prices
from labourlens.agent.smalltalk import _EXAMPLES
from labourlens.answer import llm
from labourlens.answer.pipeline import load_prompt
from labourlens.mcp.redact import redact

MODEL = "gpt-6-luna"
PROMPT = "triage_v1"
TIMEOUT_S = 8.0  # worst case 8 s here plus the agent's 80 s run deadline stays inside the 90 s request timeout
MAX_COMPLETION_TOKENS = 1500  # same cap as the planner; reasoning tokens count against it
MAX_QUESTION_CHARS = 1000  # same limit as the agent; a longer message is left to the agent's own rejection
MAX_REPLY_CHARS = 400
ROUTES = ("in_scope", "out_of_scope", "small_talk", "unsafe_or_sensitive")
CONFIG = f"scope_triage|{PROMPT}|{MODEL}"
EVENTS = {"out_of_scope": "outside_scope_answered_without_searching", "small_talk": "small_talk_answered_without_searching",
          "unsafe_or_sensitive": "unsafe_or_sensitive_declined_without_searching"}
_SPACE = re.compile(r"\s+")


class Triage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route: Literal["in_scope", "out_of_scope", "small_talk", "unsafe_or_sensitive"]
    reply: str


def json_schema() -> dict:
    return {"type": "object", "additionalProperties": False, "required": ["route", "reply"],
            "properties": {"route": {"type": "string", "enum": list(ROUTES)}, "reply": {"type": "string"}}}


def _empty_usage() -> dict:
    return {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0}


def clean_reply(text: str) -> str:
    return redact(_SPACE.sub(" ", text).strip())[:MAX_REPLY_CHARS].strip()


def classify(question: str, model: str = MODEL, prompt: str = PROMPT, timeout_s: float = TIMEOUT_S) -> dict:
    """One triage call. Never raises: any failure returns route 'in_scope' with `error` set (fail open).

    Returns {route, reply, error, usage, model, prompt, prompt_sha256, seconds}. `route` is the effective route; `reply` is non-empty
    only for a non-in_scope route."""
    system, user, digest = load_prompt(prompt)
    out = {"route": "in_scope", "reply": "", "error": None, "usage": _empty_usage(), "model": model, "prompt": prompt, "prompt_sha256": digest, "seconds": 0.0}
    if not question.strip() or len(question) > MAX_QUESTION_CHARS:
        out["error"] = "skipped_question_length"  # the agent rejects these itself
        return out
    t0 = time.perf_counter()
    r = None
    try:
        message = user.format(question=html.escape(question, quote=False))
        r = llm.chat(model, [{"role": "system", "content": system}, {"role": "user", "content": message}],
                     max_completion_tokens=MAX_COMPLETION_TOKENS, schema=json_schema(), schema_name="triage", timeout_s=timeout_s)
        u = out["usage"]
        u.update(calls=1, prompt_tokens=r.prompt_tokens, completion_tokens=r.completion_tokens, llm_seconds=round(r.seconds, 2),
                 cost_usd=round(prices.chat_cost(model, r.prompt_tokens, r.completion_tokens), 6))
        if r.refusal:
            raise ValueError("ModelRefusal")
        parsed = Triage.model_validate(json.loads(r.content))
        reply = clean_reply(parsed.reply)
        if parsed.route != "in_scope" and not reply:
            raise ValueError("EmptyReply")
        out["route"], out["reply"] = parsed.route, ("" if parsed.route == "in_scope" else reply)
    except (ValidationError, json.JSONDecodeError, ValueError, TypeError):
        out["error"] = "invalid_output"
    except Exception as e:  # LLMError, timeout, provider or shape failure, missing key: fail open
        out["error"] = type(e).__name__
    out["seconds"] = round(time.perf_counter() - t0, 3)
    return out


def _audit_block(info: dict) -> dict:
    u = info["usage"]
    return {"route": info["route"], "error": info["error"], "model": info["model"], "prompt": info["prompt"], "prompt_sha256": info["prompt_sha256"],
            "prompt_tokens": u["prompt_tokens"], "completion_tokens": u["completion_tokens"], "cost_usd": u["cost_usd"], "seconds": info["seconds"]}


def answer_for(route: str, reply: str) -> dict:
    if route == "unsafe_or_sensitive":
        return {"status": "refused", "summary": reply, "claims": [], "caveats": [], "clarification_question": "", "reason": ""}
    return {"status": "clarify", "summary": reply, "claims": [], "caveats": [], "clarification_question": _EXAMPLES, "reason": ""}


def _fast_result(question: str, shared, audit: dict | None, save_trace: bool, info: dict) -> dict:
    route = info["route"]
    outcome = "refused" if route == "unsafe_or_sensitive" else "clarify"
    detail = {"route": route, "seconds": info["seconds"], "prompt_tokens": info["usage"]["prompt_tokens"], "completion_tokens": info["usage"]["completion_tokens"]}
    trace = [{"t": round(time.time(), 3), "node": "validate_question", "event": EVENTS[route], "detail": detail},
             {"t": round(time.time(), 3), "node": "finalize", "event": outcome, "detail": {}}]
    run_id = uuid.uuid4().hex[:12]
    res = {"run_id": run_id, "question": question, "config": CONFIG, "outcome": outcome, "answer": answer_for(route, info["reply"]), "errors": [],
           "rounds": 0, "tool_calls": 0, "crosscheck_enabled": False, "evidence": [], "evidence_text": {}, "cited_ids": [],
           "usage": dict(info["usage"]), "trace": trace, "seconds": info["seconds"],
           "corpus": shared.corpus if isinstance(getattr(shared, "corpus", None), dict) else None}
    if save_trace:
        d = paths.DATA / "runs" / "agent"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{run_id}.json").write_text(redact(json.dumps({k: v for k, v in res.items() if k != "evidence_text"}, indent=1)))
    if audit is not None:
        from labourlens.audit.log import log_run

        log_run(res, audit.get("channel", "api"), audit.get("session"), audit.get("ip"),
                {**(audit.get("extra") or {}), "fast_path": "scope_triage", "triage": _audit_block(info)})
    return res


def run_with_triage(question: str, shared, audit: dict | None, agent: Callable[[dict | None], dict], save_trace: bool = True,
                    classifier: Callable[[str], dict] | None = None) -> dict:
    """Triage the question; answer here when it is clearly outside the workbench, otherwise call `agent(audit)` unchanged.

    The triage cost and a scope-check trace step are added to the agent result, so the daily budget ledger sees them."""
    info = (classifier or classify)(question)
    if info["route"] != "in_scope":
        return _fast_result(question, shared, audit, save_trace, info)
    extra = {**((audit or {}).get("extra") or {}), "triage": _audit_block(info)}
    res = agent(None if audit is None else {**audit, "extra": extra})
    if isinstance(res, dict) and isinstance(res.get("usage"), dict):
        failed = info["error"] is not None and not info["error"].startswith("skipped")
        detail = {"route": "in_scope", "seconds": info["seconds"], **({"error_kind": info["error"]} if info["error"] else {})}
        event = {"t": round(time.time(), 3), "node": "validate_question", "event": "scope_check_failed_open" if failed else "scope_check_in_scope", "detail": detail}
        res["trace"] = [event, *(res.get("trace") or [])]
        u, t = res["usage"], info["usage"]
        for key in ("calls", "prompt_tokens", "completion_tokens"):
            u[key] = u.get(key, 0) + t[key]
        u["cost_usd"] = round(u.get("cost_usd", 0.0) + t["cost_usd"], 6)
        u["llm_seconds"] = round(u.get("llm_seconds", 0.0) + t["llm_seconds"], 2)
    return res
