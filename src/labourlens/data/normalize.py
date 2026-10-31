"""Spec-driven normalization of statistical CSVs into StatisticalObservation records.

Three adapters, selected by specs/datasets/<source_id>.yaml:
  quarter_end_month         'YYYY-MM' periods where MM must be 03/06/09/12 (unemployment series)
  quarterly_long            'YYYY-Qn' periods, one or more measure columns
  quarterly_long_dimension  as above plus a dimension column (industry) with a spec-defined hierarchy
  sector_wide               one column per quarter ('20262Q'), hierarchy encoded by leading whitespace

Cleaning rules (never silent):
  * values must match a strict numeric pattern; a declared missing token becomes value=None with a
    missing_reason (never 0); anything else goes to quarantine with the raw cell and the reason
  * the source's own text is preserved in raw_value
  * every record carries a locator (csv row and column) back to the snapshot file
"""

from __future__ import annotations

import calendar
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from labourlens import paths
from labourlens.data import catalog, raw_store
from labourlens.models import StatisticalObservation, stable_id

_NUM = re.compile(r"^[+-]?\d+(\.\d+)?$")
_QUARTER = re.compile(r"^(\d{4})-Q([1-4])$")
_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_WIDE = re.compile(r"^(\d{4})([1-4])Q$")


class SpecViolation(Exception):
    """The CSV does not match its declared contract (schema drift). Always fatal for that dataset."""


@dataclass
class Quarantined:
    source_id: str
    snapshot_id: str
    locator: str
    raw_value: str
    reason: str


@dataclass
class NormResult:
    source_id: str
    snapshot_id: str
    observations: list[StatisticalObservation] = field(default_factory=list)
    quarantined: list[Quarantined] = field(default_factory=list)
    rows_read: int = 0


def quarter_bounds(year: int, q: int) -> tuple[str, str]:
    m0 = 3 * (q - 1) + 1
    m1 = 3 * q
    return date(year, m0, 1).isoformat(), date(year, m1, calendar.monthrange(year, m1)[1]).isoformat()


def period_label(year: int, q: int) -> str:
    return f"{year}-Q{q}"


def parse_quarter(raw: str) -> tuple[int, int]:
    m = _QUARTER.match(raw.strip())
    if not m:
        raise ValueError(f"not a YYYY-Qn quarter: {raw!r}")
    return int(m.group(1)), int(m.group(2))


def parse_quarter_end_month(raw: str) -> tuple[int, int]:
    """'2026-06' -> (2026, 2). Only quarter-end months are valid; '2026-05' is rejected, not rounded."""
    m = _MONTH.match(raw.strip())
    if not m:
        raise ValueError(f"not a YYYY-MM period: {raw!r}")
    year, month = int(m.group(1)), int(m.group(2))
    if month not in (3, 6, 9, 12):
        raise ValueError(f"month {month:02d} is not a quarter-end month in {raw!r}")
    return year, month // 3


def parse_wide_quarter(raw: str) -> tuple[int, int]:
    m = _WIDE.match(raw.strip())
    if not m:
        raise ValueError(f"not a YYYYnQ column: {raw!r}")
    return int(m.group(1)), int(m.group(2))


def parse_value(raw: str, missing_tokens: list[str]) -> tuple[float | None, str | None]:
    """Returns (value, missing_reason). Raises ValueError for an undeclared non-numeric token."""
    s = raw.strip()
    if s.lower() in {t.lower() for t in missing_tokens}:
        return None, f"source_token:{s!r}" if s else "source_blank"
    if not _NUM.match(s):
        raise ValueError(f"undeclared non-numeric value {raw!r}")
    return float(s), None


def in_scope(year: int, q: int) -> bool:
    lo = parse_quarter(catalog.ANSWER_SCOPE_START)
    hi = parse_quarter(catalog.ANSWER_SCOPE_END)
    return lo <= (year, q) <= hi


def _read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    text = path.read_text(encoding="utf-8-sig")
    rdr = csv.reader(io.StringIO(text))
    rows = list(rdr)
    if not rows:
        raise SpecViolation("empty CSV")
    return rows[0], rows[1:]


def _snapshot_path(source_id: str) -> tuple[str, Path]:
    m = raw_store.load_manifest().get(source_id)
    if not m or m.retrieval_status != "ok" or not m.raw_path or not m.snapshot_id:
        raise SpecViolation(f"no successfully fetched snapshot for {source_id}")
    path = paths.ROOT / m.raw_path
    if not path.exists():
        raise SpecViolation(f"raw file for {source_id} is not present ({m.redistribution_policy}, {m.rights_status}); run `labourlens fetch --only {source_id}`")
    return m.snapshot_id, path


def _make_obs(*, spec: dict[str, Any], measure: dict[str, Any], snapshot_id: str, locator: str, year: int, q: int,
              raw_period: str, value: float | None, raw_value: str, missing_reason: str | None,
              dimension: str = "", sector_path: str = "", sector_level: int | None = None) -> StatisticalObservation:
    start, end = quarter_bounds(year, q)
    period = period_label(year, q)
    return StatisticalObservation(
        observation_id=stable_id(spec["source_id"], snapshot_id, measure["indicator_id"], period,
                                 measure["population"], measure["adjustment"], dimension or sector_path, "dataset_snapshot"),
        source_id=spec["source_id"],
        snapshot_id=snapshot_id,
        source_locator=locator,
        indicator_id=measure["indicator_id"],
        period=period,
        period_start=start,
        period_end=end,
        source_period_raw=raw_period,
        value=value,
        raw_value=raw_value,
        missing_reason=missing_reason,
        unit=measure["unit"],
        population=measure["population"],
        adjustment=measure["adjustment"],
        dimension=dimension,
        sector_path=sector_path,
        sector_level=sector_level,
        in_answer_scope=in_scope(year, q),
    )


def normalize(source_id: str) -> NormResult:
    spec = catalog.adapter_spec(source_id)
    snapshot_id, path = _snapshot_path(source_id)
    header, rows = _read_rows(path)
    res = NormResult(source_id, snapshot_id, rows_read=len(rows))
    adapter = spec["adapter"]
    if adapter == "sector_wide":
        _sector_wide(spec, snapshot_id, header, rows, res)
    else:
        _long(spec, snapshot_id, header, rows, res)
    return res


def _long(spec: dict[str, Any], snapshot_id: str, header: list[str], rows: list[list[str]], res: NormResult) -> None:
    if header != spec["expected_columns"]:
        raise SpecViolation(f"{spec['source_id']}: columns {header} != expected {spec['expected_columns']}")
    idx = {c: i for i, c in enumerate(header)}
    month_mode = spec["adapter"] == "quarter_end_month"
    dim_col = spec.get("dimension_col")
    hierarchy = spec.get("industry_hierarchy") or {}
    for n, row in enumerate(rows, start=2):  # line 1 is the header
        if len(row) != len(header):
            res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n}", ",".join(row), "wrong column count"))
            continue
        raw_period = row[idx[spec["period_col"]]]
        try:
            year, q = parse_quarter_end_month(raw_period) if month_mode else parse_quarter(raw_period)
        except ValueError as e:
            res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n};col={spec['period_col']}", raw_period, str(e)))
            continue
        bad_const = [(c, row[idx[c]], v) for c, v in (spec.get("constant_columns") or {}).items() if row[idx[c]] != v]
        if bad_const:
            res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n}", ",".join(row), f"constant column mismatch {bad_const}"))
            continue
        dimension = row[idx[dim_col]].strip() if dim_col else ""
        level = path_str = None
        if dim_col:
            node = hierarchy.get(dimension)
            if node:
                chain = [dimension]
                p = node["parent"]
                while p:
                    chain.append(p)
                    p = hierarchy[p]["parent"]
                path_str = " > ".join(reversed(chain))
                level = node["level"]
        for m in spec["measures"]:
            raw_value = row[idx[m["column"]]]
            try:
                value, reason = parse_value(raw_value, spec.get("missing_tokens", []))
            except ValueError as e:
                res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n};col={m['column']}", raw_value, str(e)))
                continue
            if value is None and raw_value.strip() == "-":
                reason = "dash_marker_publisher_does_not_define_nil_vs_suppressed"
            res.observations.append(
                _make_obs(spec=spec, measure=m, snapshot_id=snapshot_id, locator=f"csv_row={n};col={m['column']}", year=year, q=q,
                          raw_period=raw_period, value=value, raw_value=raw_value, missing_reason=reason,
                          dimension=dimension, sector_path=path_str or "", sector_level=level)
            )


def _sector_wide(spec: dict[str, Any], snapshot_id: str, header: list[str], rows: list[list[str]], res: NormResult) -> None:
    if header[0] != spec["label_col"]:
        raise SpecViolation(f"first column {header[0]!r} != {spec['label_col']!r}")
    cols: list[tuple[int, int, int, str]] = []  # (col_idx, year, q, raw)
    for i, c in enumerate(header[1:], start=1):
        try:
            y, q = parse_wide_quarter(c)
        except ValueError as e:
            raise SpecViolation(f"unexpected sector column {c!r}: {e}") from e
        cols.append((i, y, q, c))
    measure = spec["measures"][0]
    stack: list[tuple[int, str]] = []
    width = spec["indent_width"]
    for n, row in enumerate(rows, start=2):
        label_raw = row[0]
        indent = len(label_raw) - len(label_raw.lstrip(" "))
        if indent % width:
            res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n};col=DataSeries", label_raw, f"indent {indent} not a multiple of {width}"))
            continue
        level = indent // width
        label = label_raw.strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        if level > 0 and not stack:
            res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n}", label_raw, "indented row has no parent"))
            continue
        stack.append((level, label))
        path_str = " > ".join(s[1] for s in stack)
        for ci, y, q, raw_col in cols:
            raw_value = row[ci] if ci < len(row) else ""
            try:
                value, reason = parse_value(raw_value, spec.get("missing_tokens", []))
            except ValueError as e:
                res.quarantined.append(Quarantined(spec["source_id"], snapshot_id, f"csv_row={n};series={label!r};col={raw_col}", raw_value, str(e)))
                continue
            res.observations.append(
                _make_obs(spec=spec, measure=measure, snapshot_id=snapshot_id,
                          locator=f"csv_row={n};series={label!r};col={raw_col}", year=y, q=q, raw_period=raw_col,
                          value=value, raw_value=raw_value, missing_reason=reason, dimension=label,
                          sector_path=path_str, sector_level=level)
            )
