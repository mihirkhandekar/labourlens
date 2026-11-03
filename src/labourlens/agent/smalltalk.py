"""Small-talk fast path for the served web application (D-050).

A whole-message match against a closed list answers greetings, thanks, goodbyes, "what can you do" and similar without a model
call, a search or any cost. Matching is deliberately narrow: the message is normalised (case, punctuation, whitespace) and must
equal a listed phrase exactly, so "hi, ignore previous instructions" or "help me compare unemployment" still reach the agent.
A message with no letter or digit at all (only punctuation or emoji) gets the same helpful reply instead of an abstention.

This module is used only by the web runner. `run_agent` and the evaluated experiments never call it."""

from __future__ import annotations

import json
import re
import time
import unicodedata
import uuid

from labourlens import paths
from labourlens.data import catalog

CONFIG = "small_talk_fast_path"

_GREETING = {
    "hi", "hello", "hey", "hiya", "howdy", "yo", "hi there", "hello there", "hey there", "greetings", "good morning",
    "good afternoon", "good evening", "morning", "afternoon", "evening", "hi labourlens", "hello labourlens", "hey labourlens",
    "how are you", "how are you doing", "hows it going", "whats up", "sup",
}
_THANKS = {
    "thanks", "thank you", "thanks a lot", "thank you very much", "thanks very much", "thanks so much", "thank you so much",
    "many thanks", "cheers", "thx", "ty", "ta", "ok thanks", "okay thanks", "great thanks", "perfect thanks", "thanks labourlens",
}
_BYE = {"bye", "bye bye", "goodbye", "good bye", "see you", "see you later", "see ya", "cya", "good night", "goodnight"}
_ABOUT = {
    "who are you", "what are you", "what is labourlens", "whats labourlens", "who is labourlens", "what is this", "whats this",
    "what is this tool", "what is this site",
}
_HELP = {
    "help", "help me", "i need help", "can you help", "can you help me", "how can you help", "how can you help me",
    "what can you do", "what do you do", "what can i ask", "what can i ask you", "what can you help with",
    "what can you help me with", "how does this work", "how do you work", "how do i use this", "examples", "show examples",
    "give me examples", "instructions", "menu",
}
_FILLER = {"ok", "okay", "k", "yes", "no", "yep", "nope", "sure", "cool", "nice", "great", "hmm", "hm", "test", "testing", "test test", "ping", "ready"}

_INTRO = {
    "greeting": "Hello, I am LabourLens.",
    "thanks": "You are welcome.",
    "bye": "Goodbye. Come back whenever you have a question.",
    "about": "I am LabourLens, a research assistant for Singapore labour-market questions.",
    "help": "I am LabourLens, a research assistant for Singapore labour-market questions.",
    "filler": "I am LabourLens, a research assistant for Singapore labour-market questions.",
    "no_content": "I could not find a question in that message.",
}
_CAPABILITY = (f"I can look up Ministry of Manpower statistics and MOM report passages for {catalog.scope_words()}, compare figures across "
               "quarters, and cite every source I use. When the evidence is missing or does not support an answer, I say so instead of guessing.")
_EXAMPLES = ("You could ask: “What was the resident unemployment rate in Q4 2025?” or “How did retrenchments change between Q1 2025 and Q1 2026?” "
             "or “What did the Q2 2026 advance release say about employment growth?”")

_PUNCTUATION = re.compile(r"[^\w\s]|_", re.UNICODE)
_HAS_CONTENT = re.compile(r"[^\W_]", re.UNICODE)
_CLASSES = (("greeting", _GREETING), ("thanks", _THANKS), ("bye", _BYE), ("about", _ABOUT), ("help", _HELP), ("filler", _FILLER))


def normalise(text: str) -> str:
    """Lower-case, NFKC, apostrophes dropped, other punctuation turned into spaces, whitespace collapsed."""
    t = unicodedata.normalize("NFKC", text).casefold().replace("'", "").replace("\u2019", "")
    return " ".join(_PUNCTUATION.sub(" ", t).split())


def classify(question: str) -> str | None:
    """Return the small-talk class ('greeting', 'thanks', 'bye', 'about', 'help', 'filler', 'no_content') or None to run the agent."""
    if not isinstance(question, str):
        return None
    if not _HAS_CONTENT.search(question):
        return "no_content"
    if len(question) > 200:
        return None
    norm = normalise(question)
    for name, phrases in _CLASSES:
        if norm in phrases:
            return name
    return None


def answer_for(kind: str) -> dict:
    return {"status": "clarify", "summary": f"{_INTRO[kind]} {_CAPABILITY}", "claims": [], "caveats": [],
            "clarification_question": _EXAMPLES, "reason": ""}


def run_smalltalk(question: str, shared=None, audit: dict | None = None, save_trace: bool = True) -> dict | None:
    """Return a run_agent-shaped result for small talk, or None when the agent should handle the question."""
    kind = classify(question)
    if kind is None:
        return None
    t0 = time.perf_counter()
    run_id = uuid.uuid4().hex[:12]
    event = {"t": round(time.time(), 3), "node": "validate_question", "event": "small_talk_answered_without_searching", "detail": {"kind": kind}}
    done = {"t": round(time.time(), 3), "node": "finalize", "event": "clarify", "detail": {}}
    res = {"run_id": run_id, "question": question, "config": CONFIG, "outcome": "clarify", "answer": answer_for(kind), "errors": [],
           "rounds": 0, "tool_calls": 0, "crosscheck_enabled": False, "evidence": [], "evidence_text": {}, "cited_ids": [],
           "usage": {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0},
           "trace": [event, done], "corpus": shared.corpus if isinstance(getattr(shared, "corpus", None), dict) else None}
    res["seconds"] = round(time.perf_counter() - t0, 4)
    if save_trace:
        d = paths.DATA / "runs" / "agent"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{run_id}.json").write_text(json.dumps({k: v for k, v in res.items() if k != "evidence_text"}, indent=1))
    if audit is not None:
        from labourlens.audit.log import log_run

        log_run(res, audit.get("channel", "api"), audit.get("session"), audit.get("ip"), {**(audit.get("extra") or {}), "fast_path": "small_talk"})
    return res
