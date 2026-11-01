"""The landing page is the project report: a hero, a step navigator and one band per step of the story.

These are source-level checks (the page is drawn in the browser). They pin the required sections, the
honest review wording, the copy rules (no dashes, internal identifiers or review timings) and that every
number the copy reads from report.json is still in the projection.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
STATIC = WEB / "static"
REPORT_JS = [STATIC / "js" / name for name in ("home.js", "report-story.js", "report-kit.js", "report-pool.js", "report-process.js")]
REPORT_CSS = STATIC / "css" / "report.css"
STORY = (STATIC / "js" / "report-story.js").read_text(encoding="utf-8")
HOME = (STATIC / "js" / "home.js").read_text(encoding="utf-8")

REQUIRED_STEPS = {
    "about": "About me", "assignment": "The assignment", "problem": "Why this problem", "system": "The system", "data": "The data",
    "eda": "What the data showed", "hard": "Hard parts", "models": "Models", "retrieval": "Retrieval", "agent": "The agent",
    "tools": "Tools and MCP", "safety": "Safety", "review": "Human review", "ops": "Cost and deployment", "process": "How I built it",
    "limits": "Limits", "coverage": "Coverage", "run": "Run it",
}
REVIEW_SENTENCE = (
    "Gold labels were drafted by AI. I went through them in the review interface and recorded a decision on every case, "
    "answer verdict and source check (403 items). Most were quick confirmations, so read the labels as AI-drafted and owner-confirmed. "
    "One reviewer, after AI pre-review and after the runs were scored."
)


def _steps():
    block = re.search(r"export const STEPS = \[(.*?)\n\];", STORY, re.S).group(1)
    return dict(re.findall(r"\['([a-z]+)', '([^']+)'\]", block))


def test_index_loads_report_styles_and_not_the_workbench_sheet():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "/static/css/presentation.css" in html and "/static/css/report.css" in html
    assert "workbench.css" not in html
    assert (STATIC / "css" / "report.css").is_file()


def test_every_required_step_has_a_nav_label_and_a_band():
    steps = _steps()
    assert steps == REQUIRED_STEPS, "step list or order changed"
    assert list(steps) == list(REQUIRED_STEPS)
    for step in steps:
        assert f"id: '{step}'" in STORY, f"no band for {step}"


def test_nav_is_text_only_with_no_numbering():
    for label in _steps().values():
        assert not re.search(r"\d", label), label
    assert "aria-label', 'Report steps'" in HOME
    assert "aria-current" in HOME and "scrollIntoView" in HOME and "IntersectionObserver" in HOME
    for key in ("ArrowDown", "ArrowUp", "Home", "End"):
        assert key in HOME
    css = REPORT_CSS.read_text(encoding="utf-8")
    assert not re.search(r"\.rp-step[^{]*::(before|after)", css), "step links must not carry markers"


def test_hero_has_name_pitch_and_two_buttons():
    assert "Mihir Khandekar" in HOME
    assert "Singapore labour statistics, answered with a source you can check." in HOME
    assert "cta('Open the workbench', '/workbench'" in HOME and "cta('View the deck', '/deck'" in HOME
    assert HOME.count("cta(") == 2


def test_assignment_weights_are_the_seven_rubric_weights():
    for weight, name in [("25%", "Evaluation and error analysis"), ("20%", "RAG and GenAI design"), ("15%", "GenAI concepts and MCP"),
                         ("10%", "Problem framing and data science"), ("10%", "Agent workflow"), ("10%", "Responsible AI"),
                         ("10%", "Reproducibility and communication")]:
        assert f"['{weight}', '{name}']" in STORY, name


def test_review_wording_is_the_honest_wording_and_has_no_timing():
    assert REVIEW_SENTENCE in STORY
    text = "".join(path.read_text(encoding="utf-8") for path in REPORT_JS)
    for banned in ("card by card", "each by my own click", "own clicks", "per card", "dwell", "minutes", "seconds per item", "quick clicks"):
        assert banned not in text, banned


def test_effort_was_not_varied_is_stated_plainly():
    assert "I did not vary reasoning effort." in STORY
    assert "provider default" in STORY


def test_process_section_covers_the_practices_with_sources():
    for practice in ("Written contract", "Milestone gates", "Decision log", "State in files", "Frozen results", "Rights scan", "Read-only tools", "Budget ledger"):
        assert practice in (STATIC / "js" / "report-process.js").read_text(encoding="utf-8"), practice
    for source in ("CLAUDE.md", "docs/decisions.md", "docs/progress.md", "docs/audit-and-logging.md", "SECURITY.md", "docs/human-review/e2e-review-summary.md", "experiments/heldout-v2/FREEZE.md"):
        assert source in STORY, source
    assert "AI reviewers, not human review" in STORY
    assert "section('work').decisions" in STORY, "the decision count must come from report.json"
    for stale in ("sandboxed", "explicit paths"):
        assert stale not in STORY, f"{stale}: not in the repository record"
    order = [m.start() for m in (re.search(f"id: '{i}'", STORY) for i in ("tools", "safety", "review", "ops", "process", "limits"))]
    assert order == sorted(order), "the process section sits after deployment and before the limits"


@pytest.mark.parametrize("path", REPORT_JS + [REPORT_CSS], ids=lambda p: p.name)
def test_copy_rules_no_dashes_internal_ids_or_hashes(path):
    text = path.read_text(encoding="utf-8")
    assert not re.search("[\u2013\u2014]", text), "em or en dash"
    assert not re.search(r"\bD-\d{3}\b", text), "decision number"
    assert not re.search(r"\b[0-9a-f]{7,}\b", text), "hash-like string"
    assert not re.search(r"eyebrow|status-dot|scroll cue|scroll to explore|Build \d|v\d+\.\d+\.\d+", text, re.I)
    assert "innerHTML" not in text and "insertAdjacentHTML" not in text


def test_no_other_typeface_and_no_external_urls_in_the_report_stylesheet():
    css = REPORT_CSS.read_text(encoding="utf-8")
    assert not re.search(r"font-family:[ \t]*(?![ \t]|var\()", css)
    assert not re.search(r"url\(\s*['\"]?(https?:|//)", css)
    assert "@import" not in css


def test_nothing_is_scrolled_by_a_window_listener():
    assert not re.search(r"addEventListener\(\s*['\"]scroll['\"]", "".join(path.read_text(encoding="utf-8") for path in REPORT_JS))


def test_imports_resolve_and_deck_graphics_exist():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    for path in REPORT_JS:
        text = path.read_text(encoding="utf-8")
        for names, target in re.findall(r"import \{([^}]*)\} from '(\.{1,2}/[^']+)'", text):
            resolved = (path.parent / target).resolve()
            assert resolved.is_file(), f"{path.name}: {target}"
            if resolved.name == "graphics.js":
                for name in (n.strip() for n in names.split(",")):
                    assert re.search(rf"export (?:function|const) {name}\b", graphics), f"graphics.js has no {name}"


def test_report_page_reuses_the_deck_charts_and_does_not_edit_them():
    for needle in ("presentation/graphics.js", "presentation/ch1-scope.js", "presentation/ch5-evaluation.js", "presentation/ch-work.js"):
        assert needle in "".join(p.read_text(encoding="utf-8") for p in REPORT_JS), needle


def test_every_number_the_copy_reads_is_in_report_json():
    report = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))
    ladder = report["retrieval"]["ladder"]
    for key in ("R0", "R1a", "R2", "R3"):
        assert isinstance(ladder["configs"][key]["hit@8"], float)
    assert ladder["n_cases"] > 0
    v2 = report["evaluation"]["heldout_v2"]
    for model in ("gpt-6-luna", "gpt-5.6-luna"):
        paired = v2["paired"][model]
        assert {"better", "worse", "paired_difference", "n_gold_cases"} <= set(paired)
    assert {"n_mismatches_primary_r3", "n_cases", "over_abstentions_primary_r3"} <= set(v2["error_analysis"])
    assert len(report["work"]["decisions"]) >= 40
    assert {"sources", "by_type"} <= set(report["sources"]["metrics"])
    assert report["sources"]["metrics"]["by_type"]["dataset_csv"] > 0
    for run in ("dev-A1", "dev-A3", "dev-X1", "dev-X2"):
        for model in ("gpt-6-luna", "gpt-5.6-luna", "gpt-4.1-mini") if run in ("dev-A1",) else ("gpt-6-luna",):
            assert any(row["id"] == f"experiments/eval/agent-{run}/{model}" for row in report["evaluation"]["rows"]), (run, model)
    assert {"compared_datasets", "identical_datasets", "matching_refusals", "different_outputs"} <= set(report["mcp"]["metrics"])
    assert report["security"]["rows"][0]["metrics"]["n_scored"] > 0
