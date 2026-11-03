"""Pure, read-only logic behind the MCP tools (no MCP types here, so tests compare it directly with the tool results).

Every function takes a StatsData, validates its arguments with the same rules as StatsData.query (supported period range,
known adjustment, known dimension) and raises AnalysisError(kind, message) for anything the caller can correct. Kinds match the
agent's tool taxonomy: invalid_arguments, not_found, too_large. Arithmetic is Decimal via agent.tools.compute_change, the same
function the agent's calculate_change uses. Nothing here reads MOM report text.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pandas as pd

from labourlens.agent.tools import ADJUSTMENTS, PERIOD, SCOPE_HI, SCOPE_LO, StatsData, _fmt, _q, compute_change
from labourlens.data import catalog, raw_store, revisions, trace
from labourlens.mcp.models import (MAX_DIMENSION_VALUES, MAX_LATEST_SERIES, MAX_REVISION_CELLS, ChangeFigure, ComparePeriodsResult, DatasetEntry,
                                   DescribeDatasetResult, DimensionValuesResult, LatestItem, LatestValueResult, ListDatasetsResult, PeriodValue,
                                   ProvenanceResult, RevisionCell, RevisionsResult, RevisionSource, SeriesInfo, SeriesSummaryResult)

LICENCE = "Singapore Open Data Licence v1.0 (attribution required; no endorsement implied)"
SERIES_COLS = ["indicator_id", "population", "adjustment", "dimension"]
OBSERVATION_ID = re.compile(r"^[0-9a-f]{16}$")
_MAX_CELL_CHARS = 80


class AnalysisError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind, self.message = kind, message


def _check_period(p: str) -> None:
    if not PERIOD.match(p or ""):
        raise AnalysisError("invalid_arguments", f"period {p!r} must look like 2026-Q2")
    if not _q(SCOPE_LO) <= _q(p) <= _q(SCOPE_HI):
        raise AnalysisError("invalid_arguments", f"supported periods are {SCOPE_LO} to {SCOPE_HI}")


def _source(stats: StatsData, source_id: str) -> pd.DataFrame:
    g = stats.obs[stats.obs.source_id == source_id]
    if g.empty:
        raise AnalysisError("not_found", f"unknown source_id {source_id!r}; valid: {sorted(set(stats.obs.source_id))}")
    return g


def _filter(stats: StatsData, source_id: str, dimension: str | None, adjustment: str | None, indicator_id: str | None) -> pd.DataFrame:
    g = _source(stats, source_id)
    if adjustment is not None and adjustment not in ADJUSTMENTS:
        raise AnalysisError("invalid_arguments", f"adjustment must be one of {ADJUSTMENTS} or null")
    if indicator_id:
        g = g[g.indicator_id == indicator_id]
    if adjustment:
        g = g[g.adjustment == adjustment]
    if dimension:
        names = sorted(set(g.dimension))
        hit = [n for n in names if n.casefold() == dimension.casefold()]
        if not hit:
            raise AnalysisError("not_found", f"dimension {dimension!r} not found in {source_id}; available: {names[:40]}")
        g = g[g.dimension == hit[0]]
    if g.empty:
        raise AnalysisError("not_found", "no rows match these filters")
    return g


def _single_series(g: pd.DataFrame, source_id: str) -> None:
    keys = g[SERIES_COLS].drop_duplicates()
    if len(keys) > 1:
        varying = {c: sorted(set(keys[c]))[:20] for c in SERIES_COLS if keys[c].nunique() > 1}
        raise AnalysisError("invalid_arguments", f"the filters leave {len(keys)} series in {source_id}; a comparison needs exactly one. "
                            f"Set the filters that still vary: {varying}")


def _pv(r) -> PeriodValue:
    return PeriodValue(period=r.period, value=float(r.value), observation_id=r.observation_id)


def _dimension_kind(source_id: str, dimension_count: int) -> str | None:
    if not dimension_count:
        return None
    m = re.search(r"_by_(\w+)$", source_id)
    return m.group(1) if m else "unspecified"


def _published(g: pd.DataFrame) -> pd.DataFrame:
    return g[g.value.notna()]


# ---- catalogue ---------------------------------------------------------------------------------------------------------------
def _entries(stats: StatsData) -> dict[str, dict]:
    return {e["source_id"]: e for e in catalog.datasets() if e["source_id"] in set(stats.obs.source_id)}


def _dataset_entry(stats: StatsData, e: dict) -> DatasetEntry:
    g = stats.obs[stats.obs.source_id == e["source_id"]]
    pub = _published(g)
    dims = g.dimension.replace("", pd.NA).dropna().nunique()
    return DatasetEntry(source_id=e["source_id"], title=e["title"], publisher=e.get("publisher"), licence=LICENCE,
                        units=sorted(set(g.unit)), populations=sorted(set(g.population)), adjustments=sorted(set(g.adjustment)),
                        first_period=pub.period.min() if len(pub) else None, last_period=pub.period.max() if len(pub) else None,
                        has_dimensions=bool(dims), dimension_count=int(dims))


def list_datasets(stats: StatsData, topic: str | None = None) -> ListDatasetsResult:
    t = (topic or "").strip().casefold()
    out = []
    for sid, e in sorted(_entries(stats).items()):
        if t:
            g = stats.obs[stats.obs.source_id == sid]
            hay = " ".join([sid, e["title"], e.get("publisher") or "", *sorted(set(g.indicator_id)), *sorted(set(g.unit))]).casefold()
            if t not in hay:
                continue
        out.append(_dataset_entry(stats, e))
    return ListDatasetsResult(dataset_count=len(out), datasets=out)


def describe_dataset(stats: StatsData, source_id: str) -> DescribeDatasetResult:
    g = _source(stats, source_id)
    e = _entries(stats)[source_id]
    spec = catalog.adapter_spec(source_id)
    definitions = {m["indicator_id"]: m.get("definition") for m in spec.get("measures", [])}
    indicators = []
    for key, s in g.groupby(["indicator_id", "unit", "population", "adjustment"]):
        pub = _published(s)
        ind = key[0]
        indicators.append(SeriesInfo(indicator_id=ind, unit=key[1], population=key[2], adjustment=key[3],
                                     definition=definitions.get(ind),
                                     first_period=pub.period.min() if len(pub) else None, last_period=pub.period.max() if len(pub) else None))
    dims = int(g.dimension.replace("", pd.NA).dropna().nunique())
    m = raw_store.load_manifest().get(source_id)
    return DescribeDatasetResult(
        source_id=source_id, title=e["title"], publisher=e.get("publisher"), canonical_url=e.get("canonical_url"), licence=LICENCE,
        licence_url=m.licence_url if m else None, publication_date=m.publication_date if m else None, snapshot_id=m.snapshot_id if m else None,
        indicators=indicators, dimension_count=dims, dimension_kind=_dimension_kind(source_id, dims), periods_in_scope=sorted(set(g.period)),
        release_stages=sorted(set(g.release_stage)))


def get_dimension_values(stats: StatsData, source_id: str) -> DimensionValuesResult:
    g = _source(stats, source_id)
    values = sorted(set(g.dimension) - {""})
    if not values:
        raise AnalysisError("not_found", f"{source_id} has no dimensions (it is a single national series)")
    return DimensionValuesResult(source_id=source_id, dimension_count=len(values), returned=min(len(values), MAX_DIMENSION_VALUES),
                                 truncated=len(values) > MAX_DIMENSION_VALUES, values=values[:MAX_DIMENSION_VALUES])


# ---- values ------------------------------------------------------------------------------------------------------------------
def latest_value(stats: StatsData, source_id: str, dimension: str | None = None, adjustment: str | None = None,
                 indicator_id: str | None = None) -> LatestValueResult:
    g = _filter(stats, source_id, dimension, adjustment, indicator_id)
    n_series = len(g[SERIES_COLS].drop_duplicates())
    if n_series > MAX_LATEST_SERIES:
        raise AnalysisError("too_large", f"{n_series} series is more than {MAX_LATEST_SERIES}; set `dimension` (see get_dimension_values) or `indicator_id`")
    items, empty = [], 0
    for _, s in g.sort_values(SERIES_COLS + ["period"]).groupby(SERIES_COLS, sort=True):
        pub = _published(s)
        if pub.empty:
            empty += 1
            continue
        last = pub.iloc[-1]
        later = sorted(p for p in s.period if p > last.period)
        items.append(LatestItem(observation_id=last.observation_id, indicator_id=last.indicator_id, dimension=last.dimension, period=last.period,
                                population=last.population, adjustment=last.adjustment, unit=last.unit, value=float(last.value),
                                display=_fmt(last.value, last.unit), release_stage=last.release_stage, later_periods_without_number=later))
    return LatestValueResult(source_id=source_id, title=stats.titles[source_id], series_count=n_series, items=items, series_without_any_value=empty)


def _row(s: pd.DataFrame, period: str):
    hit = s[s.period == period]
    if hit.empty:
        raise AnalysisError("not_found", f"the dataset has no row for {period}")
    if len(hit) > 1:
        raise AnalysisError("invalid_arguments", f"more than one row for {period}; narrow the filters")
    r = hit.iloc[0]
    if pd.isna(r.value):
        raise AnalysisError("not_found", f"no published number for {period} ({r.missing_reason}); a change cannot be computed")
    return r


def compare_periods(stats: StatsData, source_id: str, period_a: str, period_b: str, dimension: str | None = None,
                    adjustment: str | None = None, indicator_id: str | None = None) -> ComparePeriodsResult:
    for p in (period_a, period_b):
        _check_period(p)
    if period_a == period_b:
        raise AnalysisError("invalid_arguments", "period_a and period_b are the same period")
    g = _filter(stats, source_id, dimension, adjustment, indicator_id)
    _single_series(g, source_id)
    a, b = _row(g, period_a), _row(g, period_b)
    diff, diff_s, diff_u, diff_f = compute_change(a.value, b.value, "difference", a.unit)
    try:
        _, rel_s, rel_u, rel_f = compute_change(a.value, b.value, "percent_change", a.unit)
        rel = ChangeFigure(value=rel_s, unit=rel_u, formula=rel_f)
    except ZeroDivisionError:
        rel = None
    if a.unit == "percent":
        expl = (f"`difference` is {diff_s} percentage points (the arithmetic gap between two rates). `relative_change` is the change as a percent "
                f"of the {period_a} rate. They are different quantities; do not call the difference a percent change.")
    else:
        expl = f"`difference` is in {a.unit}. `relative_change` is the change as a percent of the {period_a} value."
    return ComparePeriodsResult(
        source_id=source_id, title=stats.titles[source_id], indicator_id=a.indicator_id, dimension=a.dimension, population=a.population,
        adjustment=a.adjustment, unit=a.unit, period_a=period_a, period_b=period_b, observation_id_a=a.observation_id, observation_id_b=b.observation_id,
        value_a=float(a.value), value_b=float(b.value), release_stage_a=a.release_stage, release_stage_b=b.release_stage,
        difference=ChangeFigure(value=diff_s, unit=diff_u, formula=diff_f), relative_change=rel, explanation=expl)


def series_summary(stats: StatsData, source_id: str, period_from: str, period_to: str, dimension: str | None = None,
                   adjustment: str | None = None, indicator_id: str | None = None) -> SeriesSummaryResult:
    for p in (period_from, period_to):
        _check_period(p)
    if _q(period_from) > _q(period_to):
        raise AnalysisError("invalid_arguments", "period_from is after period_to")
    g = _filter(stats, source_id, dimension, adjustment, indicator_id)
    _single_series(g, source_id)
    s = g[(g.period >= period_from) & (g.period <= period_to)].sort_values("period")
    if s.empty:
        raise AnalysisError("not_found", f"no data for {period_from} to {period_to}: the selected series has rows from {g.period.min()} to {g.period.max()}")
    pub = _published(s)
    if pub.empty:
        raise AnalysisError("not_found", "no published numbers in this period range")
    vals = [(Decimal(str(r.value)), r) for r in pub.itertuples()]
    lo = min(vals, key=lambda t: t[0])  # min/max keep the first of equal values, so ties resolve to the earliest period
    hi = max(vals, key=lambda t: t[0])
    first, last = vals[0], vals[-1]
    direction = "increase" if last[0] > first[0] else "decrease" if last[0] < first[0] else "flat"
    head = s.iloc[0]
    return SeriesSummaryResult(
        source_id=source_id, title=stats.titles[source_id], indicator_id=head.indicator_id, dimension=head.dimension, population=head.population,
        adjustment=head.adjustment, unit=head.unit, period_from=period_from, period_to=period_to, observations=len(s),
        periods_without_number=sorted(s[s.value.isna()].period), first=_pv(first[1]), last=_pv(last[1]), minimum=_pv(lo[1]), maximum=_pv(hi[1]),
        direction=direction, release_stages=sorted(set(s.release_stage)))


# ---- revisions and provenance ------------------------------------------------------------------------------------------------
def _key_in_period(key: list[str], period: str) -> bool:
    y, q = int(period[:4]), int(period[-1])
    for e in key:
        m = re.search(r"(\d{4})\D*Q([1-4])", e) or re.search(r"([1-4])\s*Q\D*(\d{4})", e)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if (a, b) == (y, q) or (b, a) == (y, q):
                return True
        m = re.fullmatch(r"(\d{4})-(\d{2})", e.strip())
        if m and int(m.group(1)) == y and (int(m.group(2)) - 1) // 3 + 1 == q:
            return True
    return False


def _clip(s: str) -> str:
    s = str(s)
    return s if len(s) <= _MAX_CELL_CHARS else s[:_MAX_CELL_CHARS] + "..."


def get_revisions(stats: StatsData, source_id: str | None = None, period: str | None = None) -> RevisionsResult:
    if source_id is not None:
        _source(stats, source_id)
    if period is not None and not PERIOD.match(period):
        raise AnalysisError("invalid_arguments", f"period {period!r} must look like 2026-Q2")
    report = revisions.compute()
    ids = sorted(set(stats.obs.source_id) & set(report)) if source_id is None else [source_id]
    sources, cells = [], []
    for sid in ids:
        r = report[sid]
        if "status" in r:
            sources.append(RevisionSource(source_id=sid, snapshots=r["snapshots"], status=r["status"]))
            continue
        ch = [c for c in r["changed_cells"] if period is None or _key_in_period(c["key"], period)]
        added = [k for k in r["added_rows"] if period is None or _key_in_period(k, period)]
        removed = [k for k in r["removed_rows"] if period is None or _key_in_period(k, period)]
        sources.append(RevisionSource(source_id=sid, snapshots=r["snapshots"], status="compared", old_snapshot=r["old"], new_snapshot=r["new"],
                                      changed_cell_count=len(ch), added_row_count=len(added), removed_row_count=len(removed)))
        cells += [RevisionCell(source_id=sid, key=[_clip(k) for k in c["key"]], column=_clip(c["column"]), old=_clip(c["old"]), new=_clip(c["new"])) for c in ch]
    compared = [s for s in sources if s.status == "compared"]
    if not compared:
        msg = ("Only one snapshot of each requested dataset is on disk, so there is no revision history yet (a baseline was established). "
               "This does not show that no published value has been revised.")
    else:
        msg = f"Compared the two most recent snapshots of {len(compared)} dataset(s)." + (f" Restricted to {period}." if period else "")
    return RevisionsResult(sources_checked=len(sources), sources_with_revisions=sum(1 for s in compared if s.changed_cell_count or s.added_row_count
                                                                                    or s.removed_row_count),
                           sources=sources, changed_cells=cells[:MAX_REVISION_CELLS], truncated=len(cells) > MAX_REVISION_CELLS, message=msg)


def get_provenance(stats: StatsData, observation_id: str) -> ProvenanceResult:
    if not OBSERVATION_ID.match(observation_id or ""):
        raise AnalysisError("invalid_arguments", "observation_id must be 16 lowercase hex characters, as returned in `observation_id` by the statistics tools. "
                            "Only statistic observations have provenance here; report passages are not served.")
    hit = stats.obs[stats.obs.observation_id == observation_id]
    if hit.empty:
        raise AnalysisError("not_found", "no such observation in the supported period range")
    o = hit.iloc[0].to_dict()
    m = raw_store.load_manifest().get(o["source_id"])
    if m is None:
        raise AnalysisError("not_found", f"no manifest entry for {o['source_id']}")
    p = trace.observation_provenance(o, m)
    steps = [f"period {p['source_period_raw']!r} in the source mapped to {o['period']} ({o['period_start']} to {o['period_end']})",
             (f"raw cell {p['raw_value']!r} parsed to number {o['value']}" if pd.notna(o["value"]) else f"no published number: {p['missing_reason']}"),
             f"unit {o['unit']}, population {o['population']}, adjustment {o['adjustment']} assigned from the dataset adapter spec",
             f"normalisation version {p['transformation_version']}"]
    return ProvenanceResult(**{k: p[k] for k in ("observation_id", "source_id", "title", "publisher", "canonical_url", "publication_date", "retrieved_utc",
                                                  "snapshot_id", "sha256", "file", "licence_id", "licence_url", "source_locator", "raw_csv_line")},
                            transformations=steps)
