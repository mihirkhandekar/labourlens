"""Conversation context for the served web application (D-054).

The workbench keeps no server-side conversation. The browser may send the last three finished turns with a new message; one short
structured call to the primary model then rewrites the message into ONE standalone question, resolving what only the conversation
or the clock can resolve ("I mean retrenched employees", "and for 2025?", "last year", "laid off"). The rewrite then goes through
the unchanged small-talk check, triage and agent as if the user had typed it, so every guard still sees a single question.

Safety properties: history and the message are untrusted data (escaped, inside tags, the prompt says so); the output must be a single
short line, must not carry an injection pattern the user's own message lacked, and must not introduce a number or capitalised name
that is in neither the message, the history nor the server's date facts; any failure (no key, timeout, provider error, invalid or
suspicious output) fails open to the original message. No call at all is made when there is no history and the message holds no
relative date and no layoff synonym, so self-contained questions cost nothing and are unchanged.

This module is used only by the web runner. `run_agent`, the experiments and the threat test never call it."""

from __future__ import annotations

import html
import json
import re
import time
from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, ValidationError

from labourlens import prices
from labourlens.answer import llm
from labourlens.answer.pipeline import load_prompt
from labourlens.security.guards import injection_flags

MODEL = "gpt-6-luna"
PROMPT = "contextualise_v1"
TIMEOUT_S = 8.0  # same bound as triage: worst case 8 s + 8 s + the agent's 80 s deadline is capped by the request timeout
MAX_COMPLETION_TOKENS = 1500
MAX_QUESTION_CHARS = 1000  # the agent's own limit; a longer message is left to its rejection
MAX_REWRITE_CHARS = 300
MAX_TURNS = 3
MAX_SUMMARY_CHARS = 600  # per history field handed to the model
MAX_STATUS_CHARS = 20
SGT = timezone(timedelta(hours=8))  # Singapore has no daylight saving

_SPACE = re.compile(r"\s+")
# "layoff" as a noun is deliberately absent: MOM also publishes "temporary layoff" as a different measure, so only the verb forms are mapped
_LAYOFF = r"laid[\s-]*off|laying[\s-]+off|made\s+redundant|let\s+go"
_RELATIVE = (r"(?:last|this|current|previous|prior|next|coming)\s+(?:full\s+|calendar\s+)?(?:year|quarter)\b"
             r"|the\s+(?:past|last)\s+(?:\w+\s+)?(?:years?|quarters?)\b|year[\s-]+to[\s-]+date\b|ytd\b|so\s+far\s+this\b")
TRIGGER = re.compile(rf"\b(?:{_LAYOFF}|{_RELATIVE})", re.IGNORECASE)
_ALWAYS_ALLOWED = {"singapore", "mom", "mti", "sgt", "singstat", "retrenched", "retrenchment", "ministry", "manpower"}
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_CAPITAL = re.compile(r"(?<![\w])[A-Z][a-z]{2,}(?:[A-Z][a-z]+)*")
_WORD = re.compile(r"[^\W_]+")


class Rewrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str


def json_schema() -> dict:
    return {"type": "object", "additionalProperties": False, "required": ["question"], "properties": {"question": {"type": "string"}}}


def _empty_usage() -> dict:
    return {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0}


def singapore_today(now: datetime | None = None) -> date:
    return (now or datetime.now(SGT)).astimezone(SGT).date()


def resolve_dates(today: date) -> dict:
    """Deterministic calendar facts for relative expressions. 'last quarter' is the calendar quarter before the current one."""
    quarter = (today.month - 1) // 3 + 1

    def shift(by: int) -> str:
        index = today.year * 4 + (quarter - 1) + by
        return f"{index // 4}-Q{index % 4 + 1}"

    return {"today": today.isoformat(), "year": today.year, "last_year": today.year - 1, "next_year": today.year + 1,
            "quarter": shift(0), "last_quarter": shift(-1), "quarter_before_last": shift(-2), "next_quarter": shift(1)}


def date_facts(today: date) -> str:
    d = resolve_dates(today)
    return (f"today is {d['today']}. The current year is {d['year']}; last year is {d['last_year']}; next year is {d['next_year']}. "
            f"This quarter is {d['quarter']}; last quarter, which is also the previous quarter, is {d['last_quarter']} (the latest complete quarter); "
            f"two quarters ago is {d['quarter_before_last']}; next quarter is {d['next_quarter']}.")


def needs_rewrite(message: str, history: list[dict]) -> bool:
    """Deterministic gate: call the model only with history, or when the message holds a relative date or a layoff synonym."""
    return bool(history) or bool(TRIGGER.search(message))


def parse_history(raw) -> list[dict]:
    """Validate the client-supplied history; raises ValueError (the endpoint turns it into a 422). None and [] mean no history."""
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > MAX_TURNS:
        raise ValueError(f"history must be a list of at most {MAX_TURNS} turns")
    turns = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"question", "status", "summary"}:
            raise ValueError("each history turn must have only question, status and summary")
        q, s, a = item["question"], item["status"], item["summary"]
        if not all(isinstance(v, str) for v in (q, s, a)):
            raise ValueError("history fields must be strings")
        if len(q) > MAX_QUESTION_CHARS or len(s) > MAX_STATUS_CHARS or len(a) > MAX_SUMMARY_CHARS:
            raise ValueError("history field too long")
        turns.append({"question": q, "status": s, "summary": a})
    return turns


def _render_history(history: list[dict]) -> str:
    def esc(text: str) -> str:
        return html.escape(_SPACE.sub(" ", text).strip()[:MAX_SUMMARY_CHARS], quote=False)

    if not history:
        return "(no earlier turns)"
    return "\n".join(f"<turn n=\"{i}\"><user_question>{esc(t['question'])}</user_question><workbench_status>{esc(t['status'])}</workbench_status>"
                     f"<workbench_reply>{esc(t['summary'])}</workbench_reply></turn>" for i, t in enumerate(history, 1))


def _clean(candidate: str, message: str, history: list[dict], today: date) -> str | None:
    """The rewrite if it is acceptable, otherwise None (fail open to the message)."""
    q = _SPACE.sub(" ", candidate).strip()
    if not q or len(q) > MAX_REWRITE_CHARS or "\n" in candidate.strip() or "<" in q or ">" in q:
        return None
    if injection_flags(q) and not injection_flags(message):
        return None
    # Earlier replies are untrusted and may carry figures or planted text: only a clarification question (which restates the options) may lend words.
    allowed_text = " ".join([message, *(t["question"] + (f" {t['summary']}" if t["status"] == "clarify" else "") for t in history), date_facts(today)])
    allowed_numbers = set(_NUMBER.findall(allowed_text))
    allowed_words = {w.lower() for w in _WORD.findall(allowed_text)} | _ALWAYS_ALLOWED
    if any(n not in allowed_numbers for n in _NUMBER.findall(q)):
        return None
    if any(w.lower() not in allowed_words for w in _CAPITAL.findall(q) if not q.startswith(w)):
        return None
    return q


def passthrough(message: str, model: str = MODEL, prompt: str = PROMPT, digest: str = "") -> dict:
    """The result shape for 'no rewrite, no call'."""
    return {"question": message, "original": message, "changed": False, "called": False, "error": None, "usage": _empty_usage(), "model": model,
            "prompt": prompt, "prompt_sha256": digest, "seconds": 0.0}


def contextualise(message: str, history: list[dict] | None = None, today: date | None = None, model: str = MODEL, prompt: str = PROMPT,
                  timeout_s: float = TIMEOUT_S, force: bool = False) -> dict:
    """Never raises. Returns {question, original, changed, called, error, usage, model, prompt, prompt_sha256, seconds}.
    `question` is the rewrite when one was produced and accepted, else the original message."""
    history = history or []
    system, user, digest = load_prompt(prompt)
    out = passthrough(message, model, prompt, digest)
    if not force and not needs_rewrite(message, history):
        return out
    if not message.strip() or len(message) > MAX_QUESTION_CHARS:
        out["error"] = "skipped_question_length"
        return out
    today = today or singapore_today()
    t0 = time.perf_counter()
    out["called"] = True
    try:
        body = user.format(dates=date_facts(today), history=_render_history(history), message=html.escape(message, quote=False))
        r = llm.chat(model, [{"role": "system", "content": system}, {"role": "user", "content": body}],
                     max_completion_tokens=MAX_COMPLETION_TOKENS, schema=json_schema(), schema_name="contextualise", timeout_s=timeout_s)
        out["usage"].update(calls=1, prompt_tokens=r.prompt_tokens, completion_tokens=r.completion_tokens, llm_seconds=round(r.seconds, 2),
                            cost_usd=round(prices.chat_cost(model, r.prompt_tokens, r.completion_tokens), 6))
        if r.refusal:
            raise ValueError("ModelRefusal")
        parsed = Rewrite.model_validate(json.loads(r.content))
        cleaned = _clean(parsed.question, message, history, today)
        if cleaned is None:
            out["error"] = "rejected_rewrite"
        elif cleaned != message.strip():
            out["question"], out["changed"] = cleaned, True
    except (ValidationError, json.JSONDecodeError, ValueError, TypeError):
        out["error"] = "invalid_output"
    except Exception as e:  # LLMError, timeout, provider failure, missing key: fail open
        out["error"] = type(e).__name__
    out["seconds"] = round(time.perf_counter() - t0, 3)
    return out


def audit_block(info: dict) -> dict:
    u = info["usage"]
    return {"called": info["called"], "changed": info["changed"], "original": info["original"][:MAX_QUESTION_CHARS], "rewritten": info["question"][:MAX_REWRITE_CHARS],
            "error": info["error"], "model": info["model"], "prompt": info["prompt"], "prompt_sha256": info["prompt_sha256"],
            "prompt_tokens": u["prompt_tokens"], "completion_tokens": u["completion_tokens"], "cost_usd": u["cost_usd"], "seconds": info["seconds"]}


def attach(res: dict, info: dict) -> dict:
    """Record the rewrite on a run result: usage, a 'contextualise' trace step, and `interpreted_as` when the question was changed."""
    if not isinstance(res, dict) or not info["called"]:
        return res
    detail = {"seconds": info["seconds"], **({"error_kind": info["error"]} if info["error"] else {})}
    event = "question_rewritten" if info["changed"] else ("failed_open" if info["error"] else "question_kept")
    res["trace"] = [{"t": round(time.time(), 3), "node": "contextualise", "event": event, "detail": detail}, *(res.get("trace") or [])]
    if isinstance(res.get("usage"), dict):
        u, t = res["usage"], info["usage"]
        for key in ("calls", "prompt_tokens", "completion_tokens"):
            u[key] = u.get(key, 0) + t[key]
        u["cost_usd"] = round(u.get("cost_usd", 0.0) + t["cost_usd"], 6)
        u["llm_seconds"] = round(u.get("llm_seconds", 0.0) + t["llm_seconds"], 2)
    if info["changed"]:
        res["interpreted_as"] = info["question"]
        res["original_question"] = info["original"]
    return res
