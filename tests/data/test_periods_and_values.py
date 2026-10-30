"""Period and value parsing: the rules that stop silent mis-dating and silent zero-filling."""
import pytest

from labourlens.data import normalize as n


@pytest.mark.parametrize("raw,expected", [("2026-03", (2026, 1)), ("2026-06", (2026, 2)), ("2025-09", (2025, 3)), ("2025-12", (2025, 4))])
def test_quarter_end_months_map_to_quarters(raw, expected):
    assert n.parse_quarter_end_month(raw) == expected


@pytest.mark.parametrize("raw", ["2026-05", "2026-01", "2026-13", "2026", "26-06", "2026-6", "June 2026"])
def test_non_quarter_end_month_is_rejected_not_rounded(raw):
    with pytest.raises(ValueError):
        n.parse_quarter_end_month(raw)


@pytest.mark.parametrize("raw", ["2026-Q5", "2026Q2", "2026-q2", "Q2-2026", ""])
def test_bad_quarter_labels_rejected(raw):
    with pytest.raises(ValueError):
        n.parse_quarter(raw)


def test_wide_columns_parse_and_reject():
    assert n.parse_wide_quarter("20262Q") == (2026, 2)
    with pytest.raises(ValueError):
        n.parse_wide_quarter("2026Q2")


def test_quarter_bounds_handle_month_lengths():
    assert n.quarter_bounds(2024, 1) == ("2024-01-01", "2024-03-31")  # leap year does not matter for Q1 end
    assert n.quarter_bounds(2026, 2) == ("2026-04-01", "2026-06-30")
    assert n.quarter_bounds(2025, 4) == ("2025-10-01", "2025-12-31")


def test_scope_window_is_inclusive():
    assert n.in_scope(2024, 1) and n.in_scope(2026, 2)
    assert not n.in_scope(2023, 4) and not n.in_scope(2026, 3)


def test_missing_token_is_none_with_reason_never_zero():
    v, reason = n.parse_value("-", ["na", "-"])
    assert v is None and reason
    v, reason = n.parse_value("NA", ["na", "-"])
    assert v is None and reason


def test_real_zero_is_a_value():
    assert n.parse_value("0", ["na"]) == (0.0, None)
    assert n.parse_value("0.0", ["na"]) == (0.0, None)


@pytest.mark.parametrize("raw", ["1,200", "12%", "n/a", "abc", "1.2.3", "--", "1e3"])
def test_undeclared_text_is_an_error(raw):
    with pytest.raises(ValueError):
        n.parse_value(raw, ["na", "-"])


def test_negative_and_decimal_values_parse():
    assert n.parse_value("-1900", ["na"]) == (-1900.0, None)
    assert n.parse_value("+2.5", ["na"]) == (2.5, None)
