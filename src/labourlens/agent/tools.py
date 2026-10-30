"""Typed, read-only agent tools (ADR-002 item 4, approved set of three): search_reports, get_series, calculate_change.

Every tool validates its arguments, returns evidence items with provenance, and never raises for bad input: it returns a
ToolResult with an error kind the graph can route on. Arithmetic is deterministic (Decimal). calculate_change only accepts
observation labels that get_series returned in the same run, so a model cannot calculate on a number it invented.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from labourlens import paths
from labourlens.answer.context import ContextPassage
from labourlens.data import catalog
from labourlens.security.guards import injection_flags, sanitize_text

SCOPE_LO, SCOPE_HI = catalog.ANSWER_SCOPE_START, catalog.ANSWER_SCOPE_END
MAX_NOTES = 8
RELEASE_ID = re.compile(r"^mom-(\d{4})-q([1-4])-(advance|final.*)$")
PERIOD = re.compile(r"^(\d{4})-Q([1-4])$")
MAX_QUERY_CHARS = 300
MAX_K = 10
MAX_ROWS = 40
ADJUSTMENTS = ("seasonally_adjusted", "not_adjusted", "unspecified", "not_applicable")
CHANGE_KINDS = ("difference", "percent_change")


class TransientToolError(Exception):
    """A recoverable failure (timeout, temporary resource problem). The graph retries once."""


@dataclass
class ToolResult:
    ok: bool
    items: list[ContextPassage] = field(default_factory=list)
    message: str = ""  # short, safe summary shown to the planner (no passage text)
    error_kind: str | None = None  # invalid_arguments | not_found | too_large


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

    def __init__(self, world=None, observations: pd.DataFrame | None = None, stats=None) -> None:
        from labourlens.retrieval.runtime import load_world

        self.retriever, self.chunks_by_id, self.passages_by_id = world or load_world()
        self.stats = stats or StatsData(observations)
        self.obs, self.titles = self.stats.obs, self.stats.titles
        # Optional replacement for the direct statistics lookup, e.g. an MCP client. Same contract as StatsData.query.
        self.stats_backend = None

    def catalogue_text(self) -> str:
        return self.stats.catalogue_text()


def _fmt(value: float, unit: str) -> str:
    v = Decimal(str(round(value, 6))).normalize()
    s = f"{v:,.2f}".rstrip("0").rstrip(".") if v != v.to_integral() else f"{int(v):,}"
    return {"percent": f"{s}%", "persons": f"{s} persons", "ratio": f"{s} (ratio)"}.get(unit, f"{s} {unit}")


def _q(period: str) -> tuple[int, int]:
    m = PERIOD.match(period)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


class Tools:
    """One instance per agent run: holds the evidence registries for that run."""

    def __init__(self, shared: Shared) -> None:
        self.sh = shared
        self.items: list[ContextPassage] = []
        self._ids: set[str] = set()
        self._obs: dict[str, dict] = {}  # label -> observation facts, for calculate_change
        self._n = {"P": 0, "O": 0, "C": 0}
        # Deterministic data-quality notes about missing data and conflicting versions. Written by code, not by a model,
        # and shown to the answer step next to the evidence (never citeable themselves).
        self.notes: list[str] = []

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

    def _coverage_notes(self, rows: list[dict], period_from: str, period_to: str) -> None:
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
            if absent:
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
    def search_reports(self, query: str, k: int = 8) -> ToolResult:
        q = (query or "").strip()
        if not q or len(q) > MAX_QUERY_CHARS:
            return ToolResult(False, message=f"query must be 1 to {MAX_QUERY_CHARS} characters", error_kind="invalid_arguments")
        if not isinstance(k, int) or not 1 <= k <= MAX_K:
            return ToolResult(False, message=f"k must be an integer from 1 to {MAX_K}", error_kind="invalid_arguments")
        new = []
        for cid, _ in self.sh.retriever.search(q, k):
            for pid in self.sh.chunks_by_id[cid].source_passage_ids:
                p = self.sh.passages_by_id.get(pid)
                if p:
                    it = self._add("P", pid, p["source_id"], p["document_title"], p["publication_date"], p["release_stage"], p["locator"], p["text"])
                    if it:
                        new.append(it)
        return ToolResult(True, new, f"{len(new)} new passages from {len({i.source_id for i in new})} documents: " + ", ".join(f"{i.label}={i.source_id}" for i in new[:12]))

    # ---- get_series -----------------------------------------------------------------------------------------------
    def get_series(self, source_id: str, period_from: str, period_to: str, dimension: str | None = None,
                   adjustment: str | None = None, indicator_id: str | None = None) -> ToolResult:
        backend = self.sh.stats_backend or self.sh.stats
        rows, err = backend.query(source_id, period_from, period_to, dimension, adjustment, indicator_id)
        if err is not None:
            return err
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
        self._coverage_notes(rows, period_from, period_to)
        return ToolResult(True, new, f"{len(new)} new observations: " + ", ".join(f"{i.label}={self._obs[i.label]['period']}" for i in new[:20]))

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
        va, vb = Decimal(str(a["value"])).normalize(), Decimal(str(b["value"])).normalize()
        if kind == "difference":
            res, unit = vb - va, ("percentage points" if a["unit"] == "percent" else a["unit"])
            formula = f"{vb:f} - {va:f}"
        else:
            if va == 0:
                return ToolResult(False, message="percent change from zero is undefined", error_kind="invalid_arguments")
            res, unit = (vb - va) / va * 100, "percent"
            formula = f"({vb:f} - {va:f}) / {va:f} * 100"
        res = res.quantize(Decimal("0.01"), ROUND_HALF_UP).normalize()
        shown = f"{res:f}"
        cid = "calc:" + hashlib.sha256(f"{a['id']}|{b['id']}|{kind}".encode()).hexdigest()[:12]
        text = (f"Calculated {kind.replace('_', ' ')} of {a['indicator_id']} ({a['dimension'] or 'all'}; {a['population']}, {a['adjustment']}) "
                f"from {a['period']} to {b['period']}: {formula} = {shown} {unit}. Inputs {obs_a} ({a['period']}) and {obs_b} ({b['period']}).")
        it = self._add("C", cid, a["source_id"], f"Calculation on {self.sh.titles[a['source_id']]}", None, "calculated", f"{obs_a},{obs_b}", text)
        if it is None:
            return ToolResult(True, message="this calculation was already done")
        return ToolResult(True, [it], f"{it.label} = {shown} {unit}")
