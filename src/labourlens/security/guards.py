"""Deterministic guards for untrusted text and model output. These are heuristics, not proof: they catch common injection
phrasing and hidden characters and give a second line of defence behind the prompt rules, schema validation and the
verbatim-quote check. Their misses are measured in the threat suite (experiments/threats) and listed in docs/threat-model.md."""

from __future__ import annotations

import os
import re
import html
import unicodedata

# Ablation switch for the threat-suite baseline ONLY: LABOURLENS_GUARDS=off disables the heuristic guards.


def guards_on() -> bool:
    return os.environ.get("LABOURLENS_GUARDS", "on") != "off"

# Phrases that address the model rather than describe labour statistics. Case-insensitive.
_INJECTION = [
    (r"\b(ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all|any|these|your|the)\b[^.\n]{0,30}\b(instruction|rule|prompt|guideline|constraint|polic)", "override_instructions"),
    (r"\b(new|updated|revised)\s+(instruction|rule|system prompt|directive)s?\b", "new_instructions"),
    (r"\byou\s+(are|must|should|will)\s+(now|only|always|never)\b", "role_reassignment"),
    (r"\b(system|developer)\s+(prompt|message|instruction)", "mentions_system_prompt"),
    (r"\b(reveal|print|show|output|repeat|leak|disclose)\b[^.\n]{0,40}\b(prompt|instruction|secret|api[ _-]?key|password|credential|environment variable|token)", "exfiltration_request"),
    (r"\b(respond|reply|answer|output)\s+(only\s+)?(with|that|exactly)\b", "output_hijack"),
    (r"\bdo\s+not\s+(cite|mention|use|follow|tell|reveal)\b", "suppression"),
    (r"\b(call|invoke|execute|run)\b[^.\n]{0,30}\b(tool|function|command|shell|sql|script)\b", "tool_invocation"),
    (r"<\s*/?\s*(system|assistant|tool|passage|evidence|instructions?)\b", "markup_spoofing"),
    (r"\bBEGIN\s+(SYSTEM|INSTRUCTIONS?)\b|\[/?INST\]|<\|im_(start|end)\|>", "chat_template_spoofing"),
    # Added 2 Nov 2026 after five paraphrase probes bypassed the scanner (docs/human-review/independent-ai-review-m1-2.md). Still lexical.
    (r"\b(send|transmit|forward|upload|email|exfiltrate)\b[^.\n]{0,60}\b(conversation|chat history|credentials?|secrets?|passwords?|api[ _-]?keys?|(its|their|the) contents?)\b[^.\n]{0,40}\b(to|at)\b|\b(send|transmit|forward|upload|exfiltrate)\b[^.\n]{0,60}https?://", "data_exfiltration"),
    (r"(~|\$HOME)/\.[a-z]|\.(aws|ssh)/|/etc/(passwd|shadow)\b|\bid_rsa\b", "sensitive_path"),
    (r"(?m)^\s*(assistant|system|developer)\s*:", "role_prefix_spoofing"),
    (r"\b(discard|drop|disable|turn off|remove)\b[^.\n]{0,30}\b(safeguards?|guardrails?|safety (rules|checks)|restrictions)\b|\b(highest|supreme|overriding)\s+(authority|priority)\b", "authority_claim"),
    (r"\b(scorer|grader|evaluator|judge)\b[^.\n]{0,30}\bexpects?\b|\b(replace|substitute|overwrite|falsify)\b[^.\n]{0,30}\b(evidence|source)\s+(values?|figures?|data)\b", "evidence_tampering"),
    (r"\b(omit|skip|hide|suppress)\b[^.\n]{0,20}\b(source|citation|reference)s?\b|\bregardless of (the )?(figures?|evidence|data|sources?)\b", "citation_or_evidence_override"),
]
INJECTION_RES = [(re.compile(p, re.I), name) for p, name in _INJECTION]
_FLAG = {"Cf"}  # zero-width and bidi-override characters can hide text from a reviewer; flagged
_STRIP = {"Cf", "Cc"}  # sanitising also drops control codes (the PDF parser leaves some from broken font encodings: not an attack sign)


def has_hidden_characters(text: str) -> bool:
    return any(unicodedata.category(c) in _FLAG for c in text)


def sanitize_text(text: str) -> str:
    """Remove control, zero-width and bidi-override characters (they can hide instructions from a human reviewer)."""
    return "".join(c for c in unicodedata.normalize("NFKC", text) if c in "\n\t" or unicodedata.category(c) not in _STRIP)


_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
_CUE_WORDS = frozenset({"ignore", "disregard", "reveal", "print", "show", "output", "reply", "answer", "you",
                        "are", "must", "should", "will", "now", "only", "always", "never", "run", "execute",
                        "invoke", "call", "discard", "disable", "safeguards", "instructions", "rules"})
_MARKUP = re.compile(r"<!--[\s\S]*?-->|</?[A-Za-z][^>]{0,1000}>")
_WORD = re.compile(r"\b[a-zA-Z0-9]+\b")
SCANNER_PROFILES = ("baseline", "markup", "leet", "window")


def scanner_views(text: str, profile: str) -> list[str]:
    """Cumulative normalisation ablations, not a semantic classifier. Preserve the original view as well.

    Leet decoding is restricted to known cue words to avoid turning published numbers into language.
    Window matching joins at most two adjacent fragments, each no more than 240 characters.
    """
    if profile not in SCANNER_PROFILES:
        raise ValueError(f"unknown scanner profile: {profile}")
    clean = sanitize_text(text)
    views = [clean]
    if profile == "baseline":
        return views
    plain = _MARKUP.sub("", html.unescape(clean))
    plain = re.sub(r"(\*\*|__|`)", "", plain)
    views.append(plain)
    if profile == "markup":
        return views

    def decode(match: re.Match) -> str:
        word = match.group()
        decoded = word.lower().translate(_LEET)
        return decoded if any(c.isdigit() for c in word) and decoded in _CUE_WORDS else word

    decoded = _WORD.sub(decode, plain)
    views.append(decoded)
    if profile == "window":
        fragments = [s.strip() for s in re.split(r"[.!?\n|]+", decoded) if s.strip()]
        views.extend(f"{a} {b}" for a, b in zip(fragments, fragments[1:]) if len(a) <= 240 and len(b) <= 240)
    return views


def injection_flags(text: str, *, profile: str = "window") -> list[str]:
    if not guards_on():
        return []
    flags = sorted({name for view in scanner_views(text, profile) for rx, name in INJECTION_RES if rx.search(view)})
    if has_hidden_characters(text):
        flags.append("hidden_characters")
    return flags


_SECRET_SHAPES = [re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
                  re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")]


def scan_output(text: str, secrets: list[str] | None = None) -> list[str]:
    """Findings in model output that must never reach a user: known secret values, secret-shaped strings, prompt text."""
    if not guards_on():
        return []
    hits = [f"secret_value:{i}" for i, s in enumerate(secrets or []) if s and s in text]
    hits += [f"secret_shape:{i}" for i, rx in enumerate(_SECRET_SHAPES) if rx.search(text)]
    if re.search(r"(?i)you are the (answer|planning) step of labourlens", text):
        hits.append("system_prompt_leak")
    return hits
