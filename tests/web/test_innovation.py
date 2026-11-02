"""Innovation stays editable, aggregate-only, truthful and CSP compatible."""
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


def test_projection_uses_explicit_editorial_source_and_aggregate_primary_measurements():
    page = projection()
    assert page["content"] == json.loads((ROOT / CONTENT).read_text())
    assert page["source"]["sha256"] == hashlib.sha256((ROOT / CONTENT).read_bytes()).hexdigest()
    assert page["measurements"]["retrieval"] == {"n": 128, "R0": 0.5391, "R3": 0.9688}
    assert page["measurements"]["scanner"] == {"before": 10, "after": 23}
    assert [split["n"] for split in page["measurements"]["splits"]] == [237, 31, 65]
    text = json.dumps(page, ensure_ascii=False)
    for banned in ("gpt-5.6", "held-out", "\u2014", "\u2013", "evidence_text", "passage_text"):
        assert banned not in text
    assert all(item["status"] == "proposal" for group in page["content"]["roadmap"] for item in group["items"])


def test_six_assessment_questions_match_the_short_deliverable():
    groups = projection()["content"]["roadmap"]
    headings = re.findall(r"^## (.+)$", (ROOT / "docs/innovation.md").read_text(), re.M)
    assert len(groups) == len(headings) == 6
    assert [group["name"] for group in groups] == headings
    priorities = groups[-1]["items"]
    assert len(priorities) == 2
    assert all(term in priorities[0]["why"] for term in ("0.50", "false-answer", "blind"))
    assert all(term in priorities[1]["why"] for term in ("kappa", "0.70", "0.10", "blind"))


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
    content["roadmap"][0]["items"][0]["status"] = bad
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
    assert "innerHTML" not in js and "IntersectionObserver" in js
    assert "addEventListener('scroll'" not in js
    for path in (WEB / "innovation.html", WEB / "static/js/innovation.js", WEB / "static/css/innovation.css"):
        assert not any(char in path.read_text() for char in ("\u2014", "\u2013"))
