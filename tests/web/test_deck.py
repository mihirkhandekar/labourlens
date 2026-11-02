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
    assert 28 <= len(specs) <= 32, len(specs)
    total = len(re.findall(r"\badd\(\{", (STATIC / "presentation" / "slides.js").read_text()))
    assert total - len(specs) >= 10  # appendix slides
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
        assert not re.search(r"ADR-|D-0\d\d|T-I06|\.md\b", text), path.name


def test_no_bridge_sentences_or_pills_on_faces():
    main = _slides_main_section()
    for banned in ("withSoWhat", "The next slide", "pill", "eyebrow"):
        assert banned not in main


REQUIRED_TITLES = [
    "The assignment", "My project", "The Agentic System", "Success criteria and failure modes",
    "Choosing the data", "What the data showed", "Retrenchments rose but the data does not say why", "Advance and final figures differ", "Challenges with the data",
    "Reading the reports", "One current document build", "Retrieval Strategies", "Does filtering help?",
    "The agent loop", "Choosing the models", "The MCP server", "GenAI concepts in this build",
    "Ensuring Reliable Sources", "Agent Workbench",
    "How I measured", "Human Review of Dataset", "The experiment ladder", "Why it missed", "Fixing the calculation gap", "Attacks and defences", "A planted wrong figure",
    "How I built it", "Limits and next steps", "Summary",
]


def _flow_rows():
    text = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    block = text.split("const FLOW = [", 1)[1].split("\n  ];", 1)[0]
    return re.findall(r"\['([^']+)', (null|'all'|\d), '([^']+)'\]", block)


def test_main_deck_follows_the_navigation_flow_and_has_short_plain_titles():
    main = _slides_main_section()
    defined = set(re.findall(r"\btitle: '([^']+)'", main))
    rows = _flow_rows()
    assert len(rows) == 30
    assert [r[0] for r in rows[1:]] == REQUIRED_TITLES
    for title, _, _ in rows:
        assert title in defined or "Singapore AI Agent" in title, title
    # Each slide's stage sits in the top navigation order: Sources, Processing, Retrieval, Agent, Answer, Checks.
    stages = [int(s) for _, s, _ in rows if s.isdigit()]
    assert stages == sorted(stages) and set(stages) == {0, 1, 2, 3, 4, 5}
    names = ["Sources", "Processing", "Retrieval", "Agent", "Answer", "Checks"]
    for title, stage, chapter in rows:
        if stage.isdigit():
            assert chapter == names[int(stage)], title
    assert "['Sources', 'Processing', 'Retrieval', 'Agent', 'Answer', 'Checks']" in (STATIC / "presentation" / "deck.js").read_text()
    for title in [r[0] for r in rows][1:]:
        assert len(title.split()) <= 9, title
    assert 28 <= len(re.findall(r"\badd\(\{", main)) <= 32


def test_calculation_fix_slide_states_the_failure_and_the_graphics_exist():
    main = _slides_main_section()
    assert main.count("Fixing the calculation gap") == 1
    assert "failed rules I set before the run" in main and "optimistic" in main and "not adopted" in main.lower()
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
    for needle in ("k1=1.5, b=0.75", "text-embedding-3-large", "reciprocal rank fusion, c=60", "ranks top 30 candidates, returns up to 10"):
        assert needle in main or needle in graphics, needle
    assert "not the 70.8% on the previous slide" in main and "24 cases" in main and "128" in main


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
    assert "no false answers at the lowest cost" in main and "not a ranking" in main and "fresh questions" in main
    assert "I would choose gpt-5.6-luna" in main


def test_mcp_slide_states_where_mcp_sits():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    block = graphics.split("export function mcpMap", 1)[1].split("return wrap;", 1)[0]
    for needle in ("Direct calls", "Through MCP", "get_statistic", "labourlens://sources", "compare_quarters", "17 parts", "10 hostile-server cases", "One agent question over MCP", "${lat.direct} ms and ${lat.mcp} ms", "No measured gain"):
        assert needle in block, needle
    main = _slides_main_section()
    assert "The live app reaches statistics through MCP. Every accuracy evaluation called the same functions directly" in main
    assert "Through MCP, the live web app" in block and "Direct calls, the accuracy evaluations" in block


def test_threat_slide_reads_counts_from_the_report_data_and_labels_runs():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    block = graphics.split("export function threatMatrix", 1)[1].split("return wrap;", 1)[0]
    assert "threatRuns(m)" in block and "(final run)" in block and "(earlier run)" in block
    assert "With defences" in block and "Without defences" in block
    assert "e2efixRow" in graphics and "securityRow" in graphics
    main = _slides_main_section()
    assert "threatRuns(m)" in main and "no defence effect for the stronger models" in main


def test_workbench_slide_names_the_live_only_steps():
    main = _slides_main_section()
    assert "a small-talk reply, a scope check and a rewrite of follow-up questions" in main and "The experiments did not use them" in main


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
        imported = set(re.findall(r"[\w$]+", re.search(r"import \{([^}]*)\} from '[./]*(?:presentation/)?graphics\.js'", text).group(1)))
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
    assert "final evaluation ran on this build" in rerun and "one run per arm" in rerun
    dev = next(s for s in final["splits"] if s["id"] == "dev")
    r3 = next(a for a in dev["arms"] if a["arm"] == "r3" and a["model"] == "gpt-6-luna")
    assert f"{r3['metrics']['behaviour_accuracy']['rate'] * 100:.1f}%" in rerun
    graphics = (STATIC / "presentation" / "graphics.js").read_text(encoding="utf-8")
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    assert "finalComparison(m)" in slides and "provenanceTable(m)" in slides
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
            assert entry["candidate_correct"] is not None and entry["baseline_correct"] is not None
    assert all(row["runs_per_arm"] == 1 and row["corpus"] == "v3.1" for row in final["provenance_table"])


def test_mcp_wording_is_exact():
    mcp = (STATIC / "presentation" / "ch7-mcp.js").read_text(encoding="utf-8")
    assert "another protocol version" not in mcp and "unexpected version string" in mcp and "client default is 8 s" in mcp
    slides = (STATIC / "presentation" / "slides.js").read_text(encoding="utf-8")
    assert "advertised input schemas" in slides and "fixed in code" in slides and "2025-11-25" in slides
