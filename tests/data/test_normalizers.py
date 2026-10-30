"""Adapters on small synthetic CSVs, using real adapter specs."""
import copy

import pytest

from labourlens.data import catalog
from labourlens.data import normalize as n


def _res(sid):
    return n.NormResult(sid, "snap-test")


def test_quarterly_long_dash_and_na_are_null_not_zero():
    spec = catalog.adapter_spec("retrenched_by_industry")
    header = spec["expected_columns"]
    assert len(header) == 3
    ind = next(k for k in spec["industry_hierarchy"])
    rows = [["2026-Q2", ind, "-"], ["2026-Q2", ind, "120"], ["2026-Q1", ind, "0"]]
    res = _res(spec["source_id"])
    n._long(spec, "snap-test", header, rows, res)
    vals = [(o.period, o.value, o.missing_reason) for o in res.observations]
    assert vals[0][1] is None and "dash_marker" in vals[0][2]
    assert vals[1][1] == 120.0 and vals[1][2] is None
    assert vals[2][1] == 0.0 and vals[2][2] is None  # a real zero stays a zero


def test_bad_period_and_bad_value_are_quarantined_not_dropped():
    spec = catalog.adapter_spec("retrenched_employees")
    header = spec["expected_columns"]
    rows = [["2026-Q9", "100"], ["2026-Q1", "oops"], ["2026-Q1", "100"], ["2026-Q2"]]
    res = _res(spec["source_id"])
    n._long(spec, "snap-test", header, rows, res)
    assert len(res.observations) == 1
    assert len(res.quarantined) == 3
    assert {q.reason.split(" ")[0] for q in res.quarantined} >= {"not", "undeclared", "wrong"}


def test_schema_drift_is_fatal():
    spec = catalog.adapter_spec("retrenched_employees")
    with pytest.raises(n.SpecViolation):
        n._long(spec, "snap-test", ["quarter", "retrenchments"], [], _res(spec["source_id"]))


def test_unexpected_wide_column_is_fatal():
    spec = catalog.adapter_spec("employment_change_by_sector")
    with pytest.raises(n.SpecViolation):
        n._sector_wide(spec, "snap-test", [spec["label_col"], "2026Q2"], [], _res(spec["source_id"]))
    with pytest.raises(n.SpecViolation):
        n._sector_wide(spec, "snap-test", ["Wrong", "20262Q"], [], _res(spec["source_id"]))


def test_sector_wide_hierarchy_and_long_conversion():
    spec = catalog.adapter_spec("employment_change_by_sector")
    w = spec["indent_width"]
    header = [spec["label_col"], "20251Q", "20252Q"]
    rows = [["Total", "10", "20"], [" " * w + "Goods", "4", "na"], [" " * w * 2 + "Manufacturing", "3", "5"], [" " * w + "Services", "6", "15"]]
    res = _res(spec["source_id"])
    n._sector_wide(spec, "snap-test", header, rows, res)
    assert len(res.observations) == 8
    manuf = [o for o in res.observations if o.dimension == "Manufacturing"]
    assert {o.sector_path for o in manuf} == {"Total > Goods > Manufacturing"}
    assert {o.sector_level for o in manuf} == {2}
    na = [o for o in res.observations if o.dimension == "Goods" and o.period == "2025-Q2"][0]
    assert na.value is None and na.missing_reason
    # child sums reproduce the parent for the quarter where all values exist
    q1 = {o.dimension: o.value for o in res.observations if o.period == "2025-Q1"}
    assert q1["Goods"] + q1["Services"] == q1["Total"]


def test_odd_indent_and_orphan_rows_are_quarantined():
    spec = catalog.adapter_spec("employment_change_by_sector")
    w = spec["indent_width"]
    header = [spec["label_col"], "20251Q"]
    rows = [[" " * (w + 1) + "Odd", "1"], [" " * w + "Orphan", "2"]]
    res = _res(spec["source_id"])
    n._sector_wide(spec, "snap-test", header, rows, res)
    assert not res.observations and len(res.quarantined) == 2


def test_observation_ids_are_deterministic():
    spec = catalog.adapter_spec("retrenched_employees")
    rows = [["2026-Q2", "4620"]]
    a, b = _res(spec["source_id"]), _res(spec["source_id"])
    n._long(copy.deepcopy(spec), "snap-test", spec["expected_columns"], rows, a)
    n._long(copy.deepcopy(spec), "snap-test", spec["expected_columns"], rows, b)
    assert a.observations[0].observation_id == b.observations[0].observation_id
