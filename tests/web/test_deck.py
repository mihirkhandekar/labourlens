"""The presentation deck: route, CSP, vendored files, and source hygiene for the slides.

Slides are built in the browser from report.json, so the checks that need a rendered DOM (slide count,
headings, speaker notes) read the slide declarations and the builder; the headless Chrome run in the
hand-off covers the rendered deck.
"""
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
    "About me", "The assignment", "Why this problem", "The task, and what I left out", "The Agentic System", "Choosing the data", "One current document build", "Reading the reports",
    "What the data showed", "Hard parts, and what handles them", "Keyword, meaning or both?", "Does filtering help?", "The agent loop", "Every claim has a source",
    "Choosing the models", "How I measured", "Who checked the answers", "The experiment ladder", "On fresh questions, the gain was small", "Why it missed", "Fixing the calculation gap",
    "GenAI concepts in this build", "The MCP server", "Attacks and defences", "A planted wrong figure", "The product, and how to run it", "How I built it", "Limits, and what next", "Summary",
]


def test_main_deck_follows_the_assignment_and_has_short_plain_titles():
    main = _slides_main_section()
    titles = []
    for title in re.findall(r"\btitle: '([^']+)'", main):
        if title not in titles:
            titles.append(title)
    position = -1
    for wanted in REQUIRED_TITLES:
        assert wanted in titles, wanted
        assert titles.index(wanted) > position, f"{wanted} is out of order"
        position = titles.index(wanted)
    for title in titles[1:]:
        assert len(title.split()) <= 9, title
    assert 28 <= len(re.findall(r"\badd\(\{", main)) <= 32


def test_calculation_fix_slide_states_the_failure_and_the_graphics_exist():
    main = _slides_main_section()
    assert main.count("Fixing the calculation gap") == 1
    assert "pre-declared criteria" in main and "optimistic" in main and "not adopted" in main.lower()
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    for name in ("threeAnswers", "twoSources", "buildTimeline", "flattening", "retrievalStaircase", "agentLoop", "evidenceTrace", "experimentStaircase", "costBars", "toolFixBars", "toolFixFlow", "assignmentBrief", "domainChoice", "challengeGrid", "earlyModelChart", "aboutMe", "architectureDiagram", "taskAndLeftOut", "hardParts", "keywordVsMeaning", "reviewStreams", "threatMatrix", "workbenchShot", "conceptGrid", "measureCards", "plantedFlow", "buildProcess"):
        assert f"export function {name}" in graphics, name
    slides = (STATIC / "presentation" / "slides.js").read_text()
    assert "403" in main and "Human reviewed" in main
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
    assert "Human reviewed" in slides and "same model family" in slides
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


def test_method_panels_and_retrieval_baseline_note():
    main = _slides_main_section()
    deck = (STATIC / "presentation" / "deck.js").read_text()
    assert "deck-method" in deck and "spec.detail.open" in deck
    for needle in ("k1=1.5, b=0.75", "text-embedding-3-large", "reciprocal rank fusion, c=60", "ranks top 30 candidates, returns up to 10"):
        assert needle in main, needle
    assert "not the 70.8% on the previous slide" in main and "24 cases" in main and "128" in main


def test_title_slide_has_no_graphic_and_structure_labels_are_plain():
    graphics = (STATIC / "presentation" / "graphics.js").read_text()
    assert "titleVisual" not in graphics
    assert "Structured: statistics" in graphics and "Unstructured: reports" in graphics
    assert "Same 65 questions, reused" in graphics and "not adopted" in graphics


def test_workbench_qr_has_a_quiet_zone():
    svg = (STATIC / "presentation" / "workbench-qr.svg").read_text()
    xs = [int(x) for x in re.findall(r'x="(\d+)mm" y="\d+mm" width="1mm"', svg)]
    ys = [int(y) for y in re.findall(r'x="\d+mm" y="(\d+)mm" width="1mm"', svg)]
    size = int(re.search(r'width="(\d+)mm"', svg).group(1))
    assert min(xs) >= 4 and min(ys) >= 4 and size - 1 - max(xs) >= 4 and size - 1 - max(ys) >= 4
