"""Single-process presentation server with a deliberately bounded, authenticated live demo."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import inspect
import json
import logging
import math
import os
import re
import secrets
import time
import unicodedata
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from labourlens import paths
from labourlens.answer.validate import copied_spans, key_numbers, norm, quote_in, report_windows, rights_tokens
from labourlens.mcp.redact import redact, redact_values
from labourlens.audit import log as audit_log
from labourlens.report import audit as web_audit

COOKIE = "labourlens_session"
# Conservative admission charge for this bounded demo; provider project budgets remain the hard stop.
RUN_RESERVATION_USD = 0.05
STREAM_KEEPALIVE_S = 10.0  # an idle stream sends a comment line this often so a proxy does not close it
RIGHTS_NOTICE = "Text withheld: excessive verbatim overlap with source evidence."


def _tool_transport_from_env() -> str:
    """LABOURLENS_MCP=false (the D-053 switch) means direct; otherwise LABOURLENS_TOOL_TRANSPORT (direct | mcp_stats | mcp_all, default mcp_stats).
    An unknown value stops the start-up rather than quietly choosing a route."""
    from labourlens.agent.served import DEFAULT_TRANSPORT, TRANSPORTS

    if os.getenv("LABOURLENS_MCP", "true").lower() == "false":
        return "direct"
    value = os.getenv("LABOURLENS_TOOL_TRANSPORT", DEFAULT_TRANSPORT).strip().lower()
    if value not in TRANSPORTS:
        raise ValueError(f"LABOURLENS_TOOL_TRANSPORT must be one of {TRANSPORTS}, got {value!r}")
    return value


@dataclass
class Settings:
    access_codes: tuple[str, ...] = ()
    session_secret: str = ""
    demo_enabled: bool = True
    daily_budget_usd: float = 2.0
    login_limit: int = 5
    session_limit: int = 10
    ip_limit: int = 20
    window_seconds: int = 60
    max_concurrent: int = 2
    request_timeout: float = 90.0
    body_limit: int = 8192
    login_lock_per_address: int = 10   # failed codes from one client address within 10 minutes before it is locked
    login_lock_global: int = 200       # failed codes from all addresses within 10 minutes before every invalid code is refused
    run_deadline_s: float = 80.0       # planner + answer LLM budget for one run; below request_timeout so the slot is freed
    feedback_dir: Path = field(default_factory=lambda: paths.DATA / "audit")
    triage_enabled: bool = True        # D-051: LLM scope check in front of the agent, web app only
    contextualise_enabled: bool = True # D-054: follow-up and relative-date rewrite before triage, web app only
    tool_transport: str = "mcp_stats"    # D-066: how the agent's three tools reach their data: mcp_stats (live default: get_series only, D-053), mcp_all (all three tools, measured, not live) or direct (LABOURLENS_TOOL_TRANSPORT)

    @property
    def mcp_enabled(self) -> bool:
        return self.tool_transport != "direct"

    @classmethod
    def from_env(cls):
        return cls(access_codes=tuple(c.strip() for c in os.getenv("LABOURLENS_ACCESS_CODES", "").split(",") if c.strip()),
                   session_secret=os.getenv("LABOURLENS_SESSION_SECRET", ""),
                   demo_enabled=os.getenv("LABOURLENS_DEMO_ENABLED", "true").lower() != "false",
                   triage_enabled=os.getenv("LABOURLENS_TRIAGE", "true").lower() != "false",
                   contextualise_enabled=os.getenv("LABOURLENS_CONTEXTUALISE", "true").lower() != "false",
                   tool_transport=_tool_transport_from_env(),
                   daily_budget_usd=float(os.getenv("LABOURLENS_DAILY_BUDGET_USD", "2.0")))

    @property
    def enabled(self):
        return (self.demo_enabled and bool(self.access_codes)
                and all(len(code) >= 16 for code in self.access_codes) and len(self.session_secret) >= 32)


def _version() -> str:
    from importlib import metadata

    try:
        base = metadata.version("labourlens")
    except metadata.PackageNotFoundError:
        base = "unknown"
    build = re.sub(r"[^0-9A-Za-z._-]", "", os.getenv("LABOURLENS_BUILD", ""))[:40]
    return f"{base}+{build}" if build else base


def _safe_url(value):
    value = str(value or "")
    return value if urlparse(value).scheme == "https" else ""


@lru_cache(maxsize=1)
def _provenance():
    manifest = paths.DATA / "manifests" / "manifest.json"
    try:
        return {e["source_id"]: e for e in json.loads(manifest.read_text()).get("entries", [])}
    except (OSError, ValueError, KeyError):
        return {}

RIGHTS_WORD_WINDOW = 13
RIGHTS_CHAR_WINDOW = 80
_TOKEN = re.compile(r"[^\W_]+")
COPYRIGHT_TRIM_NOTE = "Some wording was removed to respect the publisher's copyright."


def _tokens(text) -> list[str]:
    """Letters and digits only, NFKC case-folded: punctuation, hyphens, spacing and zero-width characters do not change tokens."""
    return _TOKEN.findall(unicodedata.normalize("NFKC", str(text or "")).casefold())


class _Overlap:
    """Does free text reproduce a stretch of the evidence? Two tests on the punctuation-free text: a 13-word window and an
    80-character window over the letters and digits with the spaces removed (so hyphenating, re-spacing or re-punctuating words
    does not hide a copied stretch). Light word substitutions every few words still evade it: this reduces verbatim
    disclosure, it does not prove its absence."""

    def __init__(self, texts):
        w, c = RIGHTS_WORD_WINDOW, RIGHTS_CHAR_WINDOW
        self.words, self.chars = set(), set()
        for text in texts:
            tokens = _tokens(text)
            self.words.update(tuple(tokens[i:i + w]) for i in range(max(0, len(tokens) - w + 1)))
            joined = "".join(tokens)
            self.chars.update(hash(joined[i:i + c]) for i in range(max(0, len(joined) - c + 1)))

    def copies(self, value) -> bool:
        w, c = RIGHTS_WORD_WINDOW, RIGHTS_CHAR_WINDOW
        tokens = _tokens(value)
        if any(tuple(tokens[i:i + w]) in self.words for i in range(max(0, len(tokens) - w + 1))):
            return True
        joined = "".join(tokens)
        return any(hash(joined[i:i + c]) in self.chars for i in range(max(0, len(joined) - c + 1)))


_CLAUSE_END = re.compile(r"[.!?;][\"')\]]*(?=\s|$)|\n")


class _ReportSpans:
    """Served policy: no seven consecutive normalized report words in prose (the validator's tokenisation and window length, shared
    from answer.validate). A sentence or clause containing a copied run is dropped whole, never replaced by a placeholder, and
    ``trimmed`` records that something was removed so the caller can say so. This is a conservative reproduction boundary, not a
    legal clearance claim."""

    def __init__(self, texts):
        self.windows = report_windows(texts)
        self.trimmed = False

    def trim(self, value):
        text = str(value or "")
        spans = copied_spans(text, self.windows)
        if not spans:
            return text
        self.trimmed = True
        bounds, last = [], 0
        for m in _CLAUSE_END.finditer(text):
            bounds.append((last, m.end()))
            last = m.end()
        bounds.append((last, len(text)))
        kept = "".join(text[a:b] for a, b in bounds if not any(s < b and e > a for s, e in spans)).strip()
        return kept[:-1].rstrip() + "." if kept.endswith(";") else kept


def _short_report_quote(quote):
    """Keep an actual source substring, never an ellipsis presented as verbatim."""
    tokens = rights_tokens(quote)
    return quote[:tokens[5][2]] if len(tokens) > 6 else quote


def _bounded_answer(answer, evidence_text, *, served_annual=False):
    """Rights boundary independent of model compliance and internal validators.

    Only P* report passages are guarded, not open-data O* or computed C* rows.
    Annual served runs trim seven-word report spans and cap report quotations at
    six normalized words, including quotations embedded in reasons/caveats.
    Frozen/nonannual projections retain the historical 13-word/80-character
    whole-field heuristic and 40-word citation allowance for reproducibility.
    """
    texts = [text for label, text in evidence_text.items() if str(label).startswith("P")]
    overlap = _ReportSpans(texts) if served_annual else _Overlap(texts)

    def free_text(value):
        if served_annual:
            return overlap.trim(value)
        return RIGHTS_NOTICE if overlap.copies(value) else str(value or "")

    result = {k: (str(answer.get(k, "") or "") if k == "status" and served_annual else free_text(answer.get(k, "")))
              for k in ("status", "summary", "reason", "clarification_question")}
    result["caveats"] = [free_text(c) for c in answer.get("caveats", [])]
    if served_annual:
        result["caveats"] = [c for c, original in zip(result["caveats"], answer.get("caveats", [])) if c or not str(original or "").strip()]
    result["claims"] = []
    seen, total = set(), 0
    per_card = defaultdict(int)
    for claim in answer.get("claims", [])[:12]:
        projected = {k: free_text(v) if isinstance(v, str) else v for k, v in claim.items() if k != "citations"}
        if served_annual and not str(projected.get("text", "")).strip() and str(claim.get("text", "")).strip():
            continue  # the whole claim was copied report wording: dropped, not shown as a placeholder
        projected["citations"] = []
        shown = set()  # a quote is listed once per claim; the same quote may support several claims
        for citation in claim.get("citations", [])[:3]:
            label, quote = str(citation.get("label", "")), str(citation.get("quote", ""))
            count = len(quote.split())
            normalized = norm(quote)
            # Same matching rule as answer.validate.check, so a citation the validator accepted is not dropped here.
            if (not count or count > 40 or (label, normalized) in shown
                    or not quote_in(quote, str(evidence_text.get(label, "")))):
                continue
            if served_annual and label.startswith("P"):
                quote = _short_report_quote(quote)
                count, normalized = len(quote.split()), norm(quote)
                if (label, normalized) in shown:
                    continue
            if normalized not in seen:  # reuse of an already shown quote discloses nothing new, so it costs no quote budget
                if total + count > 120 or per_card[label] + count > 120:
                    continue
                seen.add(normalized)
                total += count
                per_card[label] += count
            shown.add((label, normalized))
            projected["citations"].append({**citation, "quote": quote})
        result["claims"].append(projected)
    if served_annual and overlap.trimmed:
        result["caveats"].append(COPYRIGHT_TRIM_NOTE)
    return result


def _ungrounded_numbers(raw: dict) -> list[str]:
    """Figures the validator could not find in the evidence (last validate_answer event), as 'where: number'."""
    for event in reversed(raw.get("trace", []) or []):
        if isinstance(event, dict) and event.get("node") == "validate_answer":
            flagged = (event.get("detail") or {}).get("ungrounded_numbers") or []
            # The trace keeps every flag; the browser shows key figures only (decimals, comma-grouped, 100 or more), not "Q1" or "2 sectors".
            return [str(x)[:60] for x in flagged if isinstance(x, str) and key_numbers(x.rsplit(": ", 1)[-1])][:12]
    return []


_TRACE_DETAIL_KEYS = {"tool", "args", "new_items", "seconds", "round", "n_calls", "observations", "passages", "calculations", "error_kind", "calls_used", "data_quality_notes"}


def public_trace_item(e: dict) -> dict:
    """One trace event as the browser may see it: node, event and an allow-listed subset of the detail (never passage text or model output)."""
    detail = e.get("detail", {}) if isinstance(e.get("detail"), dict) else {}
    return {"node": e.get("node", ""), "event": e.get("event", ""),
            "detail": {**{k: v for k, v in detail.items() if k in _TRACE_DETAIL_KEYS}, **({"transport": "mcp"} if detail.get("transport") == "mcp" else {})}}


_STAGE_TEXT = {("contextualise", "running"): "Reading the question in context.", ("contextualise", "done"): "Question read.",
               ("triage", "running"): "Checking the question is about Singapore labour-market statistics.", ("triage", "done"): "Scope check finished.",
               ("planning", "running"): "Planning which evidence to collect.", ("answering", "running"): "Writing the answer from the evidence.",
               ("validating", "running"): "Checking every quote and number against the evidence."}
_NODE_STAGE = {"plan_research": "planning", "generate_answer": "answering", "validate_answer": "validating"}


def public_event(event: dict):
    """A live runner event as (sse event name, data), or None when it is not shown. Only allow-listed fields pass; there is no model text."""
    kind = event.get("type")
    if kind == "stage":
        stage, state = str(event.get("stage", ""))[:24], str(event.get("state", ""))[:12]
        data = {"stage": stage, "state": state, "text": _STAGE_TEXT.get((stage, state), "")}
        if stage == "triage" and state == "done":
            data["route"] = str(event.get("route", ""))[:24]
            if data["route"] != "in_scope":
                data["text"] = "The question is outside the workbench, so it was answered without searching."
        if stage == "contextualise" and state == "done" and event.get("changed"):
            data["text"] = "Question rewritten using the earlier turns."
        return "status", data
    if kind == "node_started":
        stage = _NODE_STAGE.get(event.get("node"))
        return None if stage is None else ("status", {"stage": stage, "state": "running", "text": _STAGE_TEXT[(stage, "running")]})
    if kind == "trace" and isinstance(event.get("item"), dict):
        return "trace", {"item": public_trace_item(event["item"])}
    if kind == "tool_call_started":
        args = event.get("args") if isinstance(event.get("args"), dict) else {}
        return "tool", {"phase": "started", "tool": str(event.get("tool", ""))[:64], "args": {str(k)[:40]: (v[:300] if isinstance(v, str) else v) for k, v in args.items()}}
    if kind == "tool_call_finished" and isinstance(event.get("item"), dict):
        return "tool", {"phase": "finished", "item": public_trace_item(event["item"])}
    return None


def public_result(raw: dict, shared) -> dict:
    """Expose only cited report fragments, never the tool's full passage registry."""
    answer = raw.get("answer")
    if not isinstance(answer, dict) or raw.get("outcome") not in ("answered", "abstained", "clarify", "refused"):
        reason = ("The drafted answer did not pass the citation checks, so I did not show it. Try rephrasing or ask again."
                  if raw.get("outcome") == "invalid" else "Evidence or service unavailable.")
        answer = {"status": "abstained", "summary": "The run did not produce a validated answer.", "claims": [], "caveats": [], "reason": reason, "clarification_question": ""}
    answer = _bounded_answer(answer, raw.get("evidence_text", {}), served_annual=raw.get("tool_set") == "annual")
    flagged = _ungrounded_numbers(raw)
    answer["ungrounded_numbers"] = flagged
    if flagged:
        # Visible in the browser: the run was not rejected (validator behaviour is unchanged), but the reader is told.
        answer["caveats"] = [*answer["caveats"], "Number not found in evidence: " + ", ".join(f.replace(": ", " (", 1) + ")" for f in flagged) + ". Treat as unverified."]
    quotes = defaultdict(list)
    for claim in answer.get("claims", []):
        for c in claim.get("citations", []):
            quote = str(c.get("quote", ""))
            if len(quote.split()) <= 40:
                quotes[str(c.get("label", ""))].append(quote)
    from labourlens.data import catalog
    sources = {s["source_id"]: s for group in catalog.sources().values() if isinstance(group, list) for s in group if isinstance(s, dict) and "source_id" in s}
    obs = getattr(shared, "obs", None)
    observations = {} if obs is None or "observation_id" not in obs else {str(r["observation_id"]): r for r in obs.to_dict("records")}
    evidence, series = [], defaultdict(list)
    for item in raw.get("evidence", []):
        label, eid = str(item.get("label", "")), str(item.get("id", ""))
        sid = str(item.get("source_id", ""))
        source = {**sources.get(sid, {}), **_provenance().get(sid, {})}
        record = observations.get(eid)
        passage = getattr(shared, "passages_by_id", {}).get(eid, {})
        if not isinstance(passage, dict):
            passage = vars(passage) if hasattr(passage, "__dict__") else {}
        fallback = {"document_title": item.get("title"), "publication_date": item.get("date"), "release_stage": item.get("stage"), "locator": item.get("locator")}
        passage = {**{k: v for k, v in fallback.items() if v}, **{k: v for k, v in passage.items() if v}}
        metadata = record if record is not None else passage
        card = {"label": label, "kind": "statistic" if record is not None else ("calculation" if label.startswith("C") else "report"),
                "source_title": source.get("title", metadata.get("document_title", sid)), "publisher": source.get("publisher", "Ministry of Manpower"),
                "date": str(metadata.get("publication_date", source.get("publication_date", ""))), "release_stage": metadata.get("release_stage", source.get("release_stage", "")),
                "locator": metadata.get("locator", metadata.get("period", "")), "url": _safe_url(source.get("canonical_url", source.get("url", source.get("landing_url", ""))))}
        # A report excerpt must be both cited and an actual substring of fetched evidence.
        text = str(raw.get("evidence_text", {}).get(label, ""))
        card["quotes"] = list(dict.fromkeys(q for q in quotes[label] if q and quote_in(q, text)))
        if record is not None:
            for key in ("unit", "indicator_id", "population", "adjustment", "dimension", "period", "missing_reason", "source_locator"):
                if key in record and isinstance(record[key], str):
                    card[key] = record[key]
            value = record.get("value")
            card["value"] = float(value) if value is not None and math.isfinite(float(value)) else None
        elif label.startswith("C") and eid.startswith("calc:"):
            # Derived evidence is not a publisher release. Only project input locators
            # actually present in the deterministic calculation's own evidence text.
            card.update(source_title=f"Calculation on {source.get('title', sid)}", date="", release_stage="calculated", locator="")
            inputs = re.search(r"\bInputs (O\d+) \((\d{4}-Q[1-4])\) and (O\d+) \((\d{4}-Q[1-4])\)\.$", text)
            if inputs:
                a, period_a, b, period_b = inputs.groups()
                card["locator"] = f"{a} ({period_a}) → {b} ({period_b})"
        evidence.append(card)
        if record is not None and label.startswith("O"):
            val = record.get("value")
            if val is not None and math.isfinite(float(val)):
                key = (sid, record.get("indicator_id", ""), record.get("dimension", ""), record.get("population", ""), record.get("adjustment", ""), record.get("unit", ""))
                series[key].append({"period": record["period"], "value": float(val), "observation_id": eid})
    chart = {"series": [{"source_id": k[0], "label": " / ".join(str(v) for v in k[1:5] if v), "unit": k[5], "points": sorted(v, key=lambda p: p["period"])} for k, v in series.items()]}
    trace = [public_trace_item(e) for e in raw.get("trace", [])]
    shown = {c["label"] for c in evidence}
    for event in trace:
        labels = event["detail"].get("new_items")
        if isinstance(labels, list) and any(str(x) not in shown for x in labels):
            kept = [x for x in labels if str(x) in shown]
            event["detail"]["new_items"] = kept
            event["detail"]["unused_items"] = len(labels) - len(kept)  # retrieved but never in the answer context: counted, not listed as sources
    reports = [c for c in evidence if c["kind"] == "report"]
    counts = raw.get("evidence_counts") if isinstance(raw.get("evidence_counts"), dict) else {}
    used = len(reports)
    retrieved = max(used, int(counts.get("retrieved_passages", used))) if isinstance(counts.get("retrieved_passages", used), int) else used
    over = len(counts.get("unused_labels", [])) if isinstance(counts.get("unused_labels"), list) else retrieved - used
    evidence_summary = {"retrieved_passages": retrieved, "used_passages": used, "over_limit_labels": over, "text": f"{retrieved} retrieved, {used} used"}
    groups: dict[tuple, dict] = {}
    for c in reports:
        group = groups.setdefault((c["source_title"], c["locator"]), {"source_title": c["source_title"], "locator": c["locator"], "date": c["date"], "release_stage": c["release_stage"], "url": c["url"], "labels": []})
        group["labels"].append(c["label"])
    evidence_sources = [{**g, "count": len(g["labels"]),
                         "text": f"{g['source_title']}{', ' + g['locator'] if g['locator'] else ''} ({len(g['labels'])} passage{'' if len(g['labels']) == 1 else 's'})"} for g in groups.values()]
    usage = {"cost_usd": raw.get("usage", {}).get("cost_usd", 0), "seconds": raw.get("seconds", 0)}
    for key in ("prompt_tokens", "completion_tokens"):
        value = raw.get("usage", {}).get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            usage[key] = value
    result = {"run_id": raw.get("run_id", ""), "answer": answer, "evidence": evidence, "evidence_summary": evidence_summary, "evidence_sources": evidence_sources, "chart": chart, "trace": trace, "usage": usage}
    interpreted = raw.get("interpreted_as")
    if isinstance(interpreted, str) and interpreted.strip():
        result["interpreted_as"] = interpreted[:300]
    return result

# Fixed, read-only example calls for the workbench MCP tab. Never free-form tool names or arguments.
MCP_REPLY_CHARS = 8000
MCP_EXAMPLES = {
    "latest_resident_unemployment": {"label": "Latest resident unemployment", "tool": "latest_value", "arguments": {"source_id": "resident_unemployment_rate"}},
    "retrenched_2025q1_to_2026q1": {"label": "Retrenched employees, 2025-Q1 to 2026-Q1", "tool": "get_statistic",
                                    "arguments": {"source_id": "retrenched_employees", "period_from": "2025-Q1", "period_to": "2026-Q1"}},
    "list_datasets": {"label": "List datasets", "tool": "list_datasets", "arguments": {}},
}


def create_app(settings: Settings | None = None, runner=None, shared_factory=None):
    cfg = settings or Settings.from_env()
    injected_runner = runner is not None
    if runner is None:
        from labourlens.agent.served import SHIPPED_PROMPTS, make_runner, shipped_config

        # D-077, D-078: the shipped prompts (2020-Q1 window) and the native function-calling planner. Not the evaluated configuration.
        runner = make_runner(shipped_config(cfg.run_deadline_s), contextualise_enabled=cfg.contextualise_enabled, triage_enabled=cfg.triage_enabled,
                             triage_prompt=SHIPPED_PROMPTS["triage"], contextualise_prompt=SHIPPED_PROMPTS["contextualise"])
    if shared_factory is None:
        from labourlens.agent.served import make_shared

        shared_factory = lambda: make_shared(cfg.tool_transport)
    counters = defaultdict(deque)
    tasks = set()
    budget_file = cfg.feedback_dir / "budget.json"
    sessions = {}
    login_failures = defaultdict(deque)  # per client address, monotonic times of recent failed codes
    global_failures = deque()
    session_runs = defaultdict(lambda: deque(maxlen=50))  # run ids produced for each session; feedback must match one

    def persist_budget():
        try:
            cfg.feedback_dir.mkdir(parents=True, exist_ok=True)
            temporary = budget_file.with_suffix(".tmp")
            temporary.write_text(json.dumps({"day": str(app.state.day), "spent_usd": app.state.spent_usd}))
            temporary.replace(budget_file)
        except Exception:
            app.state.spent_usd = cfg.daily_budget_usd
            raise HTTPException(503, "Budget ledger unavailable.")

    @asynccontextmanager
    async def lifespan(app):
        if cfg.demo_enabled and not cfg.enabled:
            logging.getLogger(__name__).warning("Live demo disabled: require a session secret >=32 characters and every access code >=16 characters.")
        app.state.shared = shared_factory() if cfg.enabled else None
        if cfg.enabled and budget_file.exists():
            try:
                saved = json.loads(budget_file.read_text())
                if saved.get("day") == str(date.today()):
                    app.state.spent_usd = float(saved["spent_usd"])
                    if not math.isfinite(app.state.spent_usd) or app.state.spent_usd < 0:
                        app.state.spent_usd = cfg.daily_budget_usd
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                # An unreadable ledger must not silently reset the spend limit.
                app.state.spent_usd = cfg.daily_budget_usd
        yield
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.spent_usd = 0.0
    app.state.day = date.today()
    app.state.active = 0

    def hit(key, limit):
        now = time.monotonic()
        for stale in [k for k, q in counters.items() if not q or q[-1] <= now - cfg.window_seconds]:
            counters.pop(stale, None)
        q = counters[key]
        while q and q[0] <= now - cfg.window_seconds:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "Request limit reached. Try again later.")
        q.append(now)

    def session(request):
        token = request.cookies.get(COOKIE, "")
        try:
            payload, signature = token.rsplit(".", 1)
            expected = hmac.new(cfg.session_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return None
            sid, expiry = payload.rsplit(":", 1)
            return sid if float(expiry) > time.time() and sessions.get(sid) == float(expiry) else None
        except (ValueError, TypeError):
            return None

    def check_origin(request):
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            raise HTTPException(403, "Request not allowed.")

    def client_host(request):
        return request.client.host if request.client else None

    def authorize(request):
        if not cfg.enabled or os.getenv("LABOURLENS_DEMO_ENABLED", "true").lower() == "false":
            raise HTTPException(503, "Live demo disabled.")
        sid = session(request)
        if not sid:
            raise HTTPException(401, "Sign in to use the live demo.")
        # Browser cross-site requests cannot use the session even if cookie handling changes.
        check_origin(request)
        return sid

    async def body(request):
        try:
            value = await request.json()
        except (ValueError, UnicodeError):
            raise HTTPException(400, "Invalid request.")
        if not isinstance(value, dict):
            raise HTTPException(400, "Invalid request.")
        return value

    @app.middleware("http")
    async def security(request, call_next):
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > cfg.body_limit:
                response = JSONResponse({"detail": "Request too large."}, 413)
                break
        else:
            request._body = bytes(content)
            try:
                response = await call_next(request)
            except Exception:
                response = JSONResponse({"detail": "Service unavailable."}, 500)
        response.headers.update({"Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY", "Permissions-Policy": "camera=(), microphone=(), geolocation=()"})
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            if response.status_code >= 400:
                try:
                    await asyncio.to_thread(web_audit.log_event, "request_rejected", session(request), client_host(request),
                                            {"route": request.url.path, "status": response.status_code,
                                             "reason": getattr(request.state, "reject_reason", None) or {400: "Invalid request.", 413: "Request too large."}.get(response.status_code, "Service error.")})
                except Exception:
                    pass
        return response

    @app.exception_handler(HTTPException)
    async def rejected(request: Request, exc: HTTPException):
        request.state.reject_reason = str(exc.detail)
        return JSONResponse({"detail": exc.detail}, exc.status_code)

    @app.get("/healthz")
    async def healthz():
        # Liveness plus identity: code version and the corpus fingerprint (passage-set hash, passage and chunk counts).
        # No secrets, no cost data, no passage text. Lifespan has finished loading before this answers.
        corpus = getattr(app.state.shared, "corpus", None) if getattr(app.state, "shared", None) is not None else None
        return {"status": "ok", "version": _version(), "corpus": corpus if isinstance(corpus, dict) else None}

    @app.get("/api/status")
    async def status(request: Request):
        return {"enabled": cfg.enabled and os.getenv("LABOURLENS_DEMO_ENABLED", "true").lower() != "false", "authenticated": bool(session(request))}

    @app.post("/api/login")
    async def login(request: Request):
        check_origin(request)
        ip = client_host(request)
        hit(("login", ip), cfg.login_limit)
        now = time.monotonic()
        for stale in [a for a, q in login_failures.items() if not q or q[-1] <= now - 600]:
            login_failures.pop(stale, None)
        for failures in (*login_failures.values(), global_failures):
            while failures and failures[0] <= now - 600:
                failures.popleft()
        if not cfg.enabled:
            raise HTTPException(503, "Live demo disabled.")
        data = await body(request)
        candidate = str(data.get("code", ""))
        # Hash both inputs to a fixed size; always check every configured code.
        matches = [hmac.compare_digest(hashlib.sha256(candidate.encode()).digest(), hashlib.sha256(c.encode()).digest()) for c in cfg.access_codes]
        if not any(matches):
            # The lock is per client address, so one address cannot lock out the others; a valid code is never refused by it.
            locked = len(login_failures.get(ip, ())) >= cfg.login_lock_per_address or len(global_failures) >= cfg.login_lock_global
            login_failures[ip].append(now)
            global_failures.append(now)
            if locked:
                raise HTTPException(429, "Login temporarily locked. Try again later.")
            raise HTTPException(401, "Invalid access code.")
        expiry = int(time.time()) + 28800
        for old in [key for key, end in sessions.items() if end <= time.time()]:
            sessions.pop(old, None)
            session_runs.pop(old, None)
        code_hash = hmac.new(cfg.session_secret.encode(), candidate.encode(), hashlib.sha256).hexdigest()
        sid = secrets.token_urlsafe(24) + "~" + code_hash
        sessions[sid] = expiry
        payload = sid + ":" + str(expiry)
        signature = hmac.new(cfg.session_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        response = JSONResponse({"authenticated": True})
        response.set_cookie(COOKIE, payload + "." + signature, httponly=True, secure=request.url.scheme == "https", samesite="strict", max_age=28800)
        return response
    @app.post("/api/logout")
    async def logout(request: Request):
        check_origin(request)
        sid = session(request)
        sessions.pop(sid, None)
        session_runs.pop(sid, None)
        response = JSONResponse({"authenticated": False})
        response.delete_cookie(COOKIE, httponly=True, secure=request.url.scheme == "https", samesite="strict")
        return response


    async def admit(request):
        """Everything that must pass before a run starts, shared by /api/ask and /api/ask/stream: session, origin, rate limits, request
        shape, daily budget, the concurrency slot and the durable spend reservation. Raises HTTPException; on success the slot and the
        reservation are held and `execute` must run (it releases both). Returns (session id, question, history, reserved day)."""
        sid = authorize(request)
        hit(("session", sid.rsplit("~", 1)[-1]), cfg.session_limit)
        hit(("ip", client_host(request)), cfg.ip_limit)
        data = await body(request)
        question = data.get("question")
        if not isinstance(question, str) or not question.strip() or len(question) > 1000:
            raise HTTPException(422, "Question must contain between 1 and 1000 characters.")
        from labourlens.agent.contextualise import parse_history
        try:
            history = parse_history(data.get("history"))
        except ValueError:
            raise HTTPException(422, "History must be at most 3 turns of bounded question, status and summary text, optionally resolved_question and answer_context.")
        if app.state.day != date.today():
            app.state.day, app.state.spent_usd = date.today(), 0.0
        if app.state.spent_usd + RUN_RESERVATION_USD > cfg.daily_budget_usd:
            raise HTTPException(429, "Daily demo budget reached.")
        if app.state.active >= min(2, cfg.max_concurrent):
            raise HTTPException(503, "Demo busy. Try again shortly.")
        app.state.spent_usd += RUN_RESERVATION_USD
        persist_budget()  # No await between admission, durable reservation and slot acquisition.
        app.state.active += 1
        return sid, question, history, app.state.day

    async def execute(request, sid, question, history, reserved_day, run_state, emit=None):
        """Run one admitted question and return (public payload, JSONResponse of it). `run_state["timed_out"]` is set by the caller when its
        wait ran out; the run is then charged at least the reservation. `emit(event)` receives live progress events when the runner can send them."""
        try:
            context = {"channel": "web", "session": sid, "ip": request.client.host if request.client else None, "extra": {}}
            parameters = inspect.signature(runner).parameters
            kwargs = {"audit": context} if "audit" in parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values()) else {}
            if "history" in parameters:
                kwargs["history"] = history
            if emit is not None and "emit" in parameters:
                kwargs["emit"] = emit
            from labourlens.agent.tools import CALLER_SESSION
            token = CALLER_SESSION.set(sid)  # tags this visitor's MCP lookups; the context is copied into the worker thread by to_thread
            try:
                raw = await runner(question, app.state.shared, **kwargs) if inspect.iscoroutinefunction(runner) else await asyncio.to_thread(runner, question, app.state.shared, **kwargs)
            finally:
                CALLER_SESSION.reset(token)
            if isinstance(raw.get("run_id"), str) and sid in sessions:
                session_runs[sid].append(raw["run_id"])
            if injected_runner:
                web_audit.log_injected_run(raw, question, sid, context["ip"])
            payload = redact_values(public_result(raw, app.state.shared), list(cfg.access_codes) + [cfg.session_secret])
            response = JSONResponse(payload)  # Validate serialization before releasing any reservation.
            cost = float(raw.get("usage", {}).get("cost_usd", 0))
            if not math.isfinite(cost) or cost < 0:
                cost = cfg.daily_budget_usd
            if run_state["timed_out"] or raw.get("outcome") not in ("answered", "abstained", "clarify", "refused"):
                cost = max(RUN_RESERVATION_USD, cost)
            if app.state.day == reserved_day:
                app.state.spent_usd += cost - RUN_RESERVATION_USD
                persist_budget()
            return payload, response
        finally:
            app.state.active -= 1

    def start(coro):
        task = asyncio.create_task(coro)
        tasks.add(task)

        def settled(t):
            tasks.discard(t)
            if not t.cancelled():
                t.exception()  # consume errors from runs that outlive an HTTP timeout
        task.add_done_callback(settled)
        return task

    @app.post("/api/ask")
    async def ask(request: Request):
        sid, question, history, reserved_day = await admit(request)
        run_state = {"timed_out": False}
        task = start(execute(request, sid, question, history, reserved_day, run_state))
        try:
            return (await asyncio.wait_for(asyncio.shield(task), cfg.request_timeout))[1]
        except TimeoutError:
            run_state["timed_out"] = True
            raise HTTPException(504, "Run timed out. Please try again later.")
        except Exception:
            raise HTTPException(503, "Agent unavailable. Please try again later.")

    @app.post("/api/ask/stream")
    async def ask_stream(request: Request):
        """The same run as /api/ask, sent as server-sent events: `status`, `tool` and `trace` events while it runs, then one `result` event whose
        data is exactly the /api/ask response body, or one `error` event. Every refusal (login, origin, limits, budget, request shape) is an
        ordinary HTTP error before the stream opens. No model text is streamed: the answer appears only in `result`, after validation."""
        sid, question, history, reserved_day = await admit(request)
        run_state = {"timed_out": False}
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        secrets_ = list(cfg.access_codes) + [cfg.session_secret]

        def emit(event):  # called from the runner's worker thread
            loop.call_soon_threadsafe(queue.put_nowait, event)

        async def job():
            try:
                payload, _ = await execute(request, sid, question, history, reserved_day, run_state, emit)
                queue.put_nowait({"type": "result", "payload": payload})
            except HTTPException as exc:
                queue.put_nowait({"type": "error", "status": exc.status_code, "detail": str(exc.detail)})
            except Exception:
                queue.put_nowait({"type": "error", "status": 503, "detail": "Agent unavailable. Please try again later."})

        start(job())

        def frame(name, data):
            return f"event: {name}\ndata: {json.dumps(redact_values(data, secrets_), ensure_ascii=False)}\n\n"

        async def events():
            yield frame("status", {"stage": "accepted", "state": "done", "text": "Question accepted."})
            give_up = loop.time() + cfg.request_timeout
            while True:
                left = give_up - loop.time()
                if left <= 0:
                    run_state["timed_out"] = True
                    yield frame("error", {"status": 504, "detail": "Run timed out. Please try again later."})
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), min(left, STREAM_KEEPALIVE_S))
                except TimeoutError:
                    yield ": keepalive\n\n"  # keeps an idle proxy from closing the connection during a long model call
                    continue
                kind = event.get("type")
                if kind == "result":
                    yield frame("result", event["payload"])
                    return
                if kind == "error":
                    yield frame("error", {"status": event["status"], "detail": event["detail"]})
                    return
                mapped = public_event(event)
                if mapped is not None:
                    yield frame(*mapped)

        return StreamingResponse(events(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    def mcp_backend():
        return getattr(app.state.shared, "stats_backend", None)

    @app.get("/api/mcp")
    async def mcp_overview(request: Request):
        """Read-only view of the local MCP server the agent uses: what it offers, what the agent may call, the last calls made."""
        sid = authorize(request)
        hit(("mcp", sid.rsplit("~", 1)[-1]), cfg.session_limit * 6)
        from labourlens.mcp.client import McpClientError
        from labourlens.mcp.server import AGENT_TOOLS, ALL_TOOLS, TOOL_NAME
        backend = mcp_backend()
        out = {"enabled": backend is not None and cfg.mcp_enabled, "connected": False, "message": "", "server": None, "tools": [], "resources": [], "prompts": [],
               "used_by_agent": [], "not_given_to_agent": [], "recent_calls": [], "examples": []}
        if backend is None or not cfg.mcp_enabled:
            out["message"] = "MCP is switched off in this deployment: the agent reads statistics directly from the local table."
            return out
        out["recent_calls"] = [{k: v for k, v in c.items() if k != "session"} for c in list(backend.calls) if c.get("session") == sid][-20:]  # this visitor's lookups only
        routed = getattr(app.state.shared, "mcp_routed", ()) or ()  # what this process really routes over MCP besides get_series (set by make_shared)
        agent_map = {TOOL_NAME: "get_series", "annual_average": "annual_average",
                     **{t: t for t in ("search_reports", "calculate_change") if t in routed}}
        used = list(agent_map)
        out["used_by_agent"] = used
        out["agent_tool_name"] = "get_series"
        out["agent_tools"] = agent_map  # MCP tool name -> the agent tool that calls it
        out["not_given_to_agent"] = [t for t in (*ALL_TOOLS, *(AGENT_TOOLS if routed else ())) if t not in used]
        out["examples"] = [{"id": k, "label": v["label"], "tool": v["tool"], "arguments": v["arguments"]} for k, v in MCP_EXAMPLES.items()]
        out["connected"] = backend.client is not None
        if not out["connected"]:
            out["message"] = "The MCP server is not connected right now. It reconnects on the next lookup."
            return out
        try:
            found = await asyncio.to_thread(backend.describe)
        except (McpClientError, TimeoutError, OSError, RuntimeError, asyncio.TimeoutError) as e:
            out["connected"] = False
            out["message"] = f"The MCP server did not answer discovery ({type(e).__name__})."
            return out
        except Exception as e:  # noqa: BLE001 - this view must never turn a broken server into a 500
            logging.getLogger(__name__).warning("MCP discovery failed: %s", type(e).__name__)
            out["connected"] = False
            out["message"] = "The MCP server did not answer discovery."
            return out
        out.update(found)
        for tool in out["tools"]:
            tool["used_by_agent"] = tool["name"] in used
        return redact_values(out, list(cfg.access_codes) + [cfg.session_secret])

    @app.post("/api/mcp/try")
    async def mcp_try(request: Request):
        """Run one of a fixed set of read-only example calls through the MCP client. No model call, no cost; counts against the session limit."""
        sid = authorize(request)
        hit(("session", sid.rsplit("~", 1)[-1]), cfg.session_limit)
        hit(("ip", client_host(request)), cfg.ip_limit)
        data = await body(request)
        example = MCP_EXAMPLES.get(data.get("example")) if isinstance(data.get("example"), str) else None
        if example is None:
            raise HTTPException(422, "Unknown example.")
        backend = mcp_backend()
        if backend is None or not cfg.mcp_enabled:
            raise HTTPException(503, "MCP is switched off in this deployment.")
        from labourlens.mcp.client import McpClientError
        t0 = time.perf_counter()
        out = {"tool": example["tool"], "arguments": example["arguments"], "ok": True}
        try:
            from labourlens.agent.tools import CALLER_SESSION

            def run_example():
                CALLER_SESSION.set(sid)  # to_thread runs in a copy of the context, so this does not leak
                return backend.call_tool(example["tool"], **example["arguments"])

            reply = await asyncio.to_thread(run_example)
            out["reply"] = reply.result.model_dump(mode="json")
            out["quarantined"] = reply.quarantined
        except McpClientError as e:
            out.update(ok=False, error={"kind": e.kind, "message": e.message[:300]})
        except Exception as e:  # noqa: BLE001 - a broken server is reported, never a 500
            out.update(ok=False, error={"kind": "unavailable", "message": type(e).__name__})
        out["ms"] = round((time.perf_counter() - t0) * 1000, 1)
        if "reply" in out:
            text = json.dumps(out["reply"], ensure_ascii=False)
            if len(text) > MCP_REPLY_CHARS:
                out["reply"] = {"truncated": True, "shown_characters": MCP_REPLY_CHARS, "total_characters": len(text), "text": text[:MCP_REPLY_CHARS]}
        return redact_values(out, list(cfg.access_codes) + [cfg.session_secret])

    @app.post("/api/feedback")
    async def feedback(request: Request):
        sid = authorize(request)
        hit(("feedback", sid), cfg.session_limit)
        data = await body(request)
        if data.get("rating") not in ("up", "down") or not isinstance(data.get("comment", ""), str) or len(data.get("comment", "")) > 1000:
            raise HTTPException(422, "Invalid feedback.")
        comment = re.sub(r"<[^>]*>", "", data.get("comment", ""))
        comment = "".join(c for c in comment if c.isprintable() or c in "\n\t")
        run_id = data.get("run_id")
        tags = data.get("tags", [])
        if not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{12}", run_id) or not isinstance(tags, list) or len(tags) > 4 or any(not isinstance(tag, str) or tag not in {"wrong_number", "wrong_source", "missing_info", "other"} for tag in tags):
            raise HTTPException(422, "Invalid feedback.")
        if run_id not in session_runs.get(sid, ()):
            raise HTTPException(404, "Unknown run for this session.")  # feedback attaches only to runs this session started
        try:
            audit_log.log_feedback(run_id, data["rating"], redact(comment, list(cfg.access_codes) + [cfg.session_secret]), sid, tags)
        except Exception:
            pass
        return {"saved": True}

    root = paths.ROOT / "web"
    if (root / "static").exists():
        app.mount("/static", StaticFiles(directory=root / "static"), name="static")
    @app.get("/")
    async def index():
        return FileResponse(root / "index.html")
    @app.get("/deck")
    @app.get("/deck.html")
    async def deck():
        return FileResponse(root / "deck.html")
    @app.get("/innovation")
    async def innovation():
        return FileResponse(root / "innovation.html")
    @app.get("/presentation")
    async def presentation():
        return RedirectResponse("/deck", status_code=307)
    @app.get("/workbench")
    @app.get("/workbench.html")
    async def workbench():
        return FileResponse(root / "workbench.html")
    return app
