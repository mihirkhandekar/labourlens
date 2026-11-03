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
    assert total == 43  # 28 main slides, appendix index, and references A to N
    assert total - len(specs) == 15
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
        assert not re.search(r"ADR-|D-0\d\d|T-I06|\.md\b", text), path.name


def test_no_bridge_sentences_or_pills_on_faces():
    main = _slides_main_section()
    for banned in ("withSoWhat", "The next slide", "pill", "eyebrow"):
        assert banned not in main


REQUIRED_TITLES = [
    "Assignment", "My project", "Agentic system", "Choosing the data", "Data findings", "Retrenchments rose, data gives no cause", "Advance and final figures differ", "Two kinds of evidence", "Challenges with the data", "Success criteria and failure modes",
    "Reading reports", "Retrieval Strategies", "Does filtering help?", "Agent loop", "Choosing models", "MCP server", "GenAI concepts in this build", "Ensuring Reliable Sources", "Agent Workbench", "How the question sets work",
    "How I measured", "Human Review of Dataset", "Does retrieval improve answers?", "The calculation gap", "Attacks and defences", "How I built it", "Summary",
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
    reading = main.split("title: 'Reading reports'", 1)[1].split("\n  });", 1)[0]
    for fact in ("85 sources", "16,419", "1,847", "v3.1 relabelled 40"):
        assert fact in reading


def test_calculation_fix_slide_states_the_failure_and_the_graphics_exist():
    main = _slides_main_section()
    assert main.count("title: 'The calculation gap'") == 1
    calculation = main.split("title: 'The calculation gap'", 1)[1].split("\n  });", 1)[0]
    assert "Two criteria failed" in calculation and "optimistic diagnostic" in calculation and "not adopted" in calculation
    assert "calculate_from_text_values" in main and ("do not establish why" in main or "does not establish why" in main)
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    for name in ("threeAnswers", "twoSources", "buildTimeline", "flattening", "retrievalStaircase", "agentLoop", "evidenceTrace", "experimentStaircase", "costBars", "toolFixBars", "toolFixFlow", "assignmentBrief", "challengeGrid", "modelChoice", "architectureDiagram", "myProject", "hardParts", "failureModes", "keywordVsMeaning", "reviewStreams", "threatMatrix", "threatRuns", "mcpMap", "workbenchShot", "conceptGrid", "measureCards", "plantedFlow", "buildProcess", "excerptTable", "rowsAffordance", "withTip"):
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
    luna, luna56 = rows["gpt-6-luna"], rows["gpt-5.6-luna"]
    assert (luna["false_answer_rate"], luna["cost_per_case_usd"], luna["over_abstention_rate"]) == (0.0, 0.00051, 0.417)
    assert luna56["behavior_accuracy"] > luna["behavior_accuracy"] and luna56["false_answer_rate"] == 0.0
    main = _slides_main_section()
    assert "Early screen on 30 questions" in block and "Final system on 237 questions" in block
    assert "95% Wilson interval" in block and "wilson(right, n)" in block and "runs.run1" in block and "runs.run2" in block
    models_slide = main.split("title: 'Choosing models'", 1)[1].split("\n  });", 1)[0]
    assert "gpt-5.6" not in models_slide and "89.7%" in models_slide and "no false answers at the lowest cost" in models_slide
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
    for needle in ("LabourLens host", "MCP client", "MCP server", "get_statistic", "labourlens://sources", "compare_quarters", "outputSchema", "stdio", "Nine read-only tools", "2 resources"):
        assert needle in block, needle
    assert "not in the base planner schema" in block and "Full-set accuracy evaluations used direct calls" in block
    loop = graphics.split("export function agentLoop", 1)[1].split("return wrap;", 1)[0]
    for needle in ("Search reports", "BM25 + embeddings", "Structured statistics", "Calculate in code", "Stop gathering", "Review returned evidence", "2 rounds", "6 calls", "10 s per call"):
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
    block = graphics.split("export function threatMatrix", 1)[1].split("return wrap;", 1)[0]
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


def test_workbench_slide_names_the_live_only_steps():
    main = _slides_main_section()
    assert "small-talk replies, a scope check and follow-up rewrites" in main and "65-case sample measures the served chain" in main


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
    assert metrics["observations"] == 52020 and metrics["in_scope_observations"] == 4300, metrics
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
    ladder = main.split("title: 'Does retrieval improve answers?'", 1)[1].split("\n  });", 1)[0]
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
    assert "Report search and calculation stay in the app" in block
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
    for label in ("2 rounds", "6 calls", "10 s per call", "Bounded retries"):
        assert label in loop, label
    legend = _graphics_block(graphics, "export function toolLegend()", "export function buildTimeline(m)")
    assert "MCP server (blue outline)" in legend and "Calls server tool get_statistic" in legend
    assert re.search(r"\.owner-agent \.owner-agent-node\.is-mcp rect\s*\{[^}]*stroke:\s*var\(--c3\)", css)


def test_retained_calculation_experiment_explains_its_rejection_once():
    main = _slides_main_section()
    assert [row[0] for row in _flow_rows()][24] == "The calculation gap"
    slide = main.split("title: 'The calculation gap'", 1)[1].split("\n  });", 1)[0]
    assert "visual: toolFixFlow(m)" in slide and "toolFixBars(m)" not in slide
    assert "kept it out of the live system" in slide
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    block = _graphics_block(graphics, "export function toolFixFlow(m)", "return wrap;")
    for label in ("Dataset-row calculation tool", "Report-text calculation tool", "3 of 14", "Two rules failed", "Not adopted."):
        assert label in block, label
    assert "first.x2.correct / first.x2.n" in block and "first.x3.correct / first.x3.n" in block
    assert "false answers rose from 6 to 7" in block and "one new-tool case" in block
    assert "Same 65 questions" not in block and "For both models" not in block
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
    assert len(re.findall(r"\badd\(\{", slides)) == 43
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
    assert "visual: threatMatrix(m)" in slides
    assert "Attack type" in graphics and "Defence layer(s)" in graphics
    block = graphics.split("export function threatMatrix", 1)[1].split("return wrap;", 1)[0]
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
    assert "measurementProcess()" in main
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
    assert "Trying the Decisions API" not in _slides_main_section()
    assert slides.count("title: 'Trying the Decisions API'") == 1
    appendix = slides.split("// ---------- appendix", 1)[1].split("// Appendix index lists", 1)[0]
    assert len(re.findall(r"\badd\(\{", appendix)) == 15
    last_slide = appendix.rsplit("add({", 1)[1]
    assert "id: 'decisions-api'" in last_slide
    assert "title: 'Trying the Decisions API'" in last_slide
    assert "visual: decisionsExperiment()" in last_slide
    assert "both preregistered screens failed. Not adopted." in last_slide
    assert "experiments/eval/decisions-api-results.json" in last_slide
    notes = last_slide.split("notes:", 1)[1]
    for caveat in ("historical, not contemporaneous", "no generated reply", "441 selected dependent claims",
                   "both generator models", "second-family AI judge", "not human ground truth",
                   "Same-family original-judge", "no verified unsupported negatives",
                   "No judge-latency comparison", "end-to-end swap", "no live adoption",
                   "original test and fresh questions"):
        assert caveat in notes, caveat
    assert "held-out" not in last_slide and "heldout" not in last_slide
    block = graphics.split("export function decisionsExperiment()", 1)[1].split("return wrap;", 1)[0]
    for label in ("Routing latency", "Exact route accuracy", "AUROC", "Accuracy", "Balanced accuracy",
                  "both generator models", "API model: gpt-6-luna only", "False support: 44/58"):
        assert label in block
    for identifier in ("DEV-", "HO-", "D-0", "A0", "A70"):
        assert identifier not in block
    assert "gpt-5.6-luna" not in block
    latency = results["triage"]["latency"]
    assert f"['Historical', {latency['baseline']['p50_s']}," in block
    assert f"['Decisions', {latency['case_medians']['p50_s']}," in block
    assert "const routeThreshold = 407 / 409;" in block
    assert results["triage"]["rules"]["thresholds"]["exact_matches_each_repeat"] == 407
    for arm, label in (("A0", "No confidence gate"), ("A70", "70% confidence gate")):
        counts = {v["effective_exact_route"]["numerator"] for v in results["triage"]["arms"][arm]["by_repeat"].values()}
        assert len(counts) == 1
        assert f"['{label}', {counts.pop()}]" in block
    # The historical count is derived from the stored paired deltas, not a new run.
    baseline = 405 - round(sum(v["A0"] for v in latency["paired_cases"]))
    assert f"['Baseline', {baseline}]" in block
    primary = results["support"]["metrics"]["primary"]["overall"]
    for label, key, threshold in (("AUROC", "auroc", ".80"), ("Accuracy", "all_scheduled_accuracy", ".85"),
                                  ("Balanced accuracy", "balanced_accuracy", ".70")):
        assert f"['{label}', {primary[key]}, {threshold}]" in block
    assert primary["scheduled_n"] == 441
    assert set(results["support"]["metrics"]["primary"]["strata"]["model"]) == {"gpt-6-luna", "gpt-5.6-luna"}
    assert results["triage"]["decision"] == results["support"]["decision"] == "failed_screen"
    css = (STATIC / "css/presentation.css").read_text()
    assert "const latencyRows =" in block and "const routeRows =" in block
    assert "latencyRows.forEach" in block and "routeRows.forEach" in block
    assert "supportMetrics.forEach" in block and "wrap.append(mobile)" in block
    assert ".decisions-experiment > svg { display: none; }" in css
    assert ".decisions-experiment .decisions-mobile { display: grid;" in css
    assert ".decisions-mobile-note, .decisions-mobile-threshold, .decisions-mobile-failed { font-size: 16px;" in css
