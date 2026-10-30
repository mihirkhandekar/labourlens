import json

import pytest

from labourlens import paths
from labourlens.data.revisions import diff_csv


def _w(p, text):
    p.write_text(text)
    return p


def test_diff_detects_revision_addition_removal(tmp_path):
    old = _w(tmp_path / "o.csv", "quarter,value\n2026-Q1,100\n2026-Q2,200\n2025-Q4,50\n")
    new = _w(tmp_path / "n.csv", "quarter,value\n2026-Q1,110\n2026-Q2,200\n2026-Q3,300\n")
    d = diff_csv(old, new, ["quarter"])
    assert d["changed_cells"] == [{"key": ["2026-Q1"], "column": "value", "old": "100", "new": "110"}]
    assert d["added_rows"] == [["2026-Q3"]] and d["removed_rows"] == [["2025-Q4"]]


def test_diff_identical_files_is_empty(tmp_path):
    a = _w(tmp_path / "a.csv", "quarter,value\n2026-Q1,100\n")
    d = diff_csv(a, a, ["quarter"])
    assert not (d["changed_cells"] or d["added_rows"] or d["removed_rows"])


def test_diff_reports_schema_change(tmp_path):
    a = _w(tmp_path / "a.csv", "quarter,value\n2026-Q1,100\n")
    b = _w(tmp_path / "b.csv", "quarter,value,flag\n2026-Q1,100,x\n")
    assert diff_csv(a, b, ["quarter"])["added_columns"] == ["flag"]


@pytest.fixture
def rec():
    p = paths.ARTIFACTS / "reconciliation.json"
    if not p.exists():
        pytest.skip("run `labourlens build` first")
    return json.loads(p.read_text())


def test_reconciliation_matches_hand_read_values(rec):
    """Values read by hand from the MOM releases and the sector dataset on 2026-10-30."""
    rows = {r["period"]: r for r in rec["quarters"]}
    assert rows["2026-Q2"]["advance"]["value"] == 10700
    assert rows["2026-Q2"]["final"]["value"] == 11400
    assert rows["2026-Q2"]["dataset_total"]["value"] == 14700
    assert rows["2025-Q4"]["final"]["value"] - rows["2025-Q4"]["advance"]["value"] == -1900
