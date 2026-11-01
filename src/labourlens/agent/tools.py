"""Typed, read-only agent tools (ADR-002 item 4, approved set of three): search_reports, get_series, calculate_change.
An optional fourth tool, calculate_from_text_values (tool set "v2", D-046), does the same exact arithmetic on figures that
appear in report passages.

Every tool validates its arguments, returns evidence items with provenance, and never raises for bad input: it returns a
ToolResult with an error kind the graph can route on. Arithmetic is deterministic (Decimal). calculate_change only accepts
observation labels that get_series returned in the same run, so a model cannot calculate on a number it invented;
calculate_from_text_values only accepts a figure that is verifiably present in the cited passage text of the same run.
"""

from __future__ import annotations

import contextvars
import hashlib
import re
import time
import unicodedata
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from labourlens import paths
from labourlens.answer.context import ContextPassage
from labourlens.data import catalog
from labourlens.security.guards import injection_flags, sanitize_text

SCOPE_LO, SCOPE_HI = catalog.ANSWER_SCOPE_START, catalog.ANSWER_SCOPE_END
MAX_NOTES = 8
# Set by the web layer around one visitor's request so the MCP client's call log can be filtered per visitor. Never returned to a browser.
CALLER_SESSION: contextvars.ContextVar[str | None] = contextvars.ContextVar("labourlens_caller_session", default=None)
RELEASE_ID = re.compile(r"^mom-(\d{4})-q([1-4])-(advance|final.*)$")
PERIOD = re.compile(r"^(\d{4})-Q([1-4])$")
MAX_QUERY_CHARS = 300
MAX_K = 10
MAX_ROWS = 40
ADJUSTMENTS = ("seasonally_adjusted", "not_adjusted", "unspecified", "not_applicable")
CHANGE_KINDS = ("difference", "percent_change")
TOOL_SETS = ("base", "v2")
TEXT_UNITS = ("percent", "persons", "dollars", "ratio", "vacancies")
TEXT_CALC_ARGS = ("passage_a", "value_a", "unit_a", "basis_a", "period_a", "passage_b", "value_b", "unit_b", "basis_b", "period_b", "kind")
TEXT_CALC_REQUIRED = ("passage_a", "value_a", "unit_a", "basis_a", "period_a", "passage_b", "value_b", "unit_b", "basis_b", "period_b")
_FREE = re.compile(r"^[\w\s,.;:()/%'\-]+$")
_VALUE = re.compile(r"^-?\d+(?:\.\d+)?$")
_NUMBER_IN_TEXT = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
_UNKNOWN_DIMENSION = re.compile(r"^dimension '.*' not found in ")
MAX_SNIPPETS = 5


class TransientToolError(Exception):
    """A recoverable failure (timeout, temporary resource problem). The graph retries once."""


@dataclass
class ToolResult:
    ok: bool
    items: list[ContextPassage] = field(default_factory=list)
    message: str = ""  # short, safe summary shown to the planner (no passage text)
    error_kind: str | None = None  # invalid_arguments | not_found | too_large
    retrieval_trace: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


class StatsData:
    """Read-only statistics: the observations table and the series query. No retriever and no API key, so the MCP server
    process can run with a minimal environment (least privilege)."""

    def __init__(self, observations: pd.DataFrame | None = None) -> None:
        o = observations if observations is not None else pd.read_parquet(paths.PROCESSED / "observations.parquet")
        self.obs = o[o.in_answer_scope].reset_index(drop=True)
        self.titles = {d["source_id"]: d["title"] for d in catalog.datasets()}

    def catalogue_text(self) -> str:
        lines = []
        for sid, g in self.obs.groupby("source_id"):
            meas = sorted({(r.indicator_id, r.unit, r.population, r.adjustment) for r in g.itertuples()})
            dims = g.dimension.replace("", pd.NA).dropna().nunique()
            m = "; ".join(f"{i} [{u}, {p}, {a}]" for i, u, p, a in meas)
            lines.append(f"- {sid}: {self.titles.get(sid, sid)}. Series: {m}." + (f" Has {dims} dimension values (industry, occupation or sector)." if dims else ""))
        return "\n".join(lines)

    def query(self, source_id: str, period_from: str, period_to: str, dimension: str | None = None,
              adjustment: str | None = None, indicator_id: str | None = None) -> tuple[list[dict] | None, ToolResult | None]:
        """Validated lookup. Returns (rows, None) or (None, error ToolResult). Rows carry provenance and a display string."""
        o = self.obs
        if source_id not in set(o.source_id):
            return None, ToolResult(False, message=f"unknown source_id {source_id!r}; valid: {sorted(set(o.source_id))}", error_kind="not_found")
        for p in (period_from, period_to):
            if not PERIOD.match(p or ""):
                return None, ToolResult(False, message=f"period {p!r} must look like 2026-Q2", error_kind="invalid_arguments")
        if _q(period_from) > _q(period_to):
            return None, ToolResult(False, message="period_from is after period_to", error_kind="invalid_arguments")
        if _q(period_from) < _q(SCOPE_LO) or _q(period_to) > _q(SCOPE_HI):
            return None, ToolResult(False, message=f"supported periods are {SCOPE_LO} to {SCOPE_HI}", error_kind="invalid_arguments")
        if adjustment is not None and adjustment not in ADJUSTMENTS:
            return None, ToolResult(False, message=f"adjustment must be one of {ADJUSTMENTS} or null", error_kind="invalid_arguments")
        g = o[(o.source_id == source_id)]
        if indicator_id:
            g = g[g.indicator_id == indicator_id]
        if adjustment:
            g = g[g.adjustment == adjustment]
        if dimension:
            names = sorted(set(g.dimension))
            hit = [n for n in names if n.casefold() == dimension.casefold()]
            if not hit:
                return None, ToolResult(False, message=f"dimension {dimension!r} not found in {source_id}; available: {names[:40]}", error_kind="not_found")
            g = g[g.dimension == hit[0]]
        g = g[(g.period >= period_from) & (g.period <= period_to)]
        if g.empty:
            return None, ToolResult(False, message="no rows match these filters", error_kind="not_found")
        if len(g) > MAX_ROWS:
            dims = sorted(set(g.dimension))
            return None, ToolResult(False, message=f"{len(g)} rows is more than {MAX_ROWS}; set `dimension` (available: {dims[:40]}) or narrow the periods", error_kind="too_large")
        g = g.sort_values(["indicator_id", "population", "adjustment", "dimension", "period"])
        rows = []
        for r in g.itertuples():
            disp = _fmt(r.value, r.unit) if pd.notna(r.value) else f"no published number ({r.missing_reason})"
            rows.append({"observation_id": r.observation_id, "source_id": source_id, "title": self.titles[source_id], "indicator_id": r.indicator_id,
                         "dimension": r.dimension, "period": r.period, "population": r.population, "adjustment": r.adjustment, "unit": r.unit,
                         "value": None if pd.isna(r.value) else float(r.value), "display": disp, "release_stage": r.release_stage})
        return rows, None


class Shared:
    """Read-only data shared by all runs: retriever, passages and the statistics data."""

    def __init__(self, world=None, observations: pd.DataFrame | None = None, stats=None, retrieval: str = "hybrid") -> None:
        from labourlens.retrieval.runtime import load_world

        self.retrieval = retrieval
        self.retriever, self.chunks_by_id, self.passages_by_id = world or load_world()
        from labourlens.retrieval.runtime import corpus_fingerprint

        self.corpus = corpus_fingerprint(self.passages_by_id, self.chunks_by_id)
        self.stats = stats or StatsData(observations)
        self.obs, self.titles = self.stats.obs, self.stats.titles
        # Optional replacement for the direct statistics lookup, e.g. an MCP client. Same contract as StatsData.query.
        self.stats_backend = None

    def catalogue_text(self) -> str:
        return self.stats.catalogue_text()


def is_unknown_dimension(res: ToolResult | None) -> bool:
    """True for the get_series error 'dimension ... not found in ...' from either statistics backend (direct or MCP)."""
    return res is not None and not res.ok and res.error_kind == "not_found" and bool(_UNKNOWN_DIMENSION.match(res.message or ""))


def _signed_numbers(text: str) -> set[Decimal]:
    """Every number in `text` as a Decimal, thousands separators removed. A minus sign counts only when it directly precedes
    the digits and follows a space, an opening bracket or the start of the text (so 2024-2025 is not read as -2025)."""
    t = unicodedata.normalize("NFKC", text)
    out: set[Decimal] = set()
    for m in _NUMBER_IN_TEXT.finditer(t):
        s = m.start()
        if s and t[s - 1] in ".,0123456789":
            continue  # tail of a longer token such as 1.2.3
        v = Decimal(m.group().replace(",", ""))
        negative = s >= 1 and t[s - 1] in "-\u2212\u2013" and (s == 1 or t[s - 2].isspace() or t[s - 2] == "(")
        out.add(-v if negative else v)
    return out


def figure_snippets(text: str, limit: int = MAX_SNIPPETS, before: int = 7, after: int = 4) -> list[str]:
    """Short word windows around the figures of a passage (decimals, comma-grouped numbers, integers of 100 or more, or any
    number followed by %). Shown to the planner of tool set v2 so it can pick a figure for calculate_from_text_values; the
    tool re-checks every chosen value against the full passage, so a snippet is a convenience, never a trust boundary."""
    words = sanitize_text(" ".join(text.split())).split(" ")
    out: list[str] = []
    last = -1
    for i, w in enumerate(words):
        if len(out) >= limit:
            break
        m = re.fullmatch(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(%?)", w.strip("()[]\"';:,").rstrip("."))
        if not m or i <= last:
            continue
        num, pct = m.groups()
        if not (pct or "." in num or "," in num or int(num) >= 100) or (re.fullmatch(r"(19|20)\d\d", num) and not pct):
            continue
        lo, hi = max(0, i - before), min(len(words), i + after + 1)
        out.append(" ".join(words[lo:hi]))
        last = hi - 1
    return out


def _fmt(value: float, unit: str) -> str:
    v = Decimal(str(round(value, 6))).normalize()
    s = f"{v:,.2f}".rstrip("0").rstrip(".") if v != v.to_integral() else f"{int(v):,}"
    return {"percent": f"{s}%", "persons": f"{s} persons", "ratio": f"{s} (ratio)"}.get(unit, f"{s} {unit}")


def _q(period: str) -> tuple[int, int]:
    m = PERIOD.match(period)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def compute_change(value_a: float, value_b: float, kind: str, unit: str) -> tuple[Decimal, str, str, str]:
    """Pure, deterministic change from value_a to value_b (Decimal arithmetic, rounded half-up to 2 places).

    kind "difference": value_b - value_a, in `unit` (percentage points when the series unit is percent).
    kind "percent_change": (value_b - value_a) / value_a * 100, in percent; raises ZeroDivisionError when value_a is 0.
    Returns (result, result as a plain string, unit label, formula). Shared by the agent's calculate_change and the MCP compare_periods."""
    va, vb = Decimal(str(value_a)).normalize(), Decimal(str(value_b)).normalize()
    if kind == "difference":
        res, label = vb - va, ("percentage points" if unit == "percent" else unit)
        formula = f"{vb:f} - {va:f}"
    else:
        if va == 0:
            raise ZeroDivisionError("percent change from zero is undefined")
        res, label = (vb - va) / va * 100, "percent"
        formula = f"({vb:f} - {va:f}) / {va:f} * 100"
    res = res.quantize(Decimal("0.01"), ROUND_HALF_UP).normalize()
    return res, f"{res:f}", label, formula


class Tools:
    """One instance per agent run: holds the evidence registries for that run."""

    def __init__(self, shared: Shared, retrieval: str | None = None, question: str = "", tool_timeout_s: float = 10.0) -> None:
        self.sh = shared
        self.retrieval = retrieval or getattr(shared, "retrieval", "hybrid")
        if self.retrieval not in ("hybrid", "r3", "r3w"):
            raise ValueError("retrieval must be hybrid, r3 or r3w")
        self.question, self.tool_timeout_s = question, tool_timeout_s
        self.caller = CALLER_SESSION.get()  # visitor tag of the web request that started this run (None outside the web app); only labels MCP call-log entries
        self.tool_set = "base"  # "v2" enables calculate_from_text_values and the actionable unknown-dimension error (set by build_graph)
        self.items: list[ContextPassage] = []
        self._ids: set[str] = set()
        self._obs: dict[str, dict] = {}  # label -> observation facts, for calculate_change
        self._n = {"P": 0, "O": 0, "C": 0}
        # Deterministic data-quality notes about missing data and conflicting versions. Written by code, not by a model,
        # and shown to the answer step next to the evidence (never citeable themselves).
        self.notes: list[str] = []

    def fork(self) -> Tools:
        """Isolate a tool invocation; only an on-time completion may be committed."""
        import copy

        child = copy.copy(self)
        child.items = list(self.items)
        child._ids = set(self._ids)
        child._obs = {k: dict(v) for k, v in self._obs.items()}
        child._n = dict(self._n)
        child.notes = list(self.notes)
        return child

    def commit(self, child: Tools) -> None:
        self.items, self._ids, self._obs = child.items, child._ids, child._obs
        self._n, self.notes = child._n, child.notes

    def _note(self, text: str) -> None:
        if text not in self.notes and len(self.notes) < MAX_NOTES:
            self.notes.append(text)

    def _vintage_note(self, source_id: str) -> None:
        """Advance and final releases of the same quarter in one evidence set: flag that the final supersedes."""
        m = RELEASE_ID.match(source_id)
        if not m:
            return
        year, q, kind = m.group(1), m.group(2), "advance" if m.group(3) == "advance" else "final"
        other = "final" if kind == "advance" else "advance"
        for it in self.items:
            m2 = RELEASE_ID.match(it.source_id)
            if m2 and m2.group(1) == year and m2.group(2) == q and ("advance" if m2.group(3) == "advance" else "final") == other:
                self._note(f"Evidence contains both the advance and the final MOM release for {year}-Q{q}. Figures may differ; the final release supersedes the advance one. State which release each figure comes from and report any difference.")
                return

    def _coverage_notes(self, rows: list[dict], period_from: str, period_to: str, quarantined: int = 0) -> None:
        expected = [f"{y}-Q{q}" for y in range(_q(period_from)[0], _q(period_to)[0] + 1) for q in range(1, 5) if _q(period_from) <= (y, q) <= _q(period_to)]
        series: dict[tuple, dict[str, dict]] = {}
        for r in rows:
            series.setdefault((r["indicator_id"], r["population"], r["adjustment"], r["dimension"]), {})[r["period"]] = r
        for (ind, pop, adj, dim), by_period in series.items():
            label = f"{rows[0]['title']} ({ind}, {dim or 'all'}, {pop}, {adj})"
            nulls = sorted(p for p, r in by_period.items() if r["value"] is None)
            absent = [p for p in expected if p not in by_period]
            if nulls:
                self._note(f"{label}: no published number for {', '.join(nulls)} (the source marks it unavailable). Do not estimate it.")
            if absent and quarantined:
                self._note(f"{label}: no usable row for {', '.join(absent)}. {quarantined} row(s) of this reply were withheld by the MCP client "
                           "as unsafe, so the figure is unavailable because of a service/security event, not because the dataset lacks it. Do not estimate it.")
            elif absent:
                self._note(f"{label}: the dataset has no row for {', '.join(absent)}. Do not estimate it.")
        if len({(r["indicator_id"], r["population"], r["adjustment"]) for r in rows}) > 1:
            self._note("The statistics returned for one request contain more than one series (different indicator, population or adjustment). Never mix them; say which series each figure belongs to.")
        if any("prelim" in (r["release_stage"] or "") or r["release_stage"] == "advance" for r in rows):
            self._note("Some statistics are preliminary or advance figures and may be revised; say so.")

    def _label(self, kind: str) -> str:
        self._n[kind] += 1
        return f"{kind}{self._n[kind]}"

    def _add(self, kind: str, item_id: str, source_id: str, title: str, published, stage: str, locator: str, text: str) -> ContextPassage | None:
        if item_id in self._ids:
            return None
        self._ids.add(item_id)
        text = sanitize_text(text)
        it = ContextPassage(self._label(kind), item_id, source_id, title, published, stage, locator, text, tuple(injection_flags(text)))
        self.items.append(it)
        if kind == "P":
            self._vintage_note(source_id)
        return it

    # ---- search_reports -------------------------------------------------------------------------------------------
    def _search(self, query: str, k: int) -> tuple[list, dict, dict]:
        """Union the planner-query and original-question period/stage hints.

        Quarters are unioned; conflicting stages disable the stage restriction.
        R3w widens when fewer than 8 fused chunks survive or the best filtered
        BM25 score is below 0.5 times the unfiltered best positive BM25 score.
        These fixed thresholds were not tuned on dev cases. Default uses the old path.
        """
        if self.retrieval == "hybrid":
            return self.sh.retriever.search(query, k), {}, {}
        from labourlens.retrieval import dense, period, rerank

        started = time.perf_counter()
        a, b = period.parse(query), period.parse(self.question)
        stages = {h.stage for h in (a, b) if h.stage}
        conflict = a.stage_conflict or b.stage_conflict or len(stages) > 1
        hints = period.Hints(a.quarters | b.quarters, next(iter(stages)) if stages and not conflict else None, conflict)
        allowed = period.matching_sources(hints)
        retr, chunks = self.sh.retriever, self.sh.chunks_by_id
        n = len(chunks)
        bm = retr.bm25.search(query, n if allowed else retr.depth)
        de = retr.dense.search(query, n if allowed else retr.depth)
        filtered_bm = [x for x in bm if chunks[x[0]].source_id in allowed] if allowed else bm
        filtered_de = [x for x in de if chunks[x[0]].source_id in allowed] if allowed else de
        ranked = dense.rrf([filtered_bm[:retr.depth], filtered_de[:retr.depth]], n, retr.c)
        trace = {"retrieval": self.retrieval,
                 "hints": {"quarters": [f"{y}-Q{q}" for y, q in sorted(hints.quarters)], "stage": hints.stage, "stage_conflict": conflict},
                 "filter_applied": allowed is not None,
                 "filtered_documents": len({chunks[cid].source_id for cid, _ in filtered_bm + filtered_de}),
                 "filtered_chunks": len(ranked), "widened": False,
                 "reranked": False, "rerank_fallback": False, "rerank_seconds": 0.0, "rerank_cost_usd": 0.0}
        if self.retrieval == "r3w" and allowed and (
            len(ranked) < 8 or (bm and bm[0][1] > 0 and (not filtered_bm or filtered_bm[0][1] < 0.5 * bm[0][1]))
        ):
            # Search BM25 at its original depth: tied scores can depend on requested k.
            ranked = dense.rrf([retr.bm25.search(query, retr.depth), de[:retr.depth]], n, retr.c)
            trace["widened"] = True
        usage = {}
        if ranked:
            t0 = time.perf_counter()
            try:
                remaining = self.tool_timeout_s - (t0 - started) - 0.25
                if remaining <= 0:
                    raise TimeoutError("retrieval exhausted tool budget")
                result = rerank.rerank(query, [chunks[cid] for cid, _ in ranked[:rerank.POOL]],
                                       model=rerank.MODEL, use_cache=False, timeout_s=remaining)
                trace.update(reranked=result.ok, rerank_fallback=not result.ok, rerank_cost_usd=result.cost_usd)
                if result.ok:
                    ranked = [ranked[i] for i in result.order] + ranked[rerank.POOL:]
                usage = {"calls": 1, "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
                         "cost_usd": result.cost_usd, "llm_seconds": result.seconds}
            except Exception:
                # Failed/expired rerank never converts available evidence to a tool failure.
                trace["rerank_fallback"] = True
            trace["rerank_seconds"] = round(time.perf_counter() - t0, 3)
        return ranked[:k], trace, usage

    def search_reports(self, query: str, k: int = 8) -> ToolResult:
        q = (query or "").strip()
        if not q or len(q) > MAX_QUERY_CHARS:
            return ToolResult(False, message=f"query must be 1 to {MAX_QUERY_CHARS} characters", error_kind="invalid_arguments")
        if not isinstance(k, int) or not 1 <= k <= MAX_K:
            return ToolResult(False, message=f"k must be an integer from 1 to {MAX_K}", error_kind="invalid_arguments")
        new = []
        ranked, retrieval_trace, usage = self._search(q, k)
        for cid, _ in ranked:
            for pid in self.sh.chunks_by_id[cid].source_passage_ids:
                p = self.sh.passages_by_id.get(pid)
                if p:
                    it = self._add("P", pid, p["source_id"], p["document_title"], p["publication_date"], p["release_stage"], p["locator"], p["text"])
                    if it:
                        new.append(it)
        return ToolResult(True, new, f"{len(new)} new passages from {len({i.source_id for i in new})} documents: " + ", ".join(f"{i.label}={i.source_id}" for i in new[:12]),
                          retrieval_trace=retrieval_trace, usage=usage)

    # ---- get_series -----------------------------------------------------------------------------------------------
    def get_series(self, source_id: str, period_from: str, period_to: str, dimension: str | None = None,
                   adjustment: str | None = None, indicator_id: str | None = None) -> ToolResult:
        backend = self.sh.stats_backend or self.sh.stats
        token = CALLER_SESSION.set(self.caller)  # this runs in a pool thread that does not inherit the request context; re-attach the run's visitor tag
        try:
            rows, err = backend.query(source_id, period_from, period_to, dimension, adjustment, indicator_id)
        finally:
            CALLER_SESSION.reset(token)
        if err is not None:
            return self._dimension_help(err, source_id, dimension, adjustment, indicator_id) if self.tool_set == "v2" and is_unknown_dimension(err) else err
        new = []
        for r in rows:
            text = (f"{r['title']} | {r['indicator_id']} | {r['dimension'] or 'all'} | {r['period']} | "
                    f"{r['population']}, {r['adjustment']} | {r['display']} | release stage: {r['release_stage']}")
            it = self._add("O", r["observation_id"], r["source_id"], r["title"], None, r["release_stage"], f"observation {r['observation_id']}", text)
            if it:
                self._obs[it.label] = {"label": it.label, "id": r["observation_id"], "source_id": r["source_id"], "indicator_id": r["indicator_id"],
                                       "population": r["population"], "adjustment": r["adjustment"], "dimension": r["dimension"], "unit": r["unit"],
                                       "period": r["period"], "value": r["value"]}
                new.append(it)
        quarantined = getattr(rows, "quarantined", 0)
        if quarantined and not rows:
            self._note(f"{quarantined} row(s) of this statistics reply were withheld by the MCP client as unsafe; none remain. "
                       "The figures are unavailable because of a service/security event, not because the dataset lacks them. Do not estimate them.")
        self._coverage_notes(rows, period_from, period_to, quarantined)
        shown = f"{len(new)} new observations: " + ", ".join(f"{i.label}={self._obs[i.label]['period']}" for i in new[:20])
        return ToolResult(True, new, shown + (f" ({quarantined} quarantined by the MCP client)" if quarantined else ""))

    def _dimension_help(self, err: ToolResult, source_id: str, dimension: str, adjustment: str | None, indicator_id: str | None) -> ToolResult:
        """Replace the unknown-dimension error by one that lists the valid labels of that series, closest first. The labels come
        from the local read-only observations table, so the list is complete even when the statistics backend truncates messages."""
        import difflib

        o = self.sh.obs
        g = o[o.source_id == source_id]
        if indicator_id:
            g = g[g.indicator_id == indicator_id]
        if adjustment:
            g = g[g.adjustment == adjustment]
        names = sorted({n for n in g.dimension if n})
        if not names:
            return ToolResult(False, message=f"dimension {dimension!r} not found in {source_id}: this series has no dimension values; leave dimension null.", error_kind="not_found")
        by_fold = {n.casefold(): n for n in names}
        close = [by_fold[c] for c in difflib.get_close_matches(dimension.casefold(), list(by_fold), n=5, cutoff=0.4)]
        listing = f"closest: {close}; " if close else ""
        msg = (f"dimension {dimension!r} not found in {source_id}. Retry get_series with exactly one of the {len(names)} valid labels "
               f"(case-insensitive): {listing}all: {names[:80]}. This retry does not use up an evidence round.")
        return ToolResult(False, message=msg[:1800], error_kind="not_found")

    # ---- calculate_change -----------------------------------------------------------------------------------------
    def calculate_change(self, obs_a: str, obs_b: str, kind: str = "difference") -> ToolResult:
        if kind not in CHANGE_KINDS:
            return ToolResult(False, message=f"kind must be one of {CHANGE_KINDS}", error_kind="invalid_arguments")
        a, b = self._obs.get(obs_a), self._obs.get(obs_b)
        if a is None or b is None:
            return ToolResult(False, message="obs_a and obs_b must be observation labels returned by get_series in this run", error_kind="invalid_arguments")
        same = [k for k in ("source_id", "indicator_id", "population", "adjustment", "dimension", "unit") if a[k] != b[k]]
        if same:
            return ToolResult(False, message=f"observations are different series (differ in {same}); a change is only defined within one series", error_kind="invalid_arguments")
        if a["period"] == b["period"]:
            return ToolResult(False, message="both observations are the same period", error_kind="invalid_arguments")
        if a["value"] is None or b["value"] is None:
            return ToolResult(False, message="one observation has no published number", error_kind="not_found")
        try:
            res, shown, unit, formula = compute_change(a["value"], b["value"], kind, a["unit"])
        except ZeroDivisionError:
            return ToolResult(False, message="percent change from zero is undefined", error_kind="invalid_arguments")
        cid = "calc:" + hashlib.sha256(f"{a['id']}|{b['id']}|{kind}".encode()).hexdigest()[:12]
        text = (f"Calculated {kind.replace('_', ' ')} of {a['indicator_id']} ({a['dimension'] or 'all'}; {a['population']}, {a['adjustment']}) "
                f"from {a['period']} to {b['period']}: {formula} = {shown} {unit}. Inputs {obs_a} ({a['period']}) and {obs_b} ({b['period']}).")
        it = self._add("C", cid, a["source_id"], f"Calculation on {self.sh.titles[a['source_id']]}", None, "calculated", f"{obs_a},{obs_b}", text)
        if it is None:
            return ToolResult(True, message="this calculation was already done")
        return ToolResult(True, [it], f"{it.label} = {shown} {unit}")

    # ---- calculate_from_text_values (tool set v2) -----------------------------------------------------------------
    def calculate_from_text_values(self, passage_a: str, value_a: str, unit_a: str, basis_a: str, period_a: str,
                                   passage_b: str, value_b: str, unit_b: str, basis_b: str, period_b: str,
                                   kind: str = "difference") -> ToolResult:
        """Exact change from figure A (the earlier or base one) to figure B, both read from report passages of this run.

        Each value must be the figure as a plain number (`2.9`, `-0.3`, `1,250`; no unit, no words) and must occur in the
        text of the cited passage (label P1, P2, ...) after normalisation (thousands separators, trailing zeros). Units and
        bases must be identical. The model never supplies a result: it is computed by compute_change, the function that
        also serves calculate_change, so rounding (half-up, 2 places) and unit labels (percentage points for percent) match."""
        if kind not in CHANGE_KINDS:
            return ToolResult(False, message=f"kind must be one of {CHANGE_KINDS}", error_kind="invalid_arguments")
        legs = []
        for side, passage, value, unit, basis, period in (("a", passage_a, value_a, unit_a, basis_a, period_a), ("b", passage_b, value_b, unit_b, basis_b, period_b)):
            item = next((i for i in self.items if i.label == passage and i.label[0] == "P"), None)
            if item is None:
                return ToolResult(False, message=f"passage_{side} {passage!r} must be a passage label (P1, P2, ...) returned by search_reports in this run", error_kind="invalid_arguments")
            if item.flags:
                return ToolResult(False, message=f"passage {passage} is flagged as containing instructions and cannot be used as a source of figures", error_kind="invalid_arguments")
            if unit not in TEXT_UNITS:
                return ToolResult(False, message=f"unit_{side} must be one of {TEXT_UNITS}", error_kind="invalid_arguments")
            text_value = str(value).strip().replace(",", "").replace("\u2212", "-")
            if not _VALUE.match(text_value):
                return ToolResult(False, message=f"value_{side} must be one plain number such as 2.9 or 1250 (no unit, no words)", error_kind="invalid_arguments")
            basis, period = " ".join(str(basis or "").split()), " ".join(str(period or "").split())
            if not 1 <= len(basis) <= 120 or not _FREE.match(basis) or not 1 <= len(period) <= 40 or not _FREE.match(period):
                return ToolResult(False, message=f"basis_{side} (1 to 120 characters) and period_{side} (1 to 40 characters) must be short plain descriptions", error_kind="invalid_arguments")
            number = Decimal(text_value)
            if number not in _signed_numbers(item.text):
                return ToolResult(False, message=f"value_{side} {text_value} does not appear in passage {passage}; copy the figure exactly as the passage prints it", error_kind="invalid_arguments")
            legs.append((item, number, unit, basis, period))
        (ia, va, ua, ba, pa), (ib, vb, ub, bb, pb) = legs
        if ua != ub:
            return ToolResult(False, message=f"unit_a ({ua}) and unit_b ({ub}) differ; a change is only defined between figures in the same unit", error_kind="invalid_arguments")
        if re.sub(r"\W+", " ", ba).strip().casefold() != re.sub(r"\W+", " ", bb).strip().casefold():
            return ToolResult(False, message="basis_a and basis_b differ; a change is only defined between figures of the same measure, population and adjustment. Use identical wording for both", error_kind="invalid_arguments")
        if (ia.passage_id, va) == (ib.passage_id, vb) and pa.casefold() == pb.casefold():
            return ToolResult(False, message="both figures are the same figure from the same passage", error_kind="invalid_arguments")
        try:
            res, shown, unit, formula = compute_change(str(va), str(vb), kind, ua)
        except ZeroDivisionError:
            return ToolResult(False, message="percent change from zero is undefined", error_kind="invalid_arguments")
        cid = "calc:" + hashlib.sha256(f"text|{ia.passage_id}|{va}|{ib.passage_id}|{vb}|{kind}".encode()).hexdigest()[:12]
        text = (f"Calculated {kind.replace('_', ' ')} of {ba} from report figures: {formula} = {shown} {unit}. "
                f"Inputs {ia.label} ({_fmt(float(va), ua)}, {pa}; {ia.source_id}, {ia.stage}) and {ib.label} ({_fmt(float(vb), ua)}, {pb}; {ib.source_id}, {ib.stage}).")
        it = self._add("C", cid, ia.source_id, f"Calculation on {ia.title}", None, "calculated", f"{ia.label},{ib.label}", text)
        if it is None:
            return ToolResult(True, message="this calculation was already done")
        return ToolResult(True, [it], f"{it.label} = {shown} {unit}")
