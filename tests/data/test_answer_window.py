"""The answer window (D-077): one set of constants, the committed observations agree with it, and the frozen prompt files are untouched."""
import pandas as pd

from labourlens import paths
from labourlens.answer.pipeline import load_prompt
from labourlens.data import catalog, derived, validate

SHORT_WORKWEEK = {"short_workweek_temporary_layoff", "short_workweek_temporary_layoff_by_industry"}  # declared to end at 2025-Q4


def test_window_constants_are_defined_once_and_reused():
    assert (catalog.ANSWER_SCOPE_START, catalog.ANSWER_SCOPE_END) == ("2020-Q1", "2026-Q2")
    assert catalog.EVALUATED_WINDOW == ("2024-Q1", "2026-Q2")  # what the frozen experiments measured; never the served window
    assert (validate.SCOPE_LO, validate.SCOPE_HI) == (catalog.ANSWER_SCOPE_START, catalog.ANSWER_SCOPE_END)
    assert catalog.scope_words() == "Q1 2020 to Q2 2026"


def test_committed_observations_are_flagged_for_the_window_and_every_dataset_covers_it():
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    inside = (obs.period >= catalog.ANSWER_SCOPE_START) & (obs.period <= catalog.ANSWER_SCOPE_END)
    assert (obs.in_answer_scope == inside).all()
    scope = obs[obs.in_answer_scope]
    first, last = scope.groupby("source_id").period.min(), scope.groupby("source_id").period.max()
    assert len(first) == 36 and (first == "2020-Q1").all()  # none starts late, so the tool never has to say "no data" for the window's first quarter
    assert set(last[last != "2026-Q2"].index) == SHORT_WORKWEEK and (last[list(SHORT_WORKWEEK)] == "2025-Q4").all()
    # a series is complete when it has one row per quarter of its declared span (a '-' cell is a row with no value, never a missing row)
    spans = scope.groupby(["source_id", "indicator_id", "population", "adjustment", "sector_path", "dimension"]).period.nunique()
    expected = spans.index.get_level_values("source_id").map(lambda sid: 24 if sid in SHORT_WORKWEEK else 26)
    assert (spans.to_numpy() == expected.to_numpy()).all()


def test_derived_summary_uses_the_window():
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    summary = derived.compute(obs)["summary"]
    assert summary["vacancy_to_unemployed_ratio_recomputed"]["n"] == 26 and summary["retrenchment_components_minus_total"]["n"] == 26


def test_frozen_prompt_files_are_unchanged_and_the_served_ones_are_new_files():
    frozen = {"planner_v1": "32c800c83425", "answer_v3": "9a9372faf52e", "triage_v1": "de176c25e4b6", "contextualise_v1": "1fdf71c2fcfc"}
    assert {name: load_prompt(name)[2] for name in frozen} == frozen  # hash-pinned by the frozen experiments: never edit, add a new version
    for old, new in (("triage_v1", "triage_v2"), ("contextualise_v1", "contextualise_v2")):
        text = load_prompt(new)[0]
        assert "Q1 2020 to Q2 2026" in text and "2024" not in text and load_prompt(new)[2] != frozen[old]
    for name in ("planner_v4", "answer_v6"):
        text = load_prompt(name)[0]
        assert "1Q 2020 to 2Q 2026" in text and "2024" not in text and "2023 onward" in text
