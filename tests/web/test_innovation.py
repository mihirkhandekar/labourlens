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
    assert all(item["status"] == "proposal" for section in page["content"]["sections"] for item in section["proposals"])


def test_six_assessment_questions_match_the_short_deliverable():
    groups = projection()["content"]["sections"]
    headings = re.findall(r"^## (.+)$", (ROOT / "docs/innovation.md").read_text(), re.M)
    assert len(groups) == 6
    assert [group["title"] for group in groups] == headings[1:7]
    improvements = groups[4]["proposals"]
    arithmetic = next(item for item in improvements if item["title"] == "First: report-table arithmetic")
    review = next(item for item in improvements if item["title"] == "Second: independent review")
    assert "0.50" in arithmetic["threshold"] and "false-answer" in arithmetic["threshold"]
    assert "blind" in arithmetic["measure"]
    assert all(term in review["threshold"] for term in ("kappa", "0.70", "0.10"))
    assert "blind" in review["measure"]
    assert len(headings) == 9 and headings[0] == "Current approach"


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
    assert "innerHTML" not in js and "IntersectionObserver" in js
    assert "addEventListener('scroll'" not in js
    for path in (WEB / "innovation.html", WEB / "static/js/innovation.js", WEB / "static/css/innovation.css"):
        assert not any(char in path.read_text() for char in ("\u2014", "\u2013"))


def test_document_layout_keeps_tables_references_feedback_and_print_without_decoration():
    content = projection()["content"]
    for reference in content["references"]:
        assert (ROOT / reference["path"]).is_file()
    feedback = content["sections"][2]["proposals"][1]
    assert feedback["title"] == "Feedback review loop"
    assert all(term in feedback["measure"] for term in ("thumbs-down", "expected evidence", "one thing", "pseudonymise".capitalize()))
    js = (WEB / "static/js/innovation.js").read_text()
    css = (WEB / "static/css/innovation.css").read_text()
    for token in ("el('table'", "el('caption'", "el('dl'"):
        assert token in js
    for token in ("box-shadow", "gradient(", "iv-enter", "animation:", "transition:"):
        assert token not in css
    assert "@media print" in css and "@page" in css
    assert "max-width" in css and "72ch" in css


def test_every_github_link_on_the_innovation_page_points_to_a_tracked_file():
    import subprocess
    script = (WEB / "static/js/innovation.js").read_text()
    bases = re.findall(r"https://github\.com/[\w.-]+/[\w.-]+/blob/([\w.-]+)/", script)
    assert bases == ["master"], "The default branch is master; a blob/main link returns 404"
    assert "/blob/master/" in (WEB / "static/js/report-story.js").read_text()
    try:
        tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines())
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    content = json.loads((ROOT / CONTENT).read_text())
    assert content["references"] == []
    assert all(not paragraph["refs"] for group in content["sections"] for paragraph in group["paragraphs"])
    assert "docs/innovation.md" in tracked


def test_production_design_is_complete_but_remains_a_proposal():
    content = json.loads((ROOT / CONTENT).read_text())
    production = content["sections"][5]["proposals"][0]
    assert production["status"] == "proposal"
    assert "not deployed" in production["title"]
    short = (ROOT / "docs/innovation.md").read_text()
    for text in (production["measure"], short):
        for component in (
            "edge/WAF", "SSO", "load balancer", "stateless API", "queue", "SSE",
            "object storage", "DuckDB", "MCP", "secrets manager", "LLM gateway",
            "observability", "CI", "rollback", "backups", "restore",
        ):
            assert component.lower() in text.lower()
    script = (WEB / "static/js/innovation.js").read_text()
    assert "Production design only." in script
    assert "proposed production architecture" in script


def test_latency_plan_separates_smoke_streaming_and_adoption_evidence():
    content = json.loads((ROOT / CONTENT).read_text())
    cost = content["sections"][4]
    paragraphs = " ".join(item["text"] for item in cost["paragraphs"])
    short = (ROOT / "docs/innovation.md").read_text()
    for text in (paragraphs, short):
        for value in ("14", "29.8", "7.8", "9.1", "53.1", "8.6", "12.8"):
            assert value in text
        assert "accuracy unmeasured" in text
        assert "Streaming" in text
        assert "full-answer time" in text
    latency = next(item for item in cost["proposals"] if item["title"] == "Reduce waiting without lowering answer quality")
    assert latency["status"] == "proposal"
    for text in (latency["measure"], short):
        for term in ("237", "triage", "embeddings", "series lookups", "prompt",
                     "response", "without history", "smaller", "three calls per round",
                     "permissions", "corpus", "model"):
            assert term in text
    for term in ("p50", "p95", "accuracy", "safety", "cost", "fresh blind"):
        assert term in latency["threshold"]


def test_third_decisions_registration_cannot_erase_two_failed_trials():
    content = json.loads((ROOT / CONTENT).read_text())
    cost = content["sections"][4]
    outcomes = " ".join(item["text"] for item in cost["paragraphs"])
    short = (ROOT / "docs/innovation.md").read_text()
    for text in (outcomes, short):
        for value in ("397/409", "19/30", "44/58", "414/450", "0.362", "0.426", "1.392", "1.847"):
            assert value in text
        assert "neither decisions api trial was adopted" in text.lower()
    registered = next(item for item in cost["proposals"] if item["title"].startswith("Third Decisions attempt:"))
    assert registered["status"] == "proposal"
    assert "preregistered two-way" in registered["title"]
    for term in ("untested", "no paid execution authorised", "0.70", "150 fresh",
                 "90 in-scope", "30 out-of-scope", "15 harm", "15 small-talk",
                 "three", "interleaved", "fallback", "Do not tune"):
        assert term in registered["measure"]
    for term in ("zero legitimate", "148/150", "29/30", "1%", "450",
                 "80%", "p50", "p95", "downstream safety", "owner approval"):
        assert term in registered["threshold"]
    assert "Registered plan, untested" in (WEB / "static/js/innovation.js").read_text()


def test_short_assessment_keeps_two_page_editorial_budget_and_served_disclosures():
    short = (ROOT / "docs/innovation.md").read_text()
    assert len(short.split()) <= 1400
    for term in ("annual_average", "non-null", "never a partial", "ten tools",
                 "planner_v6", "answer_v8", "triage_v4", "contextualise_v3",
                 "untrusted data", "missing observations", "missing method/commentary",
                 "unevaluated"):
        assert term in short
    assert not any(char in short for char in ("\u2014", "\u2013"))


def test_government_readiness_and_improvement_plans_are_separate_and_proposed():
    content = json.loads((ROOT / CONTENT).read_text())
    improve, government = content["sections"][4:]
    assert improve["title"] == "How I would improve it"
    assert government["title"] == "Making it ready for government use across departments"
    for item in improve["proposals"] + government["proposals"]:
        assert item["status"] == "proposal"
        assert all(item[key] for key in ("title", "gap", "measure", "threshold"))
    improvement_text = json.dumps(improve)
    for term in ("annual_average", "2020 to 2023", "ablation", "blind", "237"):
        assert term in improvement_text
    government_text = json.dumps(government)
    for term in ("RBAC", "PDPA", "residency", "tamper-evident", "egress",
                 "supply-chain", "penetration", "Model AI Governance Framework",
                 "human-in-the-loop", "change control", "drift", "tenants",
                 "licence register", "SLO", "on-call", "cost caps", "failover",
                 "pilot", "hardened beta", "department"):
        assert term in government_text


def test_innovation_omits_inline_reference_markers_and_reference_block():
    short = (ROOT / "docs/innovation.md").read_text()
    script = (WEB / "static/js/innovation.js").read_text()
    assert not re.search(r"\[[^\]]+\]\(", short)
    assert "## References" not in short
    assert "addSection('references'" not in script
    assert "el('sup'" not in script
    assert "ref.number" not in script
