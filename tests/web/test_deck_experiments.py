# ruff: noqa: F811
"""Offline notebook navigation and artifact integrity; never calls a provider."""

import json
import re
from pathlib import Path

import pytest

from test_deck_appendix import counts, deck_page, press_a  # noqa: F401
from test_workbench_controls import workbench_url  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "web/static/presentation"


def retrieval_data():
    return json.loads((DECK / "experiments-data.js").read_text().split("export default ", 1)[1].rstrip(";\n"))


def extra_data():
    return json.loads((DECK / "experiments-data-b.js").read_text().split("export const EXPERIMENTS_B = ", 1)[1].rstrip(";\n"))


def markdown_tables(path, section=None):
    text = path.read_text()
    if section:
        text = text.split(section, 1)[1]
    groups = re.findall(r"(?m)^\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n?)+", text)
    cells = lambda line: [v.strip() for v in line.strip("|").split("|")]
    return [(cells(lines[0]), [cells(line) for line in lines[2:]]) for lines in (g.strip().splitlines() for g in groups)]


def test_all_retrieval_markdown_tables_match_exact_source():
    for experiment in retrieval_data()["experiments"]:
        for table in experiment["tables"]:
            if "tableIndex" not in table:
                continue
            columns, rows = markdown_tables(ROOT / table["source"], table.get("section"))[table["tableIndex"]]
            assert table["columns"] == columns
            assert table["rows"] == rows
    prose = (ROOT / "docs/experiments/m3-dense-hybrid.md").read_text()
    assert "header off: hit@10 0.67, MRR 0.53. header on: hit@10 0.71, MRR 0.50" in prose
    e7 = next(e for e in retrieval_data()["experiments"] if e["id"] == "e7")
    assert e7["tables"][0]["rows"] == [["off", "0.67", "0.53"], ["on", "0.71", "0.50"]]


def test_machine_readable_tables_match_immutable_metrics():
    for e in retrieval_data()["experiments"]:
        for t in e["tables"]:
            if t.get("jsonMetrics"):
                metrics = json.loads((ROOT / t["source"]).read_text())["metrics"]
                assert t["rows"] == [[k, v["n_cases"], v["hit@8"], str(v["hit@8_ci95"]), v["hit@10"], v["mrr@10"]] for k, v in metrics.items()]
            elif t.get("jsonHeldout"):
                metrics = json.loads((ROOT / t["source"]).read_text())["results"][t["jsonHeldout"]]["metrics"]
                assert t["rows"] == [
                    [k, v["n"]] + [f"{v[m]['mean']} {v[m]['ci95']}" for m in ["chunk_hit@8", "strict_passage_hit@8", "mrr@10"]] for k, v in metrics.items()
                ]
            elif t.get("v31Series"):
                for row in t["rows"]:
                    v = json.loads((ROOT / f"experiments/runs/dev-R-V31-{row[0]}/metrics.json").read_text())["metrics"]
                    assert row[1:] == [v["hit@8"], str(v["hit@8_ci95"]), str(v.get("paired_hit@8_better_worse", "baseline"))]


def test_early_bm25_rows_also_match_machine_metrics():
    folders = {"e1": "dev-E1-chunking", "e2": "dev-E2-tokenisation", "e3": "dev-E3-bm25-params", "e4": "dev-E4-combined"}
    keys = ["hit@1", "hit@3", "hit@5", "hit@10", "page_hit@5", "mrr", "passage_recall@5", "ctx_words@5", "n_chunks", "latency_ms_p50"]
    for e in retrieval_data()["experiments"]:
        if e["id"] not in folders:
            continue
        for row in e["tables"][0]["rows"]:
            path = ROOT / "experiments/runs" / folders[e["id"]] / f"{row[0]}.metrics.json"
            metrics = json.loads(path.read_text())["metrics"]
            assert [float(value) for value in row[1:11]] == [metrics[key] for key in keys]


def test_worked_examples_are_exact_rights_safe_projections():
    allowed = {"chunk_id", "score", "words", "source_id", "locator", "relevant"}
    for e in retrieval_data()["experiments"]:
        assert e["measurement"] and e["fixed"] and e["limit"] and e["takeaway"]
        assert e["examples"], e["id"]
        for example in e["examples"]:
            source = [json.loads(line) for line in (ROOT / example["source"]).read_text().splitlines()]
            match = next(
                r
                for r in source
                if r["case_id"] == example["case_id"] and ("method" not in example or (r["method"] == example["method"] and r["set"] == example["set"]))
            )
            assert example["first_relevant_rank"] == match["first_relevant_rank"]
            assert example["ranked"] == [{k: v for k, v in r.items() if k in allowed} for r in match["ranked"][:3]]
            assert all(set(r) <= allowed for r in example["ranked"])


def numeric_tokens(value):
    text = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", str(value))
    return re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", text)


def leaves(value):
    if isinstance(value, dict):
        return list(value) + [leaf for child in value.values() for leaf in leaves(child)]
    if isinstance(value, list):
        return [leaf for child in value for leaf in leaves(child)]
    return [value]


def test_additional_group_table_numbers_are_in_named_artifacts():
    data = extra_data()
    assert {e["group"] for e in data} == {"generation", "agent", "threat"}
    for e in data:
        assert e["measurement"]["corpusOrSystem"] and e["doesNotShow"] and e["example"]["lines"]
        for t in ([e["table"]] if e.get("table") else []) + e.get("tables", []):
            path = ROOT / t["source"]
            source = path.read_text()
            # JSON must parse; inspect numeric leaves rather than matching raw JSON substrings.
            if path.suffix == ".json":
                values = leaves(json.loads(source))
            elif path.suffix == ".jsonl":
                values = [leaf for line in source.splitlines() if line.strip() for leaf in leaves(json.loads(line))]
            else:
                values = [source]
            available = [float(n) for value in values for n in numeric_tokens(value)]
            for cell in [cell for row in t["rows"] for cell in row[1:]]:
                for token in numeric_tokens(cell):
                    number = float(token)
                    # Cards may express a source fraction as a percentage, or round to 3 decimals.
                    assert any(abs(number - v) < 0.00051 or abs(number - v * 100) < 0.051 or abs(number * 100 - v) < 0.051 for v in available), (
                        e["id"],
                        t["source"],
                        token,
                    )


def test_notebook_modules_contain_no_private_report_text():
    from labourlens.data.rights_scan import build_shingles, scan

    passages = ROOT / "data/passages"
    if not passages.exists():
        pytest.skip("Private corpus unavailable; numeric projection schema is checked separately")
    files = [str(p.relative_to(ROOT)) for p in [DECK / "experiments-data.js", DECK / "experiments-data-b.js", DECK / "experiments.js"]]
    assert scan(files, build_shingles(passages), root=ROOT) == []


def press_e(page, times, **flags):
    page.evaluate(
        """({times, flags}) => {
      const original = performance.now;
      try { for (const time of times) {
        performance.now = () => time;
        (document.activeElement || document.body).dispatchEvent(new KeyboardEvent('keydown',
          {key: 'e', code: 'KeyE', keyCode: 69, bubbles: true, cancelable: true, ...flags}));
      }} finally { performance.now = original; }
    }""",
        {"times": times, "flags": flags},
    )


def test_experiments_hidden_by_default_and_no_key_clash(deck_page):
    p = deck_page
    assert counts(p)["total"] == 26
    assert p.locator("#experiments").count() == 0
    press_e(p, [0, 401])
    assert p.locator("#experiments").count() == 0
    press_e(p, [801])
    assert p.locator("#experiments.present").count() == 1
    assert p.locator(".deck-counter").inner_text() == "Experiments · 26 main"
    assert p.locator(".playback").count() == 0
    press_e(p, [1000, 1100])
    assert p.locator("#experiments").count() == 0
    assert p.locator(".slides > section.present").get_attribute("data-chapter") == "Start"
    assert counts(p)["counter"] == "1 / 26"
    assert p.locator(".progress span").evaluate("n => n.style.transform") == "scaleX(0)"
    p.keyboard.press("o")
    assert p.locator(".slides > section").count() == 26


def test_toggle_from_references_and_summary_preserves_a_a(deck_page):
    p = deck_page
    p.keyboard.press("Shift+ArrowRight")
    press_e(p, [1000, 1100])
    assert p.locator("#experiments.present").count() == 1
    press_e(p, [2000, 2100])
    press_a(p, [3000, 3100])
    p.keyboard.press("Shift+ArrowRight")
    assert p.locator(".slides > section.present").get_attribute("data-chapter") == "Appendix"
    press_e(p, [4000, 4100])
    assert p.locator("#experiments.present").count() == 1
    assert p.locator(".slides > section").count() == 45
    press_e(p, [5000, 5100])
    assert p.locator(".slides > section.present").get_attribute("data-chapter") == "Appendix"
    assert p.locator(".slides > section.present").get_attribute("data-title").startswith("Q. ")
    press_a(p, [6000, 6100])
    assert counts(p)["total"] == 26


@pytest.mark.parametrize(
    "title,card",
    [
        ("Does filtering help?", "experiment-r-series"),
        ("Agent - Functional Architecture", "experiment-agent-versus-fixed"),
        ("Attacks and defences", "experiment-threat-v2-challenge"),
        ("Data sources", None),
    ],
)
def test_e_e_opens_relevant_card_and_returns_to_same_slide(deck_page, title, card):
    p = deck_page
    n = p.evaluate("t => [...document.querySelectorAll('.slides > section')].findIndex(s => s.dataset.title === t) + 1", title)
    assert n > 0
    p.evaluate("n => { location.hash = '#/' + n; }", n)
    p.wait_for_function("t => document.querySelector('.slides > section.present')?.dataset.title === t", arg=title)
    press_e(p, [1000, 1100])
    assert p.locator("#experiments.present").count() == 1
    p.wait_for_timeout(300)
    if card:
        entry = p.locator(f"#{card}")
        assert entry.evaluate("n => n.open")
        assert entry.evaluate("n => { const r = n.getBoundingClientRect(); return r.top >= 0 && r.top < innerHeight; }")
    else:
        assert p.locator(".experiment-index").is_visible()
    press_e(p, [2000, 2100])
    assert p.locator("#experiments").count() == 0
    assert p.locator(".slides > section.present").get_attribute("data-title") == title


def test_e_e_ignores_modifiers_repeats_fields_and_interruption(deck_page):
    p = deck_page
    for i, flags in enumerate([{"repeat": True}, {"ctrlKey": True}, {"metaKey": True}, {"altKey": True}]):
        press_e(p, [1000 + i * 1000, 1100 + i * 1000], **flags)
    p.evaluate("() => {const input = document.createElement('input'); document.body.append(input); input.focus();}")
    press_e(p, [6000, 6100])
    p.locator("input").evaluate("n => n.remove()")
    press_e(p, [7000])
    p.keyboard.press("Shift")
    press_e(p, [7100])
    assert p.locator("#experiments").count() == 0
    p.keyboard.press("Shift+/")
    assert p.get_by_text("E E", exact=True).is_visible()
    assert p.get_by_text("Show or hide experiments (double press within 400 ms)", exact=True).is_visible()


@pytest.mark.parametrize("width", [1440, 1024])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_notebook_group_links_layout_and_offline_requests(deck_page, width, theme, tmp_path):
    p = deck_page
    errors, external = [], []
    p.on("pageerror", lambda error: errors.append(str(error)))
    origin = p.url.split("/deck.html")[0]
    p.on("request", lambda request: external.append(request.url) if not request.url.startswith(origin + "/") else None)
    p.set_viewport_size({"width": width, "height": 900})
    p.reload()
    p.wait_for_selector(".reveal.ready")
    p.evaluate("theme => {document.documentElement.dataset.theme = theme;}", theme)
    press_e(p, [1000, 1100])
    assert p.locator("#experiments.present").count() == 1
    for group in ["Retrieval", "Generation", "Agent", "Threat"]:
        p.get_by_role("link", name=group, exact=True).click()
        assert p.locator(f"#experiment-group-{group.lower()}").is_visible()
    p.get_by_role("link", name="Retrieval", exact=True).click()
    p.locator("#experiment-e1 > summary").click()
    p.screenshot(path=str(tmp_path / f"experiments-{width}-{theme}.png"))
    assert not errors and not external
    assert p.locator(".experiment-index").evaluate("n => getComputedStyle(n).position") == "sticky"
    press_e(p, [2000, 2100])
    assert p.locator("#experiments").count() == 0


def test_cards_explain_their_short_labels(deck_page):
    p = deck_page
    n = p.evaluate("t => [...document.querySelectorAll('.slides > section')].findIndex(s => s.dataset.title === t) + 1", "Does filtering help?")
    p.evaluate("n => { location.hash = '#/' + n; }", n)
    press_e(p, [1000, 1100])
    p.wait_for_timeout(300)
    card = p.locator("#experiment-r-series")
    labels = card.locator(".experiment-terms").inner_text()
    for term in ["R0", "R1a", "R1b", "R2", "R3", "hit@k"]:
        assert term in labels
    assert "Hard period/release filter" in labels
    glossary = p.locator("#experiment-glossary")
    glossary.locator("summary").click()
    assert "Reciprocal rank fusion" in glossary.inner_text()


def test_report_notebook_page_matches_deck_data():
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    run = subprocess.run([node, str(ROOT / "scripts/build_experiment_notebook.mjs"), "--check"], capture_output=True, text=True, cwd=ROOT)
    assert run.returncode == 0, run.stderr


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_production_options_tips_stay_inside_slide_and_escape_keeps_slide_view(deck_page, theme):
    page = deck_page
    page.evaluate("(theme) => document.documentElement.dataset.theme = theme", theme)
    index = page.locator(".slides > section").evaluate_all(
        "(nodes) => nodes.findIndex(node => node.dataset.title === 'Deploy in production')"
    )
    page.keyboard.press("Shift+ArrowLeft")
    for _ in range(index):
        page.keyboard.press("ArrowRight")
    for label, example in (("Protected access", "SSO"), ("API and workers", "deadlines"),
                           ("Model gateway", "budgets"), ("Read-only evidence", "allowlist"),
                           ("Around everything", "OpenTelemetry")):
        node = page.locator(f'.present svg [aria-label="{label}"]')
        node.hover()
        tip = page.locator(".present .production-tip-host.is-active > .deck-tip")
        assert example in tip.inner_text()
        bounds = tip.bounding_box()
        assert bounds and bounds["x"] >= 0 and bounds["y"] >= 0
        assert bounds["x"] + bounds["width"] <= 1440
        assert bounds["y"] + bounds["height"] <= 900
        node.focus()
        assert tip.is_visible()
        page.keyboard.press("Escape")
        assert not tip.is_visible()
        assert not page.locator(".reveal").evaluate("node => node.classList.contains('overview')")
        assert page.locator(".slides > section.present").get_attribute("data-title") == "Deploy in production"
