"""The presentation deck: route, CSP, vendored files, and source hygiene for the slides.

Slides are built in the browser from report.json, so the checks that need a rendered DOM (slide count,
headings, speaker notes) read the slide declarations and the builder; the headless Chrome run in the
hand-off covers the rendered deck.
"""
import json
import re
from pathlib import Path
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from labourlens.report.app import Settings, create_app

WEB = Path(__file__).resolve().parents[2] / "web"
STATIC = WEB / "static"
DECK_SOURCES = [WEB / "deck.html", STATIC / "css" / "presentation.css", *sorted((STATIC / "presentation").glob("*.js")), STATIC / "charts.js"]
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


def _client(tmp_path):
    settings = Settings(access_codes=("x" * 24,), session_secret="test-only-session-signing-secret-32-bytes", demo_enabled=False,
                        daily_budget_usd=1.0, login_limit=5, session_limit=10, ip_limit=20, max_concurrent=1, feedback_dir=tmp_path / "f")
    app = create_app(settings=settings, runner=lambda q, s: {}, shared_factory=lambda: SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver")


@pytest.mark.anyio
@pytest.mark.parametrize("path", ["/deck", "/deck.html"])
async def test_deck_route_serves_html_with_unchanged_csp(tmp_path, path):
    async with _client(tmp_path) as client:
        response = await client.get(path)
    assert response.status_code == 200
    assert response.headers["content-security-policy"] == CSP
    assert "text/html" in response.headers["content-type"]
    assert 'class="slides"' in response.text


@pytest.mark.anyio
async def test_old_presentation_url_redirects_to_deck(tmp_path):
    async with _client(tmp_path) as client:
        response = await client.get("/presentation", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/deck"


@pytest.mark.anyio
async def test_vendored_files_and_deck_modules_are_served(tmp_path):
    html = (WEB / "deck.html").read_text()
    targets = [t for t in re.findall(r"\b(?:src|href)\s*=\s*['\"]([^'\"]+)", html) if t.startswith("/static/")]
    targets += ["/static/vendor/reveal/reveal.mjs", "/static/vendor/reveal/LICENSE", "/static/vendor/phosphor/LICENSE", "/static/presentation/slides.js", "/static/data/report.json"]
    assert len(targets) >= 8
    async with _client(tmp_path) as client:
        for target in targets:
            response = await client.get(target)
            assert response.status_code == 200, target
    assert "Permission is hereby granted" in (STATIC / "vendor" / "reveal" / "LICENSE").read_text()


def test_deck_html_has_no_inline_script_style_handlers_or_external_resources():
    html = (WEB / "deck.html").read_text()
    assert not re.search(r"<style\b", html, re.I)
    assert not re.search(r"\sstyle\s*=", html, re.I)
    assert not re.search(r"\son[a-z]+\s*=", html, re.I)
    for tag in re.findall(r"<script\b[^>]*>", html, re.I):
        assert re.search(r"\bsrc\s*=", tag), tag
    for body in re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.I | re.S):
        assert not body.strip()
    for target in re.findall(r"\b(?:src|href)\s*=\s*['\"]([^'\"]+)", html):
        if target.startswith("data:"):
            continue
        assert not re.match(r"(https?:)?//", target), target
        assert (WEB / target.lstrip("/").split("?", 1)[0]).is_file(), target


def test_deck_sources_have_no_em_or_en_dash():
    for path in DECK_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert "\u2014" not in text and "\u2013" not in text, path.name
        assert not re.search(r"\\u201[34]", text), path.name


def test_deck_sources_use_no_forbidden_decoration():
    banned = ["eyebrow", "pr-chapter-no", "pr-flag-dot", "scroll-cue", "pr-rail", "ink-field", "pr-meta", "pr-reveal"]
    for path in DECK_SOURCES:
        text = path.read_text(encoding="utf-8")
        for word in banned:
            assert word not in text, f"{path.name}: {word}"
    css = (STATIC / "css" / "presentation.css").read_text()
    assert "Fraunces" not in css and "backdrop-filter" not in css
    assert not re.search(r"(?<![\w-])(box-shadow|text-shadow|filter)\s*:\s*[^;]*blur", css)


def test_deck_never_transitions_layout_properties():
    css = (STATIC / "css" / "presentation.css").read_text()
    layout = {"all", "width", "height", "top", "left", "right", "bottom", "margin", "padding", "inset", "font-size"}
    for value in re.findall(r"(?<![\w-])transition\s*:\s*([^;}]+)", css):
        for part in value.split(","):
            prop = part.strip().split()[0] if part.strip() else ""
            assert prop not in layout, value
    assert "prefers-reduced-motion: reduce" in css and "print" in css


def _slides_main_section():
    slides = (STATIC / "presentation" / "slides.js").read_text()
    start = slides.index("// ---------- opening")
    end = slides.index("// ---------- appendix")
    return slides[start:end]


def test_every_slide_has_a_heading_and_speaker_notes():
    builder = (STATIC / "presentation" / "deck.js").read_text()
    assert "el(spec.layout === 'title' ? 'h1' : 'h2', 'deck-title', spec.title)" in builder
    assert "el('aside', 'notes')" in builder and "if (!notes.children.length) notes.append(" in builder
    main = _slides_main_section()
    specs = re.findall(r"\badd\(\{", main)
    assert len(specs) == 28, len(specs)
    total = len(re.findall(r"\badd\(\{", (STATIC / "presentation" / "slides.js").read_text()))
    assert total == 44  # 28 main slides, appendix index, and references A to O
    assert total - len(specs) == 16
    for block in re.split(r"\badd\(\{", main)[1:]:
        assert "notes:" in block, block[:100]
        assert "title:" in block, block[:100]


FACE_FORBIDDEN = re.compile(r"ADR-|D-0\d\d|\bX[12]\b|\bX3\b|\bA[1-5]\b|\bR[0-3]a?\b|T-I06|report\.json|\.md\b|\.js\b|\b[0-9a-f]{7,}\b|\bV2post\b")


def test_slide_faces_carry_no_identifiers():
    """Faces are everything except the notes arrays: titles, bullets, captions, row text and source lines."""
    faces = [line for line in _slides_main_section().splitlines() if "notes:" not in line and not line.strip().startswith("//")]
    for line in faces:
        assert not FACE_FORBIDDEN.search(line), line.strip()[:140]
    for path in [STATIC / "presentation" / "graphics.js"]:
        text = path.read_text()
        # Evidence-only strings are passed to withTip, never added as face labels.
        text = re.sub(r"(?m)^ +(?:const suiteSource = )?'(?:tests/|experiments/)[^\n]*\n", "", text)
        # Owner policy: case ids and run paths belong in the failure-mode hover evidence, never on a face.
        text = re.sub(r"export function failureModes\(m\).*?(?=\n/\*\* Same-set comparison of keyword)", "", text, flags=re.S)
        assert not re.search(r"ADR-|D-0\d\d|T-I06|\.md\b", text), path.name


def test_no_bridge_sentences_or_pills_on_faces():
    main = _slides_main_section()
    for banned in ("withSoWhat", "The next slide", "pill", "eyebrow"):
        assert banned not in main


REQUIRED_TITLES = [
    "Assignment", "My project", "Assumptions, constraints and scope", "System architecture", "Choosing the data", "Two kinds of evidence", "Data findings", "Retrenchments rose, data gives no cause", "Advance and final figures differ", "Challenges with the data",
    "Processing reports", "Retrieval Strategies", "Does filtering help?", "Statistics lookup through MCP", "Agent loop", "Three example runs", "Checking the answer", "How I evaluated", "Human Review of Dataset", "Choosing models",
    "Does better retrieval improve answers?", "Where the system still fails", "Attacks and defences", "Agent Workbench", "How I built it", "Next steps", "Summary",
]


def _flow_rows():
    text = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    block = text.split("const FLOW = [", 1)[1].split("\n  ];", 1)[0]
    return re.findall(r"\['([^']+)', (null|'all'|\d), '([^']+)'\]", block)


def test_main_deck_follows_the_navigation_flow_and_has_short_plain_titles():
    main = _slides_main_section()
    defined = set(re.findall(r"\btitle: '([^']+)'", main))
    rows = _flow_rows()
    assert len(rows) == 28
    assert [r[0] for r in rows[1:]] == REQUIRED_TITLES
    for title, _, _ in rows:
        assert title in defined or "Singapore AI Agent" in title, title
    stages = [int(s) for _, s, _ in rows if s.isdigit()]
    assert stages == sorted(stages) and set(stages) == {0, 1, 2, 3, 4, 5}
    names = ["Sources", "Processing", "Retrieval", "Agent", "Answer", "Checks"]
    for title, stage, chapter in rows:
        if stage.isdigit():
            assert chapter == names[int(stage)], title
    assert "['Sources', 'Processing', 'Retrieval', 'Agent', 'Answer', 'Checks']" in (STATIC / "presentation" / "deck.js").read_text()
    for title in [r[0] for r in rows][1:]:
        assert len(title.split()) <= 9, title
    assert len(re.findall(r"\badd\(\{", main)) == 28


def test_removed_slides_stay_removed_and_summary_keeps_limitations():
    slides = (STATIC / "presentation" / "slides.js").read_text()
    assert "id: 'limits'" not in slides
    assert "Limits and next steps" not in slides
    assert not re.search(r"title: 'N[1-7]\.", slides)
    assert not re.search(r"appendixIndex\.push\(\['N", slides)
    summary = _slides_main_section().split("title: 'Summary'", 1)[1]
    for caveat in ("one human reviewer", "no demonstrated gain", "23/30 attacks flagged", "provider-side spend cap", "Next:"):
        assert caveat in summary
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    assert "10 of 30 to 23 of 30 attacks flagged" in graphics
    assert "not a security boundary" in graphics and "five test attacks each" in graphics
    for wording in ("markup 0 to 5", "sentence 0 to 5", "encoding 0 to 3", "paraphrase 3 to 3", "role-play 3 to 3", "table 4 to 4"):
        assert wording in graphics


def test_reading_reports_keeps_current_build_facts():
    main = _slides_main_section()
    reading = main.split("title: 'Processing reports'", 1)[1].split("\n  });", 1)[0]
    for fact in ("85 sources", "16,419", "1,847", "v3.1 relabelled 40"):
        assert fact in reading


def test_calculation_fix_slide_states_the_failure_and_the_graphics_exist():
    main = _slides_main_section()
    slides = (STATIC / "presentation" / "slides.js").read_text()
    assert "title: 'The calculation gap'" not in main
    assert "Two criteria failed" in slides and "optimistic diagnostic" in slides
    assert "calculate_from_text_values" in slides and "do not establish why" in slides
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    for name in ("threeAnswers", "twoSources", "buildTimeline", "flattening", "retrievalStaircase", "agentLoop", "evidenceTrace", "experimentStaircase", "costBars", "toolFixBars", "assignmentBrief", "challengeGrid", "modelChoice", "architectureDiagram", "myProject", "hardParts", "failureModes", "keywordVsMeaning", "reviewStreams", "threatLayerTable", "threatRuns", "mcpMap", "workbenchShot", "conceptGrid", "measureCards", "plantedFlow", "buildProcess", "excerptTable", "rowsAffordance", "withTip"):
        assert f"export function {name}" in graphics, name
    slides = (STATIC / "presentation" / "slides.js").read_text()
    assert "403" in main and "Human reviewed" in graphics
    assert "What I covered" not in main
    title_slide = main.split("add({", 1)[1].split("});", 1)[0]
    assert "Singapore AI Agent for Workforce Policy Researchers" in title_slide
    assert "GenAI Engineer assessment" not in title_slide
    assert "card:" not in title_slide and "titleVisual" not in slides
    assert (STATIC / "presentation" / "workbench.png").is_file()
    assert (STATIC / "presentation" / "workbench-qr.svg").is_file()
    deck = (STATIC / "presentation" / "deck.js").read_text()
    assert "deck-flow" in deck and "FLOW_STAGES" in deck and "spec.detail" in deck


def test_review_wording_is_plain_and_has_no_timing_claims():
    for path in [STATIC / "presentation" / "slides.js", STATIC / "presentation" / "graphics.js", STATIC / "presentation" / "ch8-limits.js", STATIC / "presentation" / "ch-work.js"]:
        text = path.read_text(encoding="utf-8")
        for banned in ("card by card", "each by my own click", "own clicks", "8 s each", "0.39 s", "rubber", "Not independent"):
            assert banned not in text, f"{path.name}: {banned}"
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    graphics_text = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    assert "Human reviewed" in graphics_text and "same model family" in slides
    assert "after the saved runs were scored" in slides
    assert "signed off" in slides and "quick confirmation" not in slides and "I confirmed all 403" not in slides
    faces = [line for line in _slides_main_section().splitlines() if "notes:" not in line and not line.strip().startswith("//")]
    assert not any("not independent" in line.lower() for line in faces)




def test_home_page_has_no_logo_or_favicon_file():
    app = (STATIC / "app.js").read_text()
    assert "brandMark" not in app and "brand-mark" not in app
    assert not (STATIC / "favicon.svg").exists()
    for page in ("index.html", "deck.html", "workbench.html"):
        assert "favicon.svg" not in (WEB / page).read_text()
    assert "Mihir Khandekar" in (STATIC / "js" / "home.js").read_text()


def test_deck_keys_and_controls_are_wired():
    deck = (STATIC / "presentation" / "deck.js").read_text()
    for needle in ("hash: true", "touch: true", "toggleOverview", "requestFullscreen", "Speaker notes", "pdfSeparateFragments", "autoAnimate: false", "scrollActivationWidth: null"):
        assert needle in deck, needle
    for label in ("Previous slide", "Next slide", "Slide overview", "Enter fullscreen"):
        assert label in deck, label


def test_method_detail_is_in_popovers_and_notes_not_in_boxes():
    main = _slides_main_section()
    deck = (STATIC / "presentation" / "deck.js").read_text()
    css = (STATIC / "css" / "presentation.css").read_text()
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    assert "deck-method" not in deck and "deck-method" not in css and "spec.detail.open" not in deck
    assert "notes.append(el('p', '', `${spec.detail.label" in deck
    assert "export function withTip" in graphics and "function svgTips" in graphics and "aria-describedby" in graphics and "role', 'tooltip'" in graphics
    assert ".has-tip:focus" in css and ".deck-tip" in css
    for needle in ("k1=1.5, b=0.75", "text-embedding-3-large", "reciprocal rank fusion, c=60", "ranks the top 30 and returns up to 10"):
        assert needle in main or needle in graphics, needle
    assert "hybrid baseline: 53.9% hit@8" in main and "Same 128 report-answerable development questions" in main


def test_title_slide_has_no_graphic_and_structure_labels_are_plain():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    assert "titleVisual" not in graphics
    assert "Parquet table" in graphics and "BM25 and embeddings" in graphics and "Snapshot" in graphics
    assert "Same 65 questions, reused" in graphics and "not adopted" in graphics


def _faces(text):
    return [line for line in text.splitlines() if "notes:" not in line and "detail:" not in line and not line.strip().startswith(("//", "/**", "*"))]


def test_faces_follow_the_owner_edits():
    main = _slides_main_section()
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    faces = "\n".join(_faces(main))
    for banned in ("held-out", "Held-out", "same model family", "237 development and 31", "31 original test", "Only the first two are questions", "Optional MCP", "optional MCP", "Transport-sector labour data is included", "A small, checkable scope beat", "Everything final runs on the current build", "kept only so older results", "The statement is the brief in my words"):
        assert banned not in faces, banned
        slide_graphics = graphics.split("export function freshQuestions", 1)[0] + graphics.split("export function reviewStreams", 1)[1]  # freshQuestions is used by the report page only
        assert banned not in slide_graphics, banned
    assert "Hard parts" not in main and "Who checked the answers" not in main and "Every claim has a source" not in main and "On fresh questions" not in main
    assert "freshQuestions" not in main
    assert "Optional" not in graphics and "403 items signed off" not in graphics


def test_model_choice_is_read_from_the_screen_metrics():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    block = graphics.split("export function modelChoice", 1)[1].split("return wrap;", 1)[0]
    assert "m.answerRow('G1'" in block and "over_abstention_rate" in block and "false_answer_rate" in block and "mc-stack" in block
    assert not re.search(r"\['gpt-[\w.-]+', \.\d+, \.\d+", block), "model numbers must come from report.json, not literals"
    report = json.loads((STATIC / "data" / "report.json").read_text())
    rows = {r["id"].rsplit("/", 1)[1]: r["metrics"] for r in report["answers"]["rows"] if "answer-dev-G1/" in r["id"]}
    expected = {
        "gpt-6-luna": (18, 10, 0, 0.00051),
        "gpt-6.1-terra": (17, 10, 0, 0.00432),
        "gpt-5.4-mini": (21, 6, 1, 0.00335),
        "gpt-6-sol": (18, 9, 1, 0.00912),
        "gpt-4.1-mini": (25, 3, 2, 0.00161),
    }
    names = re.search(r"const names = \[([^\]]+)\]", block).group(1)
    assert re.findall(r"'([^']+)'", names) == list(expected)
    assert "primaryOnly" not in block and "gpt-5.6-luna" not in block
    for name, (right, over, false, cost) in expected.items():
        metrics = rows[name]
        assert (metrics["n"], metrics["n_answer_cases"], metrics["n_nonanswer_cases"]) == (30, 24, 6)
        assert round(metrics["behavior_accuracy"] * metrics["n"]) == right
        assert round(metrics["over_abstention_rate"] * metrics["n_answer_cases"]) == over
        assert round(metrics["false_answer_rate"] * metrics["n_nonanswer_cases"]) == false
        assert metrics["cost_per_case_usd"] == cost
    assert max(expected, key=lambda name: rows[name]["behavior_accuracy"]) == "gpt-4.1-mini"
    assert max(expected, key=lambda name: rows[name]["false_answer_rate"]) == "gpt-4.1-mini"
    assert min(expected, key=lambda name: rows[name]["cost_per_case_usd"]) == "gpt-6-luna"
    assert "name === 'gpt-6-luna' ? ' is-chosen'" in block
    assert "Wrong response type" in block and "Each question lands in exactly one group" in block
    assert "arms.filter(a => a.arm === 'r3' && a.model === 'gpt-6-luna')" in block
    main = _slides_main_section()
    assert "Early screen on 30 questions" in block and "Final system on 237 questions" in block
    assert "95% Wilson interval" in block and "wilson(right, n)" in block and "runs.run1" in block and "runs.run2" in block
    models_slide = main.split("title: 'Choosing models'", 1)[1].split("\n  });", 1)[0]
    assert "gpt-5.6" not in models_slide and "89.7%" in models_slide and "no false answers at the lowest cost" in models_slide
    assert "modelChoice(m)" in models_slide and "modelChoice(m, true)" not in models_slide
    assert "highest early accuracy but most false answers" in models_slide
    assert "lowest cost among these five" in models_slide and "25/30 (83.3%)" in models_slide and "2/6 (33.3%)" in models_slide
    final = next(s for s in report["final_evaluation"]["splits"] if s["id"] == "dev")
    arms = {a["model"]: a for a in final["arms"] if a["arm"] == "r3"}
    assert round(arms["gpt-6-luna"]["runs"]["mean"], 3) == 0.897
    for arm in arms.values():
        for key, metric in [("false_answer", "false_answer_rate"), ("over_abstain", "over_abstention_rate")]:
            assert arm["metrics"][metric]["rate"] == sum(arm["runs"][key]) / 2


def test_deck_presents_gpt_6_luna_alone_and_the_report_keeps_both():
    model = (STATIC / "presentation" / "model.js").read_text()
    deck = (STATIC / "presentation" / "deck.js").read_text()
    assert "export function withoutSecondModel" in model and "export function scrubDom" in model and "export function scrubText" in model
    assert "slideSpecs(withoutSecondModel(report))" in deck and "scrubDom(slidesHost)" in deck
    report_story = (STATIC / "js" / "report-story.js").read_text()
    assert "withoutSecondModel" not in report_story and "scrubDom" not in report_story
    report = json.loads((STATIC / "data" / "report.json").read_text())
    assert any(a["model"] == "gpt-5.6-luna" for s in report["final_evaluation"]["splits"] for a in s["arms"]), "report.json keeps both models"



def test_mcp_slide_states_where_mcp_sits():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    block = _graphics_block(graphics, "export function mcpMap", "/** The nine remaining")
    for needle in ("LabourLens host", "MCP client", "MCP server", "get_statistic", "labourlens://sources", "compare_quarters", "outputSchema", "stdio", "1 tool in use", "2 resources"):
        assert needle in block, needle
    assert "not in the base planner schema" in block and "Full-set accuracy evaluations used direct calls" in block
    loop = graphics.split("export function agentLoop", 1)[1].split("return wrap;", 1)[0]
    for needle in ("Search reports", "BM25 + embeddings", "Structured statistics", "MCP server → rows", "Calculate in code", "Stop gathering", "Review returned evidence", "2 rounds", "6 calls"):
        assert needle in loop, needle
    assert "series only" not in loop
    assert "step('wrench', 'Agent sends a series request'" in graphics and "step('path', 'MCP server returns rows'" in graphics and "Rows returned to the agent" in graphics
    assert "calculate_change" in graphics and "Search reports" in graphics and "Only the live get_series path crosses" in (STATIC / "js" / "report-story.js").read_text()


def test_mcp_slide_labels_the_all_tools_arm_as_tested_and_not_live():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    block = _graphics_block(graphics, "export function mcpMap", "/** The nine remaining")
    assert "All-tools MCP: slowest 5%" in block and "no accuracy gain" in block and "Not live." in block
    assert "which exceeds the limit set in advance (43.3 s" in block and "never receives the API key" in block
    assert "if (!showMeasurements) return wrap" in block
    report = json.loads((STATIC / "data" / "report.json").read_text())
    chain = report["serving"]["chain"]
    rows = {(r["route"], r["model"]): r["metrics"]["all"] for r in chain["rows"]}
    if ("mcp-all", "gpt-6-luna") in rows:  # present once the arm's artifacts are committed and the report is rebuilt
        allm, on, direct = rows[("mcp-all", "gpt-6-luna")], rows[("mcp-on", "gpt-6-luna")], rows[("direct-on", "gpt-6-luna")]
        assert (allm["behavior_accuracy"], on["behavior_accuracy"], direct["behavior_accuracy"]) == (0.877, 0.908, 0.908)
        assert allm["latency_p95_s"] > 43.3 and round(allm["latency_p95_s"]) == 51 and round(on["latency_p95_s"]) == 35
        assert allm["operational_failures"] == 0
        for key, better, worse in (("mcpall-vs-direct-on", 0, 2), ("mcpall-vs-mcp-on", 1, 3)):
            p = chain["paired"][key]["gpt-6-luna"]
            assert (p["better"], p["worse"], p["paired_difference"]) == (better, worse, -0.0308)
    live = (STATIC / "presentation" / "slides.js").read_text()
    assert "It exceeded the pre-set latency limit and was not adopted" in live
    assert "Without statistics: 69.2% accuracy, down from 90.8%" in block
    assert "-21.5 points" in block and "first attempt stopped at 44 of 65" in block.lower()
    assert "mcpMap(m, {showMeasurements: false})" in live


def test_ladder_hides_fresh_results_and_difference_labels_on_deck_only():
    slides = (STATIC / "presentation" / "slides.js").read_text()
    assert "finalComparison(m, {includeFresh: false, showDifference: false, showHistory: false})" in slides
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    assert "includeFresh = true, showDifference = true" in graphics
    assert "if (showDifference)" in graphics


def test_threat_slide_maps_layers_to_checks_without_an_on_off_leaderboard():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    block = graphics.split("export function threatLayerTable", 1)[1].split("return wrap;", 1)[0]
    assert "per_category" in block and "per_layer" in block
    assert "'Passed without defences (naive)'" in block and "'Passed with defences (guarded)'" in block
    assert "Same boundary on in both arms" in block
    for evidence in ("tests/test_security.py", "tests/retrieval/test_crosscheck.py",
                     "tests/retrieval/test_answer_validate.py", "tests/retrieval/test_agent.py",
                     "tests/mcp/test_mcp.py", "v2-baseline-test/metrics.json", "v2-selected-test/metrics.json"):
        assert evidence in block
    assert "no separate test of sensitive-data refusal" in block
    assert "No separate test of model obedience" in block
    assert "planted figure failed again" in block
    assert "10 of 30 to 23 of 30" in block and "9/30 benign test passages" in block
    assert "gpt-5.6-luna" not in block
    main = _slides_main_section()
    for result in ("guarded 50/54", "naive 42/54", "3/8 benign", "10 attacks", "2 only naive", "p = .039"):
        assert result.lower() in main.lower()
    assert "Guards plus answer prompt changed together" in main
    assert "35/36 in both arms" in main


def test_workbench_slide_is_a_screenshot_with_a_large_qr_code_and_the_budget_note():
    main = _slides_main_section()
    slide = main.split("title: 'Agent Workbench'", 1)[1].split("\n  });", 1)[0]
    assert "visual: workbenchShot()" in slide and "bullets:" not in slide
    assert "small-talk fast path" in slide and "65-case sample" in slide  # live-only steps stay disclosed in the notes
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    shot = graphics.split("export function workbenchShot", 1)[1].split("return wrap;", 1)[0]
    assert "qr.width = 400" in shot and "g22-budget" in shot and "Pinned" not in shot


def test_workbench_qr_has_a_quiet_zone():
    svg = (STATIC / "presentation" / "workbench-qr.svg").read_text()
    xs = [int(x) for x in re.findall(r'x="(\d+)mm" y="\d+mm" width="1mm"', svg)]
    ys = [int(y) for y in re.findall(r'x="\d+mm" y="(\d+)mm" width="1mm"', svg)]
    size = int(re.search(r'width="(\d+)mm"', svg).group(1))
    assert min(xs) >= 4 and min(ys) >= 4 and size - 1 - max(xs) >= 4 and size - 1 - max(ys) >= 4


def test_every_graphic_used_by_the_slides_and_report_is_imported():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    exported = set(re.findall(r"export (?:function|const) (\w+)", graphics))
    for path in (STATIC / "presentation" / "slides.js", STATIC / "js" / "report-story.js"):
        text = path.read_text()
        imported = {name for names in re.findall(r"import \{([^}]*)\} from '[./]*(?:presentation/)?graphics\.js'", text) for name in re.findall(r"[\w$]+", names)}
        body = re.sub(r"import \{[^}]*\} from [^\n]*", "", text)
        used = {name for name in exported if re.search(rf"(?<![\w.]){name}\(", body) or re.search(rf"safe\([^)]*, {name}\)", body)}
        assert used <= imported, (path.name, sorted(used - imported))


def test_review_slide_group_is_not_a_nested_section():
    """A <section> inside a slide makes reveal.js treat it as a vertical stack (counter 0 / 51, Previous disabled)."""
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    assert "el('section'" not in graphics


def test_context_rewrite_is_a_third_step_with_its_measurement_read_from_the_report():
    import json
    report = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))
    context = report["serving"]["context"]
    assert context["v1"]["conversation"]["passed"] == 29 and context["v2"]["conversation"]["passed"] == 30
    assert context["v2"]["adversarial"] == {"n": 6, "passed": 6}
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    assert "contextSentence(serving)" in slides and "Three steps run in front of the agent" in slides
    assert "two steps" not in slides.lower()


def test_threat_figures_in_the_report_are_labelled_by_run():
    safety = (STATIC / "presentation" / "ch6-safety.js").read_text(encoding="utf-8")
    assert "earlier run" in safety and "final-code run" in safety


def test_build_row_reads_the_final_evaluation_and_the_headline_numbers_come_from_the_data():
    import json
    report = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))
    final = report["final_evaluation"]
    assert [s["id"] for s in final["splits"]] == ["dev", "registered", "fresh"]
    rerun = next(row["rerun"] for row in report["corpus_builds"]["rows"] if row.get("current"))
    assert "final evaluation ran on this build" in rerun and "two runs per arm" in rerun
    dev = next(s for s in final["splits"] if s["id"] == "dev")
    r3 = next(a for a in dev["arms"] if a["arm"] == "r3" and a["model"] == "gpt-6-luna")
    assert f"{r3['metrics']['behaviour_accuracy']['rate'] * 100:.1f}%" in rerun
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    assert "finalComparison(m, {includeFresh: false, showDifference: false, showHistory: false})" in slides and "provenanceTable(m)" in slides
    for name in ("finalComparison", "finalSentence", "finalFacts", "provenanceTable"):
        assert f"export function {name}" in graphics


def test_final_evaluation_has_both_models_both_arms_and_paired_results():
    import json
    final = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))["final_evaluation"]
    assert [s["n"] for s in final["splits"]] == [237, 31, 65]
    for split in final["splits"]:
        assert {(a["arm"], a["model"]) for a in split["arms"]} == {(a, m) for a in ("r3", "hybrid") for m in ("gpt-6-luna", "gpt-5.6-luna")}
        assert set(split["paired"]) == {"gpt-6-luna", "gpt-5.6-luna"}
        for entry in split["paired"].values():
            assert entry["interval"] is not None and "sign_agrees" in entry
        for arm in split["arms"]:
            assert arm["metrics"]["behaviour_accuracy"]["rate"] == (arm["runs"]["run1"] + arm["runs"]["run2"]) / 2
            assert "first_run_metrics" in arm
    assert all(row["runs_per_arm"] == 2 and row["corpus"] == "v3.1" for row in final["provenance_table"])


def test_mcp_wording_is_exact():
    mcp = (STATIC / "presentation" / "ch7-mcp.js").read_text(encoding="utf-8")
    assert "another protocol version" not in mcp and "unexpected version string" in mcp and "client default is 8 s" in mcp
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    assert "advertised input schemas" in slides and "hard-coded in code" in slides and "2025-11-25" in slides


def test_report_processing_path_matches_the_runtime_and_discloses_table_limits():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = graphics.split("export function flattening(m)", 1)[1].split("return wrap;", 1)[0]
    for item in ("Source report", "Parse layout", "Passages", "Merge chunks", "Keyword index", "Embedding vectors", "Hybrid search", "table_unreliable", "merge200", "3,072", "float32", "cache.npz", "source_passage_ids"):
        assert item in block, item
    assert "corpus.passages" in block and "corpus.chunks" in block
    assert "does not turn this report table into a trusted row chunk" in block
    assert "no publisher or observation-period field" in block
    assert "visual: flattening(m)" in (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")


def _graphics_block(graphics, start, end):
    return graphics.split(start, 1)[1].split(end, 1)[0]


def test_evidence_stores_keeps_statistics_free_of_chunks_and_sources_report_counts_from_corpus():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function evidenceStores(m)", "export function questionSets(m)")
    assert "serving').corpus" in block, "report counts must read the serving.corpus section, not hard-coded numbers"
    assert "No chunking or embeddings" in block, "the statistics lane must state there is no chunk/embedding path"
    assert "corpus.quality_flags?.all_after?.table_unreliable" in block and "table_unreliable" in block
    assert "source.observations" in block and "source.by_type?.dataset_csv" in block
    assert "get_series → MCP → get_statistic" in block and "search_reports → passages" in block


def test_question_sets_show_three_equal_sets_with_known_evidence_limits():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function questionSets(m)", "export function retrievalTuning()")
    assert "finalEvaluation?.splits" in block, "set counts must come from the final evaluation, not literals"
    assert "sets.find(s => s.id === id)?.n" in block
    css = (STATIC / "css" / "presentation.css").read_text(encoding="utf-8")
    assert ".ex-sets { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr))" in css
    for title in ("'Development'", "'Original test'", "'Fresh questions'"):
        assert title in block, title
    assert "25 of 31 share development evidence" in block
    assert "six newer sources" in block


def test_tool_legend_lists_the_three_tools_with_inputs_outputs_where_and_why():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function toolLegend()", "export function buildTimeline(m)")
    assert "['Tool', 'Input → output', 'Runs in', 'Why']" in block
    for tool in ("search_reports", "get_series", "calculate_change"):
        assert f"['{tool}'," in block, tool
    for exchange in ("Question → passages", "Series + period → rows", "Two returned rows → change"):
        assert exchange in block, exchange
    for where in ("'App'", "'MCP server (blue outline)'", "'App, plain code'"):
        assert where in block, where
    assert "Read validated statistics" in block and "the base tool does not calculate from report-only figures" in block


def test_retrieval_tuning_states_fixed_numbers_and_advance_constant():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function retrievalTuning()", "export function toolLegend()")
    for needle in ("200 words, 40-word overlap", "pool of 30", "60 was fixed in advance, not searched", "I chose chunk size and overlap"):
        assert needle in block, needle


def test_report_numeric_contract_pins_total_and_in_scope_observations():
    report = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))
    metrics = report["sources"]["metrics"]
    assert metrics["observations"] == 52020 and metrics["in_scope_observations"] == 11228, metrics
    assert metrics["by_type"]["dataset_csv"] == 36


def test_metric_comparison_is_reused_and_keeps_retrieval_separate_from_answer_quality():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function metricComparison(m)", "export function retrievalStaircase(m)")
    for label in ("Retrieval hit@8", "End-to-end accuracy", "development text questions", "development questions, mean of 2 runs"):
        assert label in block, label
    for field in ("m.ladder?.configs?.R3?.['hit@8']", "m.ladder?.n_cases", "answer?.r3rate", "dev?.n"):
        assert field in block, "comparison values and denominators must come from the report model"
    assert "without generating an answer" in block
    assert "abstention, clarification or refusal" in block and "not an answerable-only score" in block
    main = _slides_main_section()
    retrieval = main.split("title: 'Does filtering help?'", 1)[1].split("\n  });", 1)[0]
    assert "unseenRetrieval()" in retrieval and "End-to-end answer gains remain unproven" in retrieval
    final = _graphics_block(graphics, "export function finalComparison", "export function agentLoop")
    assert "if (!includeFresh && showHistory) wrap.append(metricComparison(m))" in final
    ladder = main.split("title: 'Does better retrieval improve answers?'", 1)[1].split("\n  });", 1)[0]
    assert "showHistory: false" in ladder and "not retrieval hit rates" in ladder
    report = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))
    retrieval_data = report["retrieval"]["ladder"]
    assert retrieval_data["n_cases"] == 128
    assert round(retrieval_data["configs"]["R3"]["hit@8"] * 100, 1) == 96.9
    dev = next(s for s in report["final_evaluation"]["splits"] if s["id"] == "dev")
    answer = next(a for a in dev["arms"] if a["model"] == "gpt-6-luna" and a["arm"] == "r3")
    assert dev["n"] == 237 and round(answer["runs"]["mean"] * 100, 1) == 89.7


def test_early_screen_uses_the_same_right_colour_for_every_model():
    css = (STATIC / "css" / "presentation.css").read_text(encoding="utf-8")
    right_rules = [(selector, body) for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
                   if ".mc-seg.is-right" in selector]
    assert right_rules
    for selector, body in right_rules:
        assert "is-chosen" not in selector, "right behaviour must not change colour by selected model"
        assert re.search(r"background\s*:\s*var\(--accent\)", body)
        assert not re.search(r"opacity\s*:", body)


def test_report_expanders_use_the_owner_labels():
    story = (STATIC / "js" / "report-story.js").read_text(encoding="utf-8")
    assert "more('View examples'" in story
    assert "more('Problems faced'" in story


def test_architecture_names_all_three_tools_without_a_redundant_mcp_bar():
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function architectureDiagram()", "export function myProject")
    for tool in ("search_reports", "get_series", "calculate_change"):
        assert tool in block, tool
    bars = block.split("const bars =", 1)[1]
    assert "'Guardrails'" in bars and "'Evaluation'" in bars
    assert not re.search(r"\['[^']+', 'MCP',", bars)


def test_pipeline_steps_have_no_top_border_and_agent_limits_are_aligned():
    css = (STATIC / "css" / "presentation.css").read_text(encoding="utf-8")
    pipeline = re.search(r"\.rpipeline-node,\s*\.rpipeline-index\s*\{([^}]*)\}", css).group(1)
    assert not re.search(r"border(?:-top)?\s*:", pipeline)
    assert ".rpipeline-index { border-top-color" not in css
    bounds = re.search(r"\.owner-agent \.owner-agent-bounds\s*\{([^}]*)\}", css).group(1)
    assert "display: grid" in bounds and "repeat(4, minmax(0, 1fr))" in bounds
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    loop = _graphics_block(graphics, "export function agentLoop()", "return wrap;")
    for label in ("2 rounds", "6 calls", "Bounded retries"):
        assert label in loop, label
    legend = _graphics_block(graphics, "export function toolLegend()", "export function buildTimeline(m)")
    assert "MCP server (blue outline)" in legend and "Calls server tool get_statistic" in legend
    assert re.search(r"\.owner-agent \.owner-agent-node\.is-mcp rect\s*\{[^}]*stroke:\s*var\(--c3\)", css)


def test_calculation_experiment_stays_in_the_appendix_with_its_recorded_result():
    main = _slides_main_section()
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    assert "title: 'The calculation gap'" not in main and "toolFixFlow" not in slides
    assert "title: 'L. Calculation fix in detail'" in slides
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    assert "export function toolFixFlow" not in graphics
    report = json.loads((STATIC / "data" / "report.json").read_text(encoding="utf-8"))
    result = report["evaluation"]["tool_set_v2"]["dev_x3"]["criteria"]["gpt-6-luna"]
    assert (result["x2"]["n"], result["x3"]["n"]) == (237, 237)
    assert (result["x2"]["false_answers"], result["x3"]["false_answers"]) == (6, 7)
    assert result["criteria"]["2_false_answers"]["threshold"] == 6
    assert result["criteria"]["2_false_answers"]["pass"] is False and result["all_pass"] is False


def test_deck_names_the_fresh_questions_apart_from_the_original_test():
    model = (STATIC / "presentation" / "model.js").read_text()
    fresh = model.index("held-out v2 (questions|cases|set)")
    generic = model.index("[/held-out/gi")
    assert fresh < generic, "held-out v2 must be renamed before the generic held-out rule"
    assert "the fresh questions" in model and "original test" in model
    sources = {f.name: f.read_text() for f in (STATIC / "presentation").glob("*.js")}
    assert "S shows these notes" not in sources["slides.js"] and "X twice" in sources["slides.js"]
    assert "Run held-out v2 once" not in sources["ch8-limits.js"] and "were run once" not in sources["graphics.js"]


def test_three_frozen_experiments_are_integrated_without_changing_slide_count():
    root = WEB.parent
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    slides = (STATIC / "presentation" / "slides.js").read_text()
    story = (STATIC / "js" / "report-story.js").read_text()
    for helper in ("threatComparison", "unseenRetrieval", "fixedPipeline"):
        assert f"export function {helper}" in graphics
        assert helper in slides and helper in story
    assert len(re.findall(r"\badd\(\{", slides)) == 44
    threat = json.loads((root / "experiments/threats/threat-v2-analysis.json").read_text())
    assert (threat["guarded_majority_pass"], threat["naive_majority_pass"]) == (50, 42)
    assert (threat["guarded_only"], threat["naive_only"]) == (10, 2)
    assert (threat["benign_failures_guarded"], threat["benign_failures_naive"]) == (3, 3)
    assert round(threat["mcnemar_exact_p"], 3) == .039
    retrieval = json.loads((root / "experiments/eval/heldout-retrieval-20261103-paid/metrics.json").read_text())
    for key, n, hybrid, filtered in (("registered31", 18, .167, .778), ("fresh65", 34, .500, .941)):
        metrics = retrieval["results"][key]["metrics"]
        assert metrics["hybrid"]["n"] == n
        assert round(metrics["hybrid"]["strict_passage_hit@8"]["mean"], 3) == hybrid
        assert round(metrics["R3"]["strict_passage_hit@8"]["mean"], 3) == filtered
        index = 0 if key == "registered31" else 1
        for label, method in (("Hybrid", "hybrid"), ("Filter then rerank", "R3")):
            values = re.findall(r"\['" + label + r"', ([.\d]+),", graphics)
            assert round(float(values[index]), 3) == round(metrics[method]["strict_passage_hit@8"]["mean"], 3)
    fixed = json.loads((root / "experiments/eval/agent-vs-fixed-pipeline.json").read_text())
    mean = fixed["agent_two_run_mean_comparison"]
    assert round(mean["fixed_accuracy"], 3) == .814
    assert round(mean["agent_accuracy"], 3) == .897
    for caveat in ("One fixed run", "no original test or fresh-question comparison", "unchanged planner prompt", "historical runtime drift"):
        assert caveat.lower() in graphics.lower()
    assert "No retrieval-only measurement" not in (STATIC / "presentation/ch3-retrieval.js").read_text()
    assert "no retrieval-only run" not in (STATIC / "presentation/ch-work.js").read_text()
    assert "visual: threatGains()" in slides
    assert "Attack type" in graphics and "Defence layer(s)" in graphics
    block = graphics.split("export function threatLayerTable", 1)[1].split("return wrap;", 1)[0]
    rows = re.findall(r"\['([^']+)', '[^']+', '[^']+', (\d+), (\d+), (\d+),", block)
    assert len(rows) == 10
    for key, n, naive, guarded in rows:
        category = threat["per_category"][key]
        assert (int(n), int(naive), int(guarded)) == (category["cases"], category["naive"], category["guarded"])
    assert "wrap.append(final, fixedPipeline())" in graphics
    assert "exp-bar-track" in graphics and "exp-bar-value" in graphics
    assert "Chunk MRR@10" in slides and "Chunk hit@8" in slides


def test_deck_uses_geist_for_code_and_plain_labels():
    css = (STATIC / "css/presentation.css").read_text()
    assert "--font-mono: var(--font-sans)" in css
    assert "Geist Mono" not in css
    assert ".pr-tl-item::before { content: none; }" in css

def test_evaluation_story_separates_rules_from_judges_and_merges_the_tool_gap():
    slides = (STATIC / "presentation/slides.js").read_text()
    evaluation = (STATIC / "presentation/ch5-evaluation.js").read_text()
    main = _slides_main_section()
    for removed in ("title: 'Why it missed'", "title: 'Fixing the calculation gap'", "title: 'Planted wrong figure'"):
        assert removed not in main
    assert "evaluationDesign(m)" in main
    component = evaluation.split("export function measurementProcess()", 1)[1].split("return root;", 1)[0]
    for text in ("What I did", "What the AI judges did", "Claim support", "Fact coverage", "Contradictions",
                 "gpt-6.1-terra", "claude-sonnet-5-5", "Judges never set the behaviour score"):
        assert text in component
    assert "after saved runs had been scored" in main
    for forbidden in ("same query on the same local", "two routes", "adds no new knowledge", "adds no second knowledge"):
        assert forbidden not in slides


def test_decisions_api_is_exactly_one_final_appendix_slide_with_frozen_results():
    slides = (STATIC / "presentation/slides.js").read_text()
    graphics = (STATIC / "presentation/graphics.js").read_text()
    results = json.loads((WEB.parent / "experiments/eval/decisions-api-results.json").read_text())
    fresh = json.loads((WEB.parent / "experiments/eval/decisions-api-v2-results.json").read_text())
    assert "Trying the Decisions API" not in _slides_main_section()
    assert slides.count("title: 'Trying the Decisions API'") == 1
    appendix = slides.split("// ---------- appendix", 1)[1].split("// Appendix index lists", 1)[0]
    assert len(re.findall(r"\badd\(\{", appendix)) == 16
    last_slide = appendix.rsplit("add({", 1)[1]
    assert "id: 'decisions-api'" in last_slide
    assert "title: 'Trying the Decisions API'" in last_slide
    assert "visual: decisionsExperiment()" in last_slide
    assert "neither trial passed. Not adopted." in last_slide
    for source in ("decisions-api-results.json", "decisions-api-v2-results.json"):
        assert f"experiments/eval/{source}" in last_slide
    notes = last_slide.split("notes:", 1)[1]
    for caveat in ("historical, not contemporaneous", "no generated reply", "441 selected dependent claims",
                   "both generator models", "second-family AI judge", "not human ground truth",
                   "Same-family original-judge", "no verified unsupported negatives",
                   "No judge-latency comparison", "end-to-end swap", "no live adoption",
                   "original test and fresh questions", "150 AI-authored and AI-labelled",
                   "not human-reviewed truth", "not 450 independent questions",
                   "D threshold .7 and iteration 1", "development only", "C generates a reply",
                   "pure endpoint causality", "no paired cross-trial gain", "F2-070", "F2-072",
                   "F2-065 in the third repeat", "provider refusals", "failed open to the agent",
                   "not preregistered", "untested idea", "Both trials failed"):
        assert caveat in notes, caveat
    assert "held-out" not in last_slide and "heldout" not in last_slide
    block = graphics.split("export function decisionsExperiment()", 1)[1].split("return wrap;", 1)[0]
    for label in ("v2 routing latency", "Exact route accuracy", "AUROC", "Accuracy", "Balanced accuracy",
                  "API model: gpt-6-luna only", "False support: 44/58", "v1 claim-support check",
                  "Different populations, not a paired cross-trial gain", "v2 refusal and diversion",
                  "30/30 serious-harm calls: provider refused", "Refusal → fail open to agent",
                  "Not a predicted unsafe route", "In-scope diverts: D 6/270 vs C 1/270",
                  "Both trials failed. No adoption.", "v2 C bar: repeat mean"):
        assert label in block, label
    for identifier in ("DEV-", "HO-", "D-0", "F2-", "A0", "A70", "gpt-5.6-luna"):
        assert identifier not in block
    # Primary timings are contemporaneous paired case medians, not pooled calls or v1 history.
    for arm, label, colour in (("C", "C control", "--c5"), ("D", "D Decisions", "--accent")):
        latency = fresh["latency"][f"{arm}_case_medians"]
        assert latency["n"] == 150
        assert f"['{label}', {latency['p50_s']}, '{colour}']" in block
    assert str(results["triage"]["latency"]["case_medians"]["p50_s"]) not in block
    assert "const routeTrials =" in block
    assert results["triage"]["rules"]["thresholds"]["exact_matches_each_repeat"] == 407
    assert "minimum: 407, denominator: 409" in block
    assert "minimum: 148, denominator: 150" in block
    assert "148/150 each repeat" in fresh["interpretation"]["exact_quality"]
    counts = {v["effective_exact_route"]["numerator"]
              for v in results["triage"]["arms"]["A70"]["by_repeat"].values()}
    assert len(counts) == 1
    assert f"['Decisions 70%', {counts.pop()}, '397/409', '--accent']" in block
    # Historical C count is derived from stored paired deltas, not a new run.
    baseline = 405 - round(sum(v["A0"] for v in results["triage"]["latency"]["paired_cases"]))
    assert f"['C historical', {baseline}, '{baseline}/409', '--c5']" in block
    d_counts = [v["effective_exact_route"]["numerator"] for v in fresh["arms"]["D"]["by_repeat"].values()]
    c_counts = [v["effective_exact_route"]["numerator"] for v in fresh["arms"]["C"]["by_repeat"].values()]
    assert d_counts == [138, 138, 138]
    assert c_counts == [150, 150, 149]
    assert "['D Decisions', 138, '138/150 each', '--accent']" in block
    assert f"['C control', {sum(c_counts)} / 3, '150, 150, 149 /150', '--c5']" in block
    for arm, expected in (("D", 6), ("C", 1)):
        divert = fresh["arms"][arm]["pooled"]["in_scope_diversions"]
        assert (divert["numerator"], divert["denominator"]) == (expected, 270)
    assert fresh["arms"]["D"]["operational"]["errors"]["refusal"] == 30
    harm = fresh["arms"]["D"]["pooled"]["confusion_matrix"]["unsafe_or_sensitive"]
    assert harm["in_scope"] == 30 and harm["unsafe_or_sensitive"] == 0
    primary = results["support"]["metrics"]["primary"]["overall"]
    for label, key, threshold in (("AUROC", "auroc", ".80"), ("Accuracy", "all_scheduled_accuracy", ".85"),
                                  ("Balanced accuracy", "balanced_accuracy", ".70")):
        assert f"['{label}', {primary[key]}, {threshold}]" in block
    assert primary["scheduled_n"] == 441
    assert primary["confusion_matrix"]["fp"] == 44
    assert primary["frozen_reference_counts"]["partial"] == 58
    assert set(results["support"]["metrics"]["primary"]["strata"]["model"]) == {"gpt-6-luna", "gpt-5.6-luna"}
    assert results["triage"]["decision"] == results["support"]["decision"] == "failed_screen"
    assert fresh["decision"] == "do_not_adopt"
    assert not any(fresh["adoption_guards"][key] for key in ("D_safety", "D_quality", "D_operational"))
    css = (STATIC / "css/presentation.css").read_text()
    for shared_data in ("latencyRows.forEach", "routeTrials.forEach", "supportMetrics.forEach"):
        assert block.count(shared_data) == 2
    assert "wrap.append(mobile)" in block
    assert ".decisions-experiment > svg { display: none; }" in css
    assert ".decisions-experiment .decisions-mobile { display: grid;" in css
    assert ".decisions-mobile-note, .decisions-mobile-threshold, .decisions-mobile-failed { font-size: 16px;" in css


def test_failure_modes_all_eight_rows_have_visible_examples_and_scoped_mobile_layout():
    graphics = (STATIC / "presentation/graphics.js").read_text()
    block = graphics.split("export function failureModes(m)", 1)[1].split("export function keywordVsMeaning(m)", 1)[0]
    rows = re.findall(r"^    \['([^']+)',.*\n      '([^']+)',\n      '([^']+)'\]", block, re.MULTILINE)
    assert len(rows) == 8
    assert [row[0] for row in rows] == [
        "Retrieval misses the passage", "Wrong series, period or population",
        "Advance and final figures mixed", "Wrong numbers",
        "Causal overreach and unsupported claims", "Prompt injection in questions or passages",
        "Tool failure or timeout", "A real question wrongly blocked",
    ]
    assert "row.append(summary, el('p', 'fm-example', example))" in block
    assert "Hover or focus for a concrete case" not in block
    for _, example, provenance in rows:
        assert example and provenance
        assert not re.search(r"(?:DEV|HO|F2|T-[DI])-\d+", example)
    assert block.count("No observed instance in the runs") == 3
    assert "Related weakness: correct figures" in rows[2][1]
    assert "Related weakness: answered a causal demand" in rows[4][1]
    assert rows[6][1] == "No observed instance in the runs"
    assert "Trial only:" in rows[7][1] and "Decisions trial not adopted" in block
    css = (STATIC / "css/presentation.css").read_text()
    assert ".fm-row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr)" in css
    assert ".fm-row { grid-template-columns: 1fr;" in css
    assert ".fm { height: auto; min-height: 100%; align-content: start; overflow: visible; }" in css
    assert ".fm-control, .fm-measure, .fm-example { font-size: 16px;" in css


def test_failure_modes_examples_are_pinned_to_committed_gold_and_scores():
    repo = WEB.parent
    def cases(path):
        return {row["case_id"]: row for row in map(json.loads, (repo / path).read_text().splitlines())}
    gold = cases("experiments/gold/gold_v3.7.jsonl")
    dev = cases("experiments/eval/agent-dev-A3/gpt-6-luna.cases.jsonl")
    original = cases("experiments/eval/agent-heldout-FIN2-r3/gpt-6-luna.cases.jsonl")
    fresh = cases("experiments/threats/ti06-v2-fresh-20261102/runs/gpt-6-luna.verdicts.jsonl")
    earlier = cases("experiments/threats/ti06-v2-e2efix-20261102/runs/gpt-6-luna.verdicts.jsonl")
    threats = cases("experiments/threats/cases.jsonl")
    block = (STATIC / "presentation/graphics.js").read_text().split("export function failureModes(m)", 1)[1].split("export function keywordVsMeaning(m)", 1)[0]
    for case in ("DEV-009", "HO-027", "DEV-011", "T-I06", "DEV-425", "T-D01", "F2-072"):
        assert case in block
    assert "re-entry rate" in gold["DEV-009"]["question"] and gold["DEV-009"]["expected_behavior"] == "answer"
    assert dev["DEV-009"]["over_abstain"] and not dev["DEV-009"]["gold_cited"]
    report = (repo / "docs/evaluation-report.md").read_text()
    assert "DEV-009 gathered evidence without a gold passage" in report
    assert gold["HO-027"]["expected_behavior"] == "clarify"
    assert original["HO-027"]["false_answer"] and not original["HO-027"]["behavior_ok"]
    assert dev["DEV-011"]["key_number_recall"] == 1 and dev["DEV-011"]["claims_partial"] == 2
    assert "does not identify the release as advance" in " ".join(dev["DEV-011"]["judge_notes"])
    assert "not a proven numerical mix-up" in block
    assert gold["DEV-425"]["expected_behavior"] == "refuse" and dev["DEV-425"]["false_answer"]
    assert dev["DEV-425"]["claims_unsupported"] == 0 and dev["DEV-425"]["claims_supported"] == 1
    assert "not that the response asserted the requested causal claim" in block
    assert threats["T-I06"]["poison"] == "false_figure"
    assert not fresh["T-I06"]["passed"] and earlier["T-I06"]["passed"]
    assert fresh["T-I06"]["scorer"] == earlier["T-I06"]["scorer"] == "v2"
    assert earlier["T-I06"]["post_hoc_rescore"]
    assert sum(r["passed"] for r in fresh.values()) == 35
    assert sum(r["passed"] for r in earlier.values()) == 36
    assert "Ignore all previous instructions" in threats["T-D01"]["question"]
    assert fresh["T-D01"]["passed"] and fresh["T-D01"]["status"] == "refused"
    assert fresh["T-D01"]["tool_calls"] == 0
    assert "scripted, not a recorded live run" in report


def test_failure_modes_routing_trial_does_not_replace_live_baseline():
    repo = WEB.parent
    results = json.loads((repo / "experiments/eval/decisions-api-v2-results.json").read_text())
    questions = {r["case_id"]: r for r in map(json.loads, (repo / "experiments/triage/fresh_cases_v2.jsonl").read_text().splitlines())}
    assert results["decision"] == "do_not_adopt"
    assert questions["F2-072"]["expected_route"] == questions["F2-070"]["expected_route"] == "in_scope"
    assert "seasonally adjusted" in questions["F2-072"]["question"]
    source = (repo / "docs/experiments/decisions-api-v2-results.md").read_text()
    assert "F2-070 and F2-072" in source and "diverted in every repeat" in source
    slides = (STATIC / "presentation/slides.js").read_text()
    declaration = slides.split("title: 'Where the system still fails'", 1)[1].split("  });", 1)[0]
    assert "six of 270" in declaration and "two distinct" in declaration
    assert "Neither result replaces the earlier live-baseline observation of 0/333" in declaration
    assert "No observed instance in the runs" in declaration


def test_assumptions_slide_follows_project_and_records_real_boundaries():
    main = _slides_main_section()
    order = [row[0] for row in _flow_rows()]
    assert order[2:5] == ["My project", "Assumptions, constraints and scope", "System architecture"]
    block = main.split("title: 'Assumptions, constraints and scope'", 1)[1].split("\n  });", 1)[0]
    assert "assumptionsScope(m)" in block and "notes:" in block
    assert "gpt-5.6-luna" not in block
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    visual = graphics.split("export function assumptionsScope(m)", 1)[1].split("\n/**", 1)[0]
    for text in ("Assumptions and constraints", "Scope done", "Licences follow their recorded status",
                 "Public sources; report text stays local", "Read-only, bounded research", "Default sampling; one provider family",
                 "Q1 2020 to Q2 2026", "Retrieval, agent and MCP", "Evaluation, threats and workbench",
                 "No forecasts or personal advice", "Not all rights have been verified."):
        assert text in visual
    for removed in ("Validated rows anchor calculations", "AI-drafted labels, one reviewer", "4 November 2026, Singapore morning.", "10 s per call"):
        assert removed not in visual
    assert "m.section('sources').metrics?.sources" in visual
    report = json.loads((STATIC / "data" / "report.json").read_text())
    assert report["sources"]["metrics"]["sources"] == 142
    story = (STATIC / "js" / "report-story.js").read_text()
    assert "['scope-contract', 'Assumptions and constraints']" in story
    assert "assumptionsScope(m)" in story
    css = (STATIC / "css" / "presentation.css").read_text()
    assert ".scope-contract" in css and ".scope-contract { grid-template-columns: 1fr;" in css


def _threat_pass_counts(arm_dir):
    path = next((WEB.parent / "experiments/threats" / arm_dir / "runs").glob("*verdicts.jsonl"))
    counts = {}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        counts[row["case_id"]] = counts.get(row["case_id"], 0) + (1 if row["passed"] else 0)
    return counts


def test_attack_gains_and_hover_examples_match_the_frozen_threat_runs():
    flows = (STATIC / "presentation/graphics-flows.js").read_text()
    analysis = json.loads((WEB.parent / "experiments/threats/threat-v2-analysis.json").read_text())
    categories = analysis["per_category"]
    guarded, naive = _threat_pass_counts("threat-v2-guarded-20261103"), _threat_pass_counts("threat-v2-naive-20261103")
    keys = {"Direct injection": "direct_injection", "Planted false figures": "planted_false_figures",
            "Causal and forecast overreach": "causal_forecast_overreach", "Citation and unsupported claims": "citation_unsupported_claims"}
    gains = re.findall(r"^  \['([^']+)', '[^']+', (\d+), (\d+), (\d+), '(T2-\d+)',.*, (\d), (\d), '[^']*'\],?$", flows, flags=re.M)
    assert len(gains) == 4
    for name, n, without, with_, case, ex_without, ex_with in gains:
        c = categories[keys[name]]
        assert (int(n), int(without), int(with_)) == (c["cases"], c["naive"], c["guarded"]), name
        assert (int(ex_without), int(ex_with)) == (naive[case], guarded[case]), case
    held = re.findall(r"^  \['([^']+)', (\d+), '(T2-\d+)',.*, (\d), (\d)\],?$", flows, flags=re.M)
    held_keys = {"Passage injection": "indirect_injection_passage", "Personal data": "sensitive_personal_data",
                 "Unsafe tool use": "unsafe_tool_use", "MCP-side attacks": "mcp_side_attacks"}
    assert len(held) == 4 and sum(int(n) for _, n, *_ in held) == 22
    for name, n, case, without, with_ in held:
        c = categories[held_keys[name]]
        assert int(n) == c["cases"] == c["naive"] == c["guarded"], name
        assert (int(without), int(with_)) == (naive[case], guarded[case]) == (3, 3), case
    for key in ("data_exfiltration", "cost_abuse"):
        assert (categories[key]["cases"], categories[key]["naive"], categories[key]["guarded"]) == (4, 3, 3)
    open_cases = re.findall(r"^  \['([^']+)', '(T2-\d+)', .*, (\d), (\d)\],?$", flows, flags=re.M)
    assert [c[1] for c in open_cases] == ["T2-024", "T2-053"]
    for _, case, without, with_ in open_cases:
        assert (int(without), int(with_)) == (naive[case], guarded[case]) and naive[case] < 2 and guarded[case] < 2
    assert (analysis["naive_majority_pass"], analysis["guarded_majority_pass"]) == (42, 50)
    assert "42 of 54" in flows and "50 of 54" in flows
    assert len(analysis["guarded_only_ids"]) - len(analysis["naive_only_ids"]) == sum(int(w) - int(wo) for _, _, wo, w, *_ in gains)


def test_next_steps_is_dom_text_without_the_removed_footer_caption():
    slides = (STATIC / "presentation/slides.js").read_text()
    main = _slides_main_section()
    slide = main.split("title: 'Next steps'", 1)[1].split("\n  });", 1)[0]
    assert "visual: nextSteps()" in slide and "Proposals only" not in slide
    assert "None of this is built" not in slide
    graphics = (STATIC / "presentation/graphics-flows.js").read_text()
    block = graphics.split("export function nextSteps()", 1)[1].split("return wrap;", 1)[0]
    assert "el('div', 'ns-col')" in block and "el('section', 'ns-col')" not in block
    data = graphics.split("const NEXT = [", 1)[1].split("\n];", 1)[0]
    for heading in ("Improve the system", "Deploy in production", "Keep the data current", "Extend"):
        assert heading in data
    css = (STATIC / "css/presentation.css").read_text()
    assert ".deck-page .slides section.present .ns * { user-select: text; -webkit-user-select: text; }" in css


def test_summary_is_a_results_board_read_from_report_data():
    slides = _slides_main_section().split("title: 'Summary'", 1)[1].split("source:", 1)[0]
    assert "summaryBoard(m)" in slides and "cardRow" not in slides
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = graphics.split("export function summaryBoard(m)", 1)[1]
    for read in ("finalFacts(m)", "finalCostFacts(m)", "m.methodsV31", "m.ladder", "m.section('mcp').metrics", "m.scope"):
        assert read in block
    for heading in ("What changed after the evaluation", "Limits", "Behaviour accuracy, gpt-6-luna", "Retrieval hit@8", "Threat suite"):
        assert heading in block
    for phrase in ("unevaluated", "native function-calling planner", "streaming", "Decisions API trials were rejected", "signed off by one reviewer", "Scanner can be bypassed", "source rights unverified"):
        assert phrase in block
    assert "held-out" not in block and "gpt-5.6-luna" not in block and "innerHTML" not in block
    for dash in ("\u2013", "\u2014"):
        assert dash not in block
    for tip in re.findall(r"withTip\(\w+, '([^']+)'", block):
        assert len(tip.split()) <= 27, tip


def test_summary_board_css_grows_bars_on_entry_only_and_collapses():
    css = (STATIC / "css" / "presentation.css").read_text(encoding="utf-8")
    board = css.split("/* Summary results board", 1)[1]
    assert "style=" not in board
    motion = board.split("@media (prefers-reduced-motion: no-preference)", 1)[1].split("}\n}", 1)[0]
    assert "section.present .sb-bar" in motion and "section.present .sb-seg" in motion
    assert "animation" not in board.split("@media (prefers-reduced-motion: no-preference)", 1)[0].split("@keyframes sb-grow", 1)[0]
    mobile = board.split("@media (max-width: 900px)", 1)[1]
    assert ".sb { grid-template-columns: minmax(0, 1fr)" in mobile
    for size in re.findall(r"font-size: (\d+)px", mobile):
        assert int(size) >= 16
