"""Deck popover policy: short, plain, one idea, with the original kept in the speaker notes.

The policy is a dependency-free ES module (web/static/presentation/tooltips.js), so these tests run it under
Node and skip when Node is missing. The rendered check, which hovers every trigger, is scripts/audit_deck_tips.py.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

PRESENTATION = Path(__file__).resolve().parents[2] / "web" / "static" / "presentation"
NODE = shutil.which("node")
LONG = ("The statistics store covers a very wide set of series, and each of them carries units, population, adjustment and provenance "
        "on every row, which is useful to know; the rest is detail that belongs in the notes.")
FIGURES = ("Has an unsupported claim: 234 answers judged by both. Raw agreement 99.6%, kappa 0.00. "
           "Raw agreement is high but kappa is low because almost every item gets the same label, so kappa says little.")


def run(script: str):
    if not NODE:
        pytest.skip("node is not installed")
    module = (PRESENTATION / "tooltips.js").as_uri()
    out = subprocess.run([NODE, "--input-type=module", "-e", f"import * as t from {json.dumps(module)};\n{script}"],
                         capture_output=True, text=True, timeout=30, check=True)
    return json.loads(out.stdout)


def test_short_text_is_kept_and_long_text_becomes_one_clause():
    got = run(f"console.log(JSON.stringify([t.shorten('Ten words is already short enough to stay as it is.'), t.shorten({json.dumps(LONG)})]));")
    assert got[0] == "Ten words is already short enough to stay as it is."
    assert 0 < len(got[1].split()) <= 24 and got[1].endswith(".")
    assert LONG.startswith(got[1][:-1]), "the summary is the opening clause of the original, not a rewrite"


def test_a_tiny_opening_takes_the_next_sentence_and_figures_survive():
    got = run("console.log(JSON.stringify([t.shorten('Recorded evidence\\nOutcome: the agent declined to answer the question for the year 2023, "
              "which is out of range for the data set held here.'), t.shorten(" + json.dumps(FIGURES) + ")]));")
    assert got[0].startswith("Recorded evidence. Outcome:")
    assert "99.6%" in got[1] and "0.00" in got[1] and len(got[1].split()) <= 22


def test_prose_without_punctuation_is_capped_and_closed():
    text = " ".join(f"word{i}" for i in range(60))
    got = run(f"console.log(JSON.stringify(t.shorten({json.dumps(text)})));")
    assert len(got.split()) <= 22 and got.endswith(".")


def test_hand_written_summaries_are_short_unique_and_plain():
    table = run("console.log(JSON.stringify(t.OVERRIDES));")
    starts = [start for start, _ in table]
    assert len(starts) == len(set(starts)), "duplicate override key"
    for start, short in table:
        assert 0 < len(short.split()) <= 26, (start, short)
        assert short.endswith("."), (start, short)
        assert "\u2014" not in short and "\u2013" not in short, start
        assert "gpt5.6-luna" not in short and "gpt-5.6-luna" not in short, start


def test_chart_rows_are_dropped_whole():
    got = run("""
    const lines = ['A3, gpt-6-luna', 'Median 15.4 s', 'Middle half 9.1 s to 22.9 s', '5th to 95th percentile 4.8 s to 35.9 s', 'Slowest or costliest 46.3 s', '237 cases'];
    const shown = t.chartLines(lines, {});
    console.log(JSON.stringify({shown, lines, small: t.chartLines(['R2', 'hit@8: 74.2%'], {}), words: shown.join(' ').split(/\\s+/).length}));
    """)
    assert got["shown"][:2] == ["A3, gpt-6-luna", "Median 15.4 s"]
    assert got["shown"] == got["lines"][: len(got["shown"])] and len(got["shown"]) < len(got["lines"]), "rows are dropped from the end, never cut mid-row"
    assert got["words"] <= 22


def test_deck_hooks_the_policy_in_and_drops_the_native_title_duplicate():
    graphics = (PRESENTATION / "graphics.js").read_text(encoding="utf-8")
    deck = (PRESENTATION / "deck.js").read_text(encoding="utf-8")
    charts = (PRESENTATION.parent / "charts.js").read_text(encoding="utf-8")
    with_tip = graphics[graphics.index("export function withTip"):graphics.index("const STAGE_NAME")]
    assert "setAttribute('title'" not in with_tip and "recordOriginal" in with_tip
    assert "tipNotes(inner)" in deck and "tightenLabels(inner)" in deck and "setTipFormatter(chartLines)" in deck
    assert "export function setTipFormatter" in charts
