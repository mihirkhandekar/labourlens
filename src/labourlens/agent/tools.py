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
import functools
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
TOOL_SETS = ("base", "v2", "annual")
BASE_TOOLS = ("search_reports", "get_series", "calculate_change")
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



class _SearchRejected(Exception):
    """Carries the typed ToolResult of a search_reports call the MCP server rejected (invalid arguments), out of _search."""

    def __init__(self, result: "ToolResult") -> None:
        super().__init__(result.message)
        self.result = result


@dataclass
class ToolResult:
    ok: bool
    items: list[ContextPassage] = field(default_factory=list)
    message: str = ""  # short, safe summary shown to the planner (no passage text)
    error_kind: str | None = None  # invalid_arguments | not_found | too_large
    retrieval_trace: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)
    transport: str | None = None  # "mcp" when the call ran on the MCP server; set by Tools, never by a tool's own logic


def _transported(fn):
    """Public tool method: afterwards mark the ToolResult with transport "mcp" if the call used the MCP backend."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        self._mcp_used = False
        res = fn(self, *args, **kwargs)
        if self._mcp_used and isinstance(res, ToolResult):
            res.transport = "mcp"
        return res
    return wrapper


def offered_tools(shared, tool_set: str = "base") -> list[str]:
    """Runtime tool catalogue; experiments may disable tools without changing frozen prompts or live transports."""
    names = BASE_TOOLS + (("calculate_from_text_values",) if tool_set == "v2" else ("annual_average",) if tool_set == "annual" else ())
    disabled = getattr(shared, "disabled_tools", frozenset())
    return [name for name in names if name not in disabled]


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
        in_series = g
        g = g[(g.period >= period_from) & (g.period <= period_to)]
        if g.empty:
            if in_series.empty:
                return None, ToolResult(False, message="no rows match these filters", error_kind="not_found")
            # The filters match a series, but it has no row in the asked range (a dataset can start after the window opens or end before it closes).
            return None, ToolResult(False, message=f"no data for {period_from} to {period_to} in {source_id}: its rows run {in_series.period.min()} to {in_series.period.max()} "
                                                   f"inside the supported window {SCOPE_LO} to {SCOPE_HI}", error_kind="not_found")
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

    def annual_average(self, year: int, source_id: str, indicator_id: str, population: str,
                       adjustment: str, dimension: str | None = None) -> tuple[dict | None, ToolResult | None]:
        """Simple, unweighted mean of exactly four quarterly percent rates, never a publisher's annual estimate."""
        def fail(message, kind="invalid_arguments"):
            return None, ToolResult(False, message=message, error_kind=kind)

        if not isinstance(year, int) or isinstance(year, bool):
            return fail("year must be an integer")
        if year < _q(SCOPE_LO)[0] or year > _q(SCOPE_HI)[0]:
            return fail(f"year must be inside the supported window {SCOPE_LO} to {SCOPE_HI}")
        if _q(f"{year}-Q1") < _q(SCOPE_LO) or _q(f"{year}-Q4") > _q(SCOPE_HI):
            missing = [f"{year}-Q{q}" for q in range(1, 5) if not _q(SCOPE_LO) <= _q(f"{year}-Q{q}") <= _q(SCOPE_HI)]
            return fail(f"annual_average requires four in-scope published quarters; missing quarters: {', '.join(missing)}", "not_found")
        if any(not isinstance(v, str) or not v.strip() for v in (source_id, indicator_id, population, adjustment)):
            return fail("source_id, indicator_id, population and adjustment must be explicit non-empty strings")
        if dimension is not None and not isinstance(dimension, str):
            return fail("dimension must be a string or null")
        if adjustment not in ADJUSTMENTS:
            return fail(f"adjustment must be one of {ADJUSTMENTS}")
        if source_id not in set(self.obs.source_id):
            return fail(f"unknown source_id {source_id!r}", "not_found")
        g = self.obs[(self.obs.source_id == source_id) & (self.obs.indicator_id == indicator_id)
                     & (self.obs.population == population) & (self.obs.adjustment == adjustment)]
        if dimension is not None:
            g = g[g.dimension.str.casefold() == dimension.casefold()]
        if g.empty:
            return fail("no rows match these series filters", "not_found")
        keys = ["source_id", "indicator_id", "population", "adjustment", "dimension", "unit"]
        if len(g[keys].drop_duplicates()) != 1:
            return fail("filters leave mixed series; select exactly one dimension and percent rate series")
        if set(g.unit) != {"percent"}:
            return fail("annual_average supports percent rates only, not counts, ratios or other units")
        periods = [f"{year}-Q{q}" for q in range(1, 5)]
        g = g[g.period.isin(periods)].sort_values("period")
        if len(g) != 4 or list(g.period) != periods or g.value.isna().any():
            missing = [p for p in periods if g[g.period == p].empty or g[g.period == p].value.isna().any()]
            duplicates = [p for p in periods if len(g[g.period == p]) > 1]
            detail = f"missing quarters: {', '.join(missing)}" if missing else f"duplicate quarters: {', '.join(duplicates)}"
            return fail(f"annual_average requires four complete quarterly rates; {detail}; no partial-year average is computed", "not_found")
        values = [Decimal(str(v)) for v in g.value]
        if not all(v.is_finite() for v in values):
            return fail("all four quarterly rates must be finite published numbers", "not_found")
        shown = f"{(sum(values) / Decimal(4)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
        r = next(g.itertuples())
        inputs = [{"observation_id": row.observation_id, "period": row.period, "value": str(value), "release_stage": row.release_stage}
                  for row, value in zip(g.itertuples(), values)]
        return {"year": year, "source_id": source_id, "indicator_id": indicator_id, "population": population,
                "adjustment": adjustment, "dimension": r.dimension, "unit": "percent", "value": shown, "inputs": inputs,
                "method": "Simple unweighted arithmetic mean of four published quarterly percent rates; not an official published annual estimate.",
                "formula": f"({' + '.join(str(v) for v in values)}) / 4"}, None


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
        # Agent tools (besides get_series, which follows stats_backend) that also run on that MCP backend: the transport flag (agent.served).
        self.mcp_routed: frozenset[str] = frozenset()

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


def observation_change(a: dict, b: dict, kind: str):
    """The checks and arithmetic of calculate_change on two observation records (keys source_id, indicator_id, population, adjustment,
    dimension, unit, period, value). Returns a ToolResult error or (result, result as string, unit label, formula). Serves the in-process
    tool and the MCP server's calculate_change, so the two routes cannot disagree."""
    if kind not in CHANGE_KINDS:
        return ToolResult(False, message=f"kind must be one of {CHANGE_KINDS}", error_kind="invalid_arguments")
    same = [k for k in ("source_id", "indicator_id", "population", "adjustment", "dimension", "unit") if a[k] != b[k]]
    if same:
        return ToolResult(False, message=f"observations are different series (differ in {same}); a change is only defined within one series", error_kind="invalid_arguments")
    if a["period"] == b["period"]:
        return ToolResult(False, message="both observations are the same period", error_kind="invalid_arguments")
    if a["value"] is None or b["value"] is None:
        return ToolResult(False, message="one observation has no published number", error_kind="not_found")
    try:
        return compute_change(a["value"], b["value"], kind, a["unit"])
    except ZeroDivisionError:
        return ToolResult(False, message="percent change from zero is undefined", error_kind="invalid_arguments")


@dataclass
class TextChange:
    """A validated change between two report figures: the two passages (anything with label, passage_id, source_id, stage, title), the
    figures as Decimals, the input unit, the normalised basis and periods, and compute_change's output."""
    ia: object
    ib: object
    va: Decimal
    vb: Decimal
    unit_in: str
    basis: str
    period_a: str
    period_b: str
    kind: str
    formula: str
    shown: str
    unit: str


def text_change(resolve, passage_a: str, value_a: str, unit_a: str, basis_a: str, period_a: str,
                passage_b: str, value_b: str, unit_b: str, basis_b: str, period_b: str, kind: str = "difference"):
    """The checks and arithmetic of calculate_from_text_values. `resolve(side, label)` returns the passage (attributes text, flags,
    label, passage_id, source_id, stage, title) or None; the checks run side a then side b, as before. Returns a ToolResult error or a
    TextChange. Serves the in-process tool and the MCP server's calculate_from_text_values."""
    if kind not in CHANGE_KINDS:
        return ToolResult(False, message=f"kind must be one of {CHANGE_KINDS}", error_kind="invalid_arguments")
    legs = []
    for side, passage, value, unit, basis, period in (("a", passage_a, value_a, unit_a, basis_a, period_a), ("b", passage_b, value_b, unit_b, basis_b, period_b)):
        item = resolve(side, passage)
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
    return TextChange(ia, ib, va, vb, ua, ba, pa, pb, kind, formula, shown, unit)


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
        # Served answer selection uses actual returned chunk order, never a synthetic relevance score.
        self.report_ranks: dict[str, tuple[int, int]] = {}
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
        child._fork_ids = frozenset(self._ids)
        child.report_ranks = dict(getattr(self, "report_ranks", {}))
        return child

    def commit(self, child: Tools) -> None:
        self.items, self._ids, self._obs = child.items, child._ids, child._obs
        self._n, self.notes = child._n, child.notes
        self.report_ranks = child.report_ranks

    def merge(self, child: Tools, result: ToolResult) -> ToolResult:
        """Merge an on-time round snapshot in planned order, never replace sibling evidence.

        Calls can only read labels present at the start of their round. New labels are
        assigned here, not by worker completion order; calculation inputs therefore
        always refer to unchanged, previously committed labels.
        """
        from dataclasses import replace

        baseline = child._fork_ids
        labels, added = {}, {}
        by_id = {item.passage_id: item for item in self.items}
        for item in child.items:
            if item.passage_id in baseline:
                continue
            canonical = by_id.get(item.passage_id)
            if canonical is None:
                canonical = replace(item, label=self._label(item.label[0]))
                self._vintage_note(canonical.source_id)
                self.items.append(canonical)
                self._ids.add(canonical.passage_id)
                by_id[canonical.passage_id] = canonical
                added[canonical.passage_id] = canonical
                if item.label in child._obs:
                    self._obs[canonical.label] = {**child._obs[item.label], "label": canonical.label}
            labels[item.label] = canonical.label
        for note in child.notes:
            self._note(note)
        for pid, rank in child.report_ranks.items():
            self.report_ranks[pid] = min(rank, self.report_ranks.get(pid, rank))
        # Replace simultaneously: e.g. P1->P2 and P2->P3 must not cascade.
        message = re.sub(r"\b[POC]\d+\b", lambda m: labels.get(m[0], m[0]), result.message)
        return replace(result, items=[added[i.passage_id] for i in result.items if i.passage_id in added],
                       message=message)

    def _note(self, text: str) -> None:
        if text not in self.notes and len(self.notes) < MAX_NOTES:
            self.notes.append(text)

    def routed(self, tool: str) -> bool:
        """True when this agent tool runs on the MCP server (transport mcp_all; get_series also in mcp_stats)."""
        if getattr(self.sh, "stats_backend", None) is None:
            return False
        return tool in ("get_series", "annual_average") or tool in getattr(self.sh, "mcp_routed", ())

    def _invoke(self, tool: str, **args):
        """Run an agent tool on the MCP backend. Records that this tool call used MCP (the trace says transport=mcp) and re-attaches the run's
        visitor tag: this runs in a pool thread that does not inherit the request context."""
        self._mcp_used = True
        token = CALLER_SESSION.set(self.caller)
        try:
            return self.sh.stats_backend.invoke(tool, **args)
        finally:
            CALLER_SESSION.reset(token)

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
    def _served_cache_enabled(self) -> bool:
        return (self.tool_set == "annual" and bool(getattr(self.sh, "served_search_cache", False))
                and bool(getattr(self.sh, "corpus", None)))

    def _search(self, query: str, k: int) -> tuple[list, dict, dict, dict, dict]:
        if not self._served_cache_enabled():
            return self._search_uncached(query, k)
        from labourlens.retrieval import candidates, rerank
        from labourlens.retrieval.runtime import EMBEDDING_MODEL, CHUNK_CONFIG
        from labourlens.retrieval.served_cache import SEARCHES, identity, normalise

        query = normalise(query)
        model = getattr(getattr(getattr(self.sh.retriever, "dense", None), "cfg", None), "model", EMBEDDING_MODEL)
        key = identity("annual-search-v1", self.sh.corpus, normalise(self.question), query, self.retrieval, k,
                       model, CHUNK_CONFIG, rerank.MODEL, rerank.load_prompt()[2], candidates.POOL,
                       rerank.POOL, rerank.KEEP, self.routed("search_reports"),
                       getattr(self.sh, "tool_transport", "direct"))

        def compute():
            ranked, trace, usage, chunks, passages = self._search_uncached(query, k)
            # Retain only returned evidence, never a second complete corpus per query.
            selected = {cid: chunks[cid] for cid, _ in ranked}
            pids = {pid for c in selected.values() for pid in c.source_passage_ids}
            return ranked, trace, usage, selected, {pid: passages[pid] for pid in pids if pid in passages}

        result, hit = SEARCHES.get_or_compute(
            key, compute, timeout_s=self.tool_timeout_s,
            eligible=lambda r: bool(r[0]) and not r[1].get("rerank_fallback")
            and not r[1].get("cache_ineligible"))
        ranked, trace, usage, chunks, passages = result
        trace = dict(trace)
        trace["search_cache_hit"] = hit
        if hit:
            trace.update(rerank_cost_usd=0.0, rerank_seconds=0.0)
            usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0}
            if self.routed("search_reports"):
                self._mcp_used = True
                for pid, p in passages.items():
                    self.sh.passages_by_id[pid] = {x: p[x] for x in ("document_title", "publication_date", "release_stage", "locator", "source_id")}
        trace.pop("cache_ineligible", None)
        return list(ranked), trace, dict(usage), chunks, passages

    def _search_uncached(self, query: str, k: int) -> tuple[list, dict, dict, dict, dict]:
        """Returns (ranked, trace, usage, chunks_by_id, passages_by_id); the last two resolve the ranked chunks to passages.

        Union of the planner-query and original-question period/stage hints (retrieval.candidates.select). Default (hybrid) uses
        the old path. The rerank step is shared by both routes (_rerank_stage)."""
        if self.routed("search_reports"):
            return self._search_mcp(query, k)
        sh = self.sh
        if self.retrieval == "hybrid":
            return sh.retriever.search(query, k), {}, {}, sh.chunks_by_id, sh.passages_by_id
        from labourlens.retrieval import candidates

        started = time.perf_counter()
        retr, chunks = sh.retriever, sh.chunks_by_id
        if self._served_cache_enabled():
            from labourlens.retrieval.served_cache import query_vector

            vector = query_vector(sh.corpus, retr.dense.cfg.model, query, self.tool_timeout_s)
            dense_search = lambda depth: retr.dense.search_vector(vector, depth)
        else:
            dense_search = lambda depth: retr.dense.search(query, depth)
        ranked, trace = candidates.select(retr, chunks, query, self.question, self.retrieval, dense_search)
        ranked, trace, usage = self._rerank_stage(query, ranked, trace, [chunks[cid] for cid, _ in ranked[:candidates.POOL]], started, k)
        return ranked, trace, usage, chunks, sh.passages_by_id

    def _search_mcp(self, query: str, k: int) -> tuple[list, dict, dict, dict, dict]:
        """search_reports on the MCP server. The query vector is embedded HERE (this process holds the API key; the server never does) and
        sent as base64 float32; the server filters, fuses and returns the candidate chunks with their passages; reranking stays here
        because it calls a model. Same trace as the in-process route."""
        import base64

        import numpy as np

        from labourlens.retrieval import dense
        from labourlens.retrieval.runtime import EMBEDDING_MODEL

        started = time.perf_counter()
        if self._served_cache_enabled():
            from labourlens.retrieval.served_cache import query_vector

            vec = query_vector(self.sh.corpus, EMBEDDING_MODEL, query, self.tool_timeout_s)
        else:
            vec = dense.embed(EMBEDDING_MODEL, [query], purpose="queries")[0]
        reply, err = self._invoke(
            "search_reports", query=query, question=self.question, retrieval=self.retrieval, k=k,
            query_vector_b64=base64.b64encode(np.asarray(vec, dtype="<f4").tobytes()).decode("ascii"))
        if err is not None:
            raise _SearchRejected(err)
        r = reply.result
        if reply.quarantined:
            self._note(f"{reply.quarantined} report excerpt(s) of this search were withheld by the MCP client as instruction-like text. Evidence may be "
                       "incomplete because of a security event, not because the reports lack it. Do not estimate missing figures.")
        passages = {p.passage_id: p.model_dump() for p in r.passages}
        usable = []
        for c in r.chunks:  # the server omits a chunk's text when it is the newline-joined text of its passages; a chunk with a passage the client withheld is dropped
            text = c.text if c.text is not None else ("\n".join(passages[pid]["text"] for pid in c.source_passage_ids) if all(pid in passages for pid in c.source_passage_ids) else None)
            if text is not None:
                usable.append(c.model_copy(update={"text": text}))
        chunks = {c.chunk_id: c for c in usable}
        for pid, p in passages.items():  # remember the metadata the web card needs (never the text) for evidence cited later
            self.sh.passages_by_id[pid] = {x: p[x] for x in ("document_title", "publication_date", "release_stage", "locator", "source_id")}
        ranked = [(c.chunk_id, c.score) for c in usable]
        incomplete = bool(reply.quarantined) or len(usable) != len(r.chunks)
        if self.retrieval == "hybrid":
            return ranked[:k], ({"cache_ineligible": True} if incomplete else {}), {}, chunks, passages
        from labourlens.retrieval.candidates import POOL

        ranked, trace, usage = self._rerank_stage(query, ranked, r.trace.model_dump(), usable[:POOL], started, k)
        if incomplete:
            trace["cache_ineligible"] = True
        return ranked, trace, usage, chunks, passages

    def _rerank_stage(self, query: str, ranked: list, trace: dict, candidates: list, started: float, k: int) -> tuple[list, dict, dict]:
        from labourlens.retrieval import rerank

        trace.update(reranked=False, rerank_fallback=False, rerank_seconds=0.0, rerank_cost_usd=0.0)
        usage = {}
        if ranked:
            t0 = time.perf_counter()
            try:
                remaining = self.tool_timeout_s - (t0 - started) - 0.25
                if remaining <= 0:
                    raise TimeoutError("retrieval exhausted tool budget")
                result = rerank.rerank(query, candidates, model=rerank.MODEL, use_cache=False, timeout_s=remaining)
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

    @_transported
    def search_reports(self, query: str, k: int = 8) -> ToolResult:
        if not isinstance(query, str):
            return ToolResult(False, message="query must be a string containing the period and report topic; for example, 2021-Q3 retrenchment reasons", error_kind="invalid_arguments")
        q = query.strip()
        if not q:
            return ToolResult(False, message="query must contain a search phrase, not an empty or whitespace-only string; include the period and report topic", error_kind="invalid_arguments")
        if len(q) > MAX_QUERY_CHARS:
            return ToolResult(False, message=f"query has {len(q)} characters after trimming; the maximum is {MAX_QUERY_CHARS}. Shorten it to the period and report topic", error_kind="invalid_arguments")
        if not isinstance(k, int) or isinstance(k, bool):
            return ToolResult(False, message=f"k must be an integer from 1 to {MAX_K}, not a boolean, string or other type; use k=8 or omit k", error_kind="invalid_arguments")
        if not 1 <= k <= MAX_K:
            return ToolResult(False, message=f"k={k} is outside the allowed range 1 to {MAX_K}; k counts ranked chunks, not a year or character limit. Use k=8 or omit k", error_kind="invalid_arguments")
        new = []
        try:
            ranked, retrieval_trace, usage, chunks_by_id, passages_by_id = self._search(q, k)
        except _SearchRejected as e:
            return e.result
        for chunk_rank, (cid, _) in enumerate(ranked):
            for offset, pid in enumerate(chunks_by_id[cid].source_passage_ids):
                p = passages_by_id.get(pid)
                if p:
                    if self.tool_set == "annual":
                        rank = (chunk_rank, offset)
                        self.report_ranks[pid] = min(self.report_ranks.get(pid, rank), rank)
                    it = self._add("P", pid, p["source_id"], p["document_title"], p["publication_date"], p["release_stage"], p["locator"], p["text"])
                    if it:
                        new.append(it)
        return ToolResult(True, new, f"{len(new)} new passages from {len({i.source_id for i in new})} documents: " + ", ".join(f"{i.label}={i.source_id}" for i in new[:12]),
                          retrieval_trace=retrieval_trace, usage=usage)

    # ---- get_series -----------------------------------------------------------------------------------------------
    @_transported
    def get_series(self, source_id: str, period_from: str, period_to: str, dimension: str | None = None,
                   adjustment: str | None = None, indicator_id: str | None = None) -> ToolResult:
        if "get_series" in getattr(self.sh, "disabled_tools", frozenset()):
            return ToolResult(False, message="tool get_series is disabled for this experiment", error_kind="disabled_tool")
        backend = self.sh.stats_backend or self.sh.stats
        self._mcp_used = self.sh.stats_backend is not None
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

    @_transported
    def annual_average(self, year: int, source_id: str, indicator_id: str, population: str,
                       adjustment: str, dimension: str | None = None) -> ToolResult:
        if "annual_average" in getattr(self.sh, "disabled_tools", ()):
            return ToolResult(False, message="tool annual_average is disabled for this experiment", error_kind="disabled_tool")
        args = dict(year=year, source_id=source_id, indicator_id=indicator_id, population=population, adjustment=adjustment, dimension=dimension)
        if self.routed("annual_average"):
            reply, err = self._invoke("annual_average", **args)
            if err is not None:
                return err
            if reply.quarantined:
                raise RuntimeError("mcp unsafe annual_average reply")
            out = reply.result.model_dump()
            if any(out[k] != args[k] for k in ("year", "source_id", "indicator_id", "population", "adjustment")):
                raise RuntimeError("mcp malformed: annual_average reply does not match the request")
            if dimension is not None and out["dimension"].casefold() != dimension.casefold():
                raise RuntimeError("mcp malformed: annual_average dimension does not match the request")
        else:
            out, err = self.sh.stats.annual_average(**args)
            if err is not None:
                return err
        inputs = ", ".join(f"{r['period']}={r['value']}% (observation {r['observation_id']}, {r['release_stage']})" for r in out["inputs"])
        text = (f"Derived annual average for {out['year']}: {out['indicator_id']} ({out['dimension'] or 'all'}; "
                f"{out['population']}, {out['adjustment']}). {out['method']} "
                f"{out['formula']} = {out['value']} percent. Inputs: {inputs}.")
        cid = "annual:" + hashlib.sha256(text.encode()).hexdigest()[:12]
        it = self._add("C", cid, out["source_id"], f"Annual average on {self.sh.titles[out['source_id']]}",
                       None, "calculated", ",".join(r["observation_id"] for r in out["inputs"]), text)
        return ToolResult(True, [it] if it else [], f"{it.label} = {out['value']} percent (derived annual average)" if it else "this calculation was already done")

    # ---- calculate_change -----------------------------------------------------------------------------------------
    @_transported
    def calculate_change(self, obs_a: str, obs_b: str, kind: str = "difference") -> ToolResult:
        if kind not in CHANGE_KINDS:
            return ToolResult(False, message=f"kind must be one of {CHANGE_KINDS}", error_kind="invalid_arguments")
        a, b = self._obs.get(obs_a), self._obs.get(obs_b)
        if a is None or b is None:
            return ToolResult(False, message="obs_a and obs_b must be observation labels returned by get_series in this run", error_kind="invalid_arguments")
        if self.routed("calculate_change"):
            out = self._change_mcp(a, b, kind)
        else:
            out = observation_change(a, b, kind)
        if isinstance(out, ToolResult):
            return out
        res, shown, unit, formula = out
        cid = "calc:" + hashlib.sha256(f"{a['id']}|{b['id']}|{kind}".encode()).hexdigest()[:12]
        text = (f"Calculated {kind.replace('_', ' ')} of {a['indicator_id']} ({a['dimension'] or 'all'}; {a['population']}, {a['adjustment']}) "
                f"from {a['period']} to {b['period']}: {formula} = {shown} {unit}. Inputs {obs_a} ({a['period']}) and {obs_b} ({b['period']}).")
        it = self._add("C", cid, a["source_id"], f"Calculation on {self.sh.titles[a['source_id']]}", None, "calculated", f"{obs_a},{obs_b}", text)
        if it is None:
            return ToolResult(True, message="this calculation was already done")
        return ToolResult(True, [it], f"{it.label} = {shown} {unit}")

    def _change_mcp(self, a: dict, b: dict, kind: str):
        """The server recomputes the change from its own observations table, given the two observation ids; the result is the same
        (res, shown, unit, formula) tuple as observation_change, or a ToolResult error."""
        reply, err = self._invoke("calculate_change", observation_id_a=a["id"], observation_id_b=b["id"], kind=kind)
        if err is not None:
            return err
        r = reply.result
        if (r.observation_id_a, r.observation_id_b, r.kind) != (a["id"], b["id"], kind):
            raise RuntimeError("mcp malformed: calculation reply does not match the request")
        return Decimal(r.value), r.value, r.unit, r.formula

    # ---- calculate_from_text_values (tool set v2) -----------------------------------------------------------------
    @_transported
    def calculate_from_text_values(self, passage_a: str, value_a: str, unit_a: str, basis_a: str, period_a: str,
                                   passage_b: str, value_b: str, unit_b: str, basis_b: str, period_b: str,
                                   kind: str = "difference") -> ToolResult:
        """Exact change from figure A (the earlier or base one) to figure B, both read from report passages of this run.

        Each value must be the figure as a plain number (`2.9`, `-0.3`, `1,250`; no unit, no words) and must occur in the
        text of the cited passage (label P1, P2, ...) after normalisation (thousands separators, trailing zeros). Units and
        bases must be identical. The model never supplies a result: it is computed by compute_change, the function that
        also serves calculate_change, so rounding (half-up, 2 places) and unit labels (percentage points for percent) match.
        The checks live in text_change, shared with the MCP server's calculate_from_text_values tool."""
        args = (passage_a, value_a, unit_a, basis_a, period_a, passage_b, value_b, unit_b, basis_b, period_b, kind)
        if self.routed("calculate_from_text_values"):
            return self._text_change_mcp(*args)

        def resolve(side: str, label: str):
            return next((i for i in self.items if i.label == label and i.label[0] == "P"), None)

        out = text_change(resolve, *args)
        if isinstance(out, ToolResult):
            return out
        return self._text_change_item(out)

    def _text_change_item(self, c: TextChange) -> ToolResult:
        cid = "calc:" + hashlib.sha256(f"text|{c.ia.passage_id}|{c.va}|{c.ib.passage_id}|{c.vb}|{c.kind}".encode()).hexdigest()[:12]
        text = (f"Calculated {c.kind.replace('_', ' ')} of {c.basis} from report figures: {c.formula} = {c.shown} {c.unit}. "
                f"Inputs {c.ia.label} ({_fmt(float(c.va), c.unit_in)}, {c.period_a}; {c.ia.source_id}, {c.ia.stage}) and {c.ib.label} ({_fmt(float(c.vb), c.unit_in)}, {c.period_b}; {c.ib.source_id}, {c.ib.stage}).")
        it = self._add("C", cid, c.ia.source_id, f"Calculation on {c.ia.title}", None, "calculated", f"{c.ia.label},{c.ib.label}", text)
        if it is None:
            return ToolResult(True, message="this calculation was already done")
        return ToolResult(True, [it], f"{it.label} = {c.shown} {c.unit}")

    def _text_change_mcp(self, passage_a, value_a, unit_a, basis_a, period_a, passage_b, value_b, unit_b, basis_b, period_b, kind) -> ToolResult:
        """The same checks and arithmetic on the MCP server, which holds the passage text. The app sends passage ids (None for a label
        it does not know, so the server reports that in the same order as the in-process checks) and builds the evidence item itself."""
        def pid(label):
            return next((i.passage_id for i in self.items if i.label == label and i.label[0] == "P"), None)

        reply, err = self._invoke(
            "calculate_from_text_values", passage_a=passage_a, passage_id_a=pid(passage_a), value_a=value_a, unit_a=unit_a, basis_a=basis_a, period_a=period_a,
            passage_b=passage_b, passage_id_b=pid(passage_b), value_b=value_b, unit_b=unit_b, basis_b=basis_b, period_b=period_b, kind=kind)
        if err is not None:
            return err
        r = reply.result
        by_label = {i.label: i for i in self.items if i.label[0] == "P"}
        ia, ib = by_label.get(passage_a), by_label.get(passage_b)
        if ia is None or ib is None or (r.passage_id_a, r.passage_id_b) != (ia.passage_id, ib.passage_id):
            raise RuntimeError("mcp malformed: calculation reply does not match the request")
        c = TextChange(ia, ib, Decimal(r.value_a), Decimal(r.value_b), r.unit_in, r.basis, r.period_a, r.period_b, kind, r.formula, r.value, r.unit)
        return self._text_change_item(c)
