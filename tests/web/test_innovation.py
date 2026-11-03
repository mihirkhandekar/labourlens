"""Public innovation copy stays short, plain, truthful and CSP compatible."""
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from labourlens.report.app import Settings, create_app
from labourlens.report.innovation import CONTENT, project_innovation

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


def projection():
    return project_innovation(ROOT, json.loads((WEB / "static/data/report.json").read_text()))


def public_strings(value):
    """Count editorial text, not routing keys, statuses or internal table selectors."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in public_strings(item)]
    if isinstance(value, dict):
        return [text for key, item in value.items() if key not in ("id", "status", "tables") for text in public_strings(item)]
    return []


def test_projection_uses_explicit_editorial_source_and_aggregate_measurements():
    page = projection()
    assert page["content"] == json.loads((ROOT / CONTENT).read_text())
    assert page["source"]["sha256"] == hashlib.sha256((ROOT / CONTENT).read_bytes()).hexdigest()
    assert page["measurements"]["retrieval"] == {"n": 128, "R0": 0.5391, "R3": 0.9688}
    assert page["measurements"]["scanner"] == {"before": 10, "after": 23}
    assert [split["n"] for split in page["measurements"]["splits"]] == [237, 31, 65]


def test_plain_page_copy_has_no_internal_identifiers_or_unexplained_jargon():
    page_text = " ".join(public_strings(projection()["content"]))
    short = (ROOT / "docs/innovation.md").read_text()
    banned = r"\b(?:MCP|RBAC|SSO|WAF|SSE|API|CI|SLO|PDPA|BM25|DuckDB|McNemar|p50|p95|rerank(?:er|ing)?|embeddings?|triage|corpus|planner_v\d+|answer_v\d+|triage_v\d+|contextualise_v\d+|annual_average|D-\d+|gpt-[\w.-]+)\b|hit@8|\b[\w-]+\.(?:json|md|py|js)\b"
    for text in (page_text, short):
        assert not re.search(banned, text, re.I)
        assert not any(char in text for char in ("\u2014", "\u2013"))
        assert not re.search(r"\[(?:\d+|R\d+)\]|\[[^\]]+\]\(", text)


def test_word_budgets_are_about_sixty_percent_of_previous_copy():
    # Previous editorial JSON: 2,531 words; previous Markdown: 1,066 words.
    page_text = " ".join(public_strings(projection()["content"]))
    assert len(page_text.split()) <= 1520
    assert len((ROOT / "docs/innovation.md").read_text().split()) <= 660


def test_top_level_sections_and_merged_replacement_table():
    content = projection()["content"]
    titles = [section["title"] for section in content["sections"]]
    assert titles == ["How I would improve it", "Production deployment and security", "Making it ready for government use across departments"]
    headings = re.findall(r"^## (.+)$", (ROOT / "docs/innovation.md").read_text(), re.M)
    assert headings == ["Current approach", *titles, "Limitations"]
    production = content["sections"][1]
    assert production["subsections"][-1]["tables"] == ["components"]
    assert len(content["components"]) == 5
    assert all(item["replacement"].startswith("Proposed") for item in content["components"])
    script = (WEB / "static/js/innovation.js").read_text()
    assert "addSection('components'" not in script
    assert "addSection('limitations', 'Limitations')" in script


def test_proposals_are_visible_one_sentence_blocks_and_not_built():
    for section in projection()["content"]["sections"]:
        for item in section["proposals"]:
            assert item["status"] == "proposal"
            for key in ("measure", "gap", "threshold"):
                assert len(re.findall(r"[.!?](?:\s|$)", item[key])) == 1
    script = (WEB / "static/js/innovation.js").read_text()
    assert "el('details'" not in script and "el('summary'" not in script
    for text in ("el('h3'", "Change.", "Why.", "Check.", "Proposal, not built."):
        assert text in script


def test_key_improvements_and_honest_limits_are_preserved():
    content = projection()["content"]
    improve = content["sections"][0]
    assert len(improve["proposals"]) == 5
    assert [item["title"] for item in improve["proposals"]] == [
        "Shorter waits", "Retry the question-routing idea", "Broader, independent evaluation",
        "Useful calculations with clear limits", "Careful source updates",
    ]
    text = " ".join(public_strings(content))
    for term in ("14 seconds", "does not shorten", "Two earlier trials", "misdirected legitimate",
                 "untried", "2020 to 2023", "four complete quarterly rates", "not an official annual rate",
                 "independent analysts", "each protection separately", "refuse missing values"):
        assert term in text
    assert "did not demonstrate a reliable improvement" in text
    assert "Recent changes" in text and "have not been evaluated" in text


def test_production_governance_and_department_boundaries_remain_proposals():
    content = projection()["content"]
    production = " ".join(public_strings(content["sections"][1]))
    government = " ".join(public_strings(content["sections"][2]))
    for term in ("one server", "shared access codes", "replaceable workers", "secure credentials",
                 "provider data use", "independent security testing", "activity records",
                 "outside connections", "spending limits", "backups", "restoration"):
        assert term in production
    for term in ("Model AI Governance Framework", "human review", "risks and impacts",
                 "separate", "source-rights register", "department", "without promising dates",
                 "certification or compliance"):
        assert term in government
    assert "references" not in content
    assert "addSection('references'" not in (WEB / "static/js/innovation.js").read_text()


def test_projection_opens_only_curated_content_not_private_runs(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / CONTENT).write_bytes((ROOT / CONTENT).read_bytes())
    (tmp_path / "private").mkdir()
    (tmp_path / "private/answers.json").write_text('{"secret": "DO NOT PROJECT"}')
    page = project_innovation(tmp_path, {})
    assert page["content"] == json.loads((ROOT / CONTENT).read_text())
    assert "DO NOT PROJECT" not in json.dumps(page)
    assert page["measurements"]["splits"] == []


@pytest.mark.parametrize("bad", ["built", "measured", "complete"])
def test_roadmap_cannot_silently_promote_proposals(tmp_path, bad):
    (tmp_path / "docs").mkdir()
    content = json.loads((ROOT / CONTENT).read_text())
    content["sections"][0]["proposals"][0]["status"] = bad
    (tmp_path / CONTENT).write_text(json.dumps(content))
    with pytest.raises(ValueError, match="proposals"):
        project_innovation(tmp_path, {})


@pytest.mark.anyio
async def test_innovation_matches_public_deck_shell_and_keeps_api_gated(tmp_path):
    settings = Settings(access_codes=("x" * 24,), session_secret="test-only-session-signing-secret-32-bytes", feedback_dir=tmp_path)
    app = create_app(settings, runner=lambda q, s: {}, shared_factory=lambda: SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver") as client:
        page = await client.get("/innovation")
        deck = await client.get("/deck")
        assert page.status_code == deck.status_code == 200
        assert page.headers["content-security-policy"] == deck.headers["content-security-policy"]
        assert (await client.post("/api/ask", json={"question": "test"})).status_code == 401
        assert (await client.post("/api/login", json={"code": "x" * 24})).status_code == 200
        assert (await client.get("/innovation")).status_code == 200


def test_innovation_has_no_inline_code_or_external_assets():
    html = (WEB / "innovation.html").read_text()
    assert not re.search(r"<style\b|\sstyle\s*=|\son\w+\s*=", html, re.I)
    assert all("src=" in script for script in re.findall(r"<script\b[^>]*>", html))
    for asset in re.findall(r'(?:src|href)="([^"]+)"', html):
        assert not asset.startswith(("http:", "https:", "//"))
        if asset.startswith("/static/"):
            assert (WEB / asset.lstrip("/")).is_file()
    js = (WEB / "static/js/innovation.js").read_text()
    css = (WEB / "static/css/innovation.css").read_text()
    assert "innerHTML" not in js and "IntersectionObserver" in js
    assert "addEventListener('scroll'" not in js
    assert "@media print" in css and "@page" in css and "72ch" in css
    for token in ("box-shadow", "gradient(", "animation:", "transition:"):
        assert token not in css
    assert "/blob/master/" in js and "docs/innovation.md" in js
