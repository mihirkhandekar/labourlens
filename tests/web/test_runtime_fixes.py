"""Regression tests for the end-to-end review fixes (docs/experiments/m7-e2e-fixes.md): web projection, rights window,
feedback binding, corpus fingerprint, audit retention, deploy list. Offline: no corpus, network or API key unless marked."""
import asyncio
import json
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from labourlens import paths
from labourlens.answer import validate
from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer
from labourlens.audit import log as audit_log
from labourlens.report.app import RIGHTS_NOTICE, create_app, public_result
from labourlens.retrieval import runtime
from test_app import ACCESS_CODE, QUESTION, agent_result, client_for, isolated_environment, login, settings  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
NO_SHARED = SimpleNamespace(obs=pd.DataFrame(), passages_by_id={})


def _raw(evidence, claims, **answer):
    raw = agent_result()
    raw["evidence_text"] = {"P1": evidence}
    raw["evidence"] = [{"label": "P1", "id": "p1", "source_id": "fixture"}]
    raw["answer"]["claims"] = claims
    raw["answer"].update(answer)
    return raw


# ---- 1. web projection matches the validator ---------------------------------------------------------------------

def test_quote_spanning_a_pdf_line_break_is_accepted_by_the_validator_and_kept_by_the_web_layer():
    text = "Retrenchments eased in the quarter,\nwhile job vacancies stayed\nelevated across sectors."
    quote = "eased in the quarter, while job vacancies"
    assert validate.quote_in(quote, text)
    ctx = [ContextPassage("P1", "p1", "fixture", "Fixture", None, "final", "p.1", text, ())]
    answer = Answer.model_validate(dict(status="answered", summary="s", caveats=[], clarification_question="", reason="",
                                        claims=[dict(text="c", citations=[dict(label="P1", quote=quote)])]))
    assert validate.check(answer, ctx).valid
    result = public_result(_raw(text, [{"text": "c", "citations": [{"label": "P1", "quote": quote}]}]), NO_SHARED)
    assert result["answer"]["claims"][0]["citations"] == [{"label": "P1", "quote": quote}]
    assert result["evidence"][0]["quotes"] == [quote]


def test_a_quote_reused_by_several_claims_keeps_its_citation_in_every_claim():
    text = "Resident unemployment stayed low in the quarter under review."
    quote = "unemployment stayed low"
    claims = [{"text": f"claim {i}", "citations": [{"label": "P1", "quote": quote}, {"label": "P1", "quote": quote.upper()}]} for i in range(3)]
    result = public_result(_raw(text, claims), NO_SHARED)
    assert [len(c["citations"]) for c in result["answer"]["claims"]] == [1, 1, 1]  # once per claim, in every claim
    assert result["evidence"][0]["quotes"] == [quote]


def test_a_quote_that_is_not_in_the_evidence_is_still_dropped():
    result = public_result(_raw("Alpha beta gamma.", [{"text": "c", "citations": [{"label": "P1", "quote": "delta epsilon"}]}]), NO_SHARED)
    assert result["answer"]["claims"][0]["citations"] == []


# ---- 2. ungrounded numbers ---------------------------------------------------------------------------------------

def _ctx(text):
    return [ContextPassage("P1", "p1", "fixture", "Fixture", None, "final", "p.1", text, ())]


def test_fabricated_numbers_in_summary_and_caveats_are_flagged_but_status_semantics_are_unchanged():
    answer = Answer.model_validate(dict(status="answered", summary="Retrenchments rose to 9,999.", clarification_question="", reason="",
                                        caveats=["About 12.5% of firms were affected."],
                                        claims=[dict(text="Retrenchments were 3,830 persons in 2026.", citations=[dict(label="P1", quote="3,830 persons")])]))
    report = validate.check(answer, _ctx("Retrenchments totalled 3,830 persons in 2026."))
    assert report.valid  # unchanged: soft finding, not an error
    assert report.ungrounded_numbers == ["summary: 9999", "caveat 1: 12.5"]


def test_grounded_summary_numbers_are_not_flagged():
    answer = Answer.model_validate(dict(status="answered", summary="Retrenchments were 3,830 persons in 2026.", clarification_question="",
                                        reason="", caveats=[],
                                        claims=[dict(text="x", citations=[dict(label="P1", quote="3,830 persons")])]))
    assert validate.check(answer, _ctx("Retrenchments totalled 3,830 persons.")).ungrounded_numbers == []


def test_browser_projection_shows_a_number_not_found_notice():
    raw = agent_result()
    raw["trace"] = [{"node": "validate_answer", "event": "valid", "detail": {"ungrounded_numbers": ["claim 1: 9999", "claim 2: 2", "summary: 12.5"]}}]
    result = public_result(raw, NO_SHARED)
    assert result["answer"]["ungrounded_numbers"] == ["claim 1: 9999", "summary: 12.5"]
    assert any(c.startswith("Number not found in evidence: claim 1 (9999), summary (12.5)") for c in result["answer"]["caveats"])
    assert result["answer"]["status"] == "answered"  # shown, not rejected
    assert public_result(agent_result(), NO_SHARED)["answer"]["ungrounded_numbers"] == []


# ---- rights window: obfuscation ----------------------------------------------------------------------------------

EVIDENCE = ("the seasonally adjusted overall unemployment rate edged lower while the number of retrenched workers stayed "
            "broadly stable across every major sector of the economy")


@pytest.mark.parametrize("copy", [
    EVIDENCE.replace(" ", "  ").upper(),                                                  # case and spacing
    EVIDENCE.replace(" ", ", ", 6),                                                       # punctuation between words
    EVIDENCE.replace("unemployment", "un-employment").replace("retrenched", "re-trenched").replace("sector", "sec\u200btor"),  # hyphen / zero width
    EVIDENCE.replace("stayed broadly", "stayed\u00a0broadly").replace("the economy", "the\neconomy"),
])
def test_obfuscated_copy_of_evidence_is_withheld(copy):
    result = public_result(_raw(EVIDENCE, [], summary=copy), NO_SHARED)
    assert result["answer"]["summary"] == RIGHTS_NOTICE


def test_short_independent_paraphrase_is_not_withheld():
    summary = "Unemployment edged down and retrenchments were stable, according to the cited report."
    assert public_result(_raw(EVIDENCE, [], summary=summary), NO_SHARED)["answer"]["summary"] == summary


def _annual_raw(evidence, claims=None, **answer):
    raw = _raw(evidence, claims or [], **answer)
    raw["tool_set"] = "annual"
    return raw


@pytest.mark.parametrize("field", ["summary", "reason", "clarification_question", "caveats", "claim"])
def test_served_annual_removes_only_copied_report_spans_including_limits(field):
    source = "business reorganisation affected several outward oriented sectors"
    text = f'Independent context. "{source}". Causation remains unproven.'
    raw = _annual_raw(source)
    if field == "caveats":
        raw["answer"]["caveats"] = [text]
    elif field == "claim":
        raw["answer"]["claims"] = [{"text": text, "citations": []}]
    else:
        raw["answer"][field] = text
    answer = public_result(raw, NO_SHARED)["answer"]
    projected = (answer["caveats"][0] if field == "caveats" else
                 answer["claims"][0]["text"] if field == "claim" else answer[field])
    assert projected == f'Independent context. "{RIGHTS_NOTICE}". Causation remains unproven.'
    assert raw["evidence_text"]["P1"] == source


def test_served_annual_keeps_paraphrase_and_six_word_common_phrase():
    source = "business reorganisation affected several outward oriented sectors"
    paraphrase = "Corporate restructuring was reported; neither AI nor COVID is established as the cause."
    six_words = "business reorganisation affected several outward oriented"
    raw = _annual_raw(source, summary=paraphrase, caveats=[six_words])
    answer = public_result(raw, NO_SHARED)["answer"]
    assert answer["summary"] == paraphrase
    assert answer["caveats"] == [six_words]


def test_served_annual_does_not_use_compact_character_false_positive():
    shared = "internationalisation telecommunications manufacturing reorganisation competitiveness transformation"
    assert len(shared.replace(" ", "")) > 80
    summary = shared + " differ."
    raw = _annual_raw(shared + " increased.", summary=summary)
    assert public_result(raw, NO_SHARED)["answer"]["summary"] == summary
    # Historical projection intentionally remains identical, not silently rescored.
    raw.pop("tool_set")
    assert public_result(raw, NO_SHARED)["answer"]["summary"] == RIGHTS_NOTICE


@pytest.mark.parametrize("copy", [
    "ALPHA, beta; gamma\ndelta epsilon zeta eta",
    "alpha beta gam\u200bma delta epsilon zeta eta",
    "ａｌｐｈａ beta gamma delta epsilon zeta eta",
])
def test_served_annual_normalizes_copy_and_retains_surrounding_prose(copy):
    raw = _annual_raw("alpha beta gamma delta epsilon zeta eta", summary=f"Before: {copy}. After.")
    assert public_result(raw, NO_SHARED)["answer"]["summary"] == f"Before: {RIGHTS_NOTICE}. After."


def test_served_annual_merges_overlapping_spans_but_retains_separate_analysis():
    source = "alpha beta gamma delta epsilon zeta eta theta iota"
    raw = _annual_raw(source, summary=f"{source}; independent assessment; {source}")
    assert public_result(raw, NO_SHARED)["answer"]["summary"] == (
        f"{RIGHTS_NOTICE}; independent assessment; {RIGHTS_NOTICE}")


def test_served_annual_caps_citation_and_evidence_card_at_six_normalized_words():
    source = "alpha beta gamma delta epsilon zeta eta theta iota"
    claims = [{"text": "Independent finding.", "citations": [
        {"label": "P1", "quote": source},
        {"label": "P1", "quote": "alpha beta gamma delta epsilon zeta"},
    ]}]
    raw = _annual_raw(source, claims)
    result = public_result(raw, NO_SHARED)
    short = "alpha beta gamma delta epsilon zeta"
    assert result["answer"]["claims"][0]["citations"] == [{"label": "P1", "quote": short}]
    assert result["evidence"][0]["quotes"] == [short]
    assert raw["answer"]["claims"][0]["citations"][0]["quote"] == source


def test_served_annual_citation_cap_counts_hyphenated_words_not_whitespace():
    source = "alpha-beta gamma-delta epsilon-zeta eta-theta"
    raw = _annual_raw(source, [{"text": "Finding.", "citations": [{"label": "P1", "quote": source}]}])
    quote = public_result(raw, NO_SHARED)["answer"]["claims"][0]["citations"][0]["quote"]
    assert quote == "alpha-beta gamma-delta epsilon-zeta"
    assert validate.quote_in(quote, source)


def test_served_annual_rejects_invalid_quotes_and_does_not_guard_open_data_rows():
    source = "alpha beta gamma delta epsilon zeta eta"
    claims = [{"text": source, "citations": [
        {"label": "O1", "quote": source},
        {"label": "P1", "quote": "unsupported quote"},
    ]}]
    raw = _annual_raw("A separate report passage.", claims, summary=source, caveats=[source])
    raw["evidence_text"].update(O1=source, C1=source)
    result = public_result(raw, NO_SHARED)["answer"]
    assert result["summary"] == source and result["caveats"] == [source]
    assert result["claims"][0]["text"] == source
    assert result["claims"][0]["citations"] == [{"label": "O1", "quote": source}]


# ---- login lock default values / feedback binding / health -------------------------------------------------------

def test_feedback_is_bound_to_the_session_that_started_the_run(settings):
    async def scenario():
        async with client_for(settings) as (app, first):
            await login(first)
            second = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver")
            async with second:
                await login(second)
                assert (await first.post("/api/ask", json={"question": QUESTION})).status_code == 200
                body = {"run_id": "a1b2c3d4e5f6", "rating": "up", "comment": "ok"}
                assert (await second.post("/api/feedback", json=body)).status_code == 404  # someone else's run
                assert not audit_log.read_feedback()
                assert (await first.post("/api/feedback", json=body)).status_code == 200
                assert len(audit_log.read_feedback()) == 1
    asyncio.run(scenario())


def test_feedback_file_has_a_size_cap(monkeypatch):
    monkeypatch.setattr(audit_log, "FEEDBACK_MAX_BYTES", 600)
    for _ in range(10):
        audit_log.log_feedback("a1b2c3d4e5f6", "up", "x" * 100, "session")
    assert 0 < (audit_log.AUDIT_DIR / "feedback.jsonl").stat().st_size <= 600


def test_healthz_reports_the_corpus_fingerprint(settings):
    fingerprint = {"passage_set_sha256": "abc123abc123", "passages": 3, "chunks": 2}

    async def scenario():
        async with client_for(settings, shared_factory=lambda: SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}, corpus=fingerprint)) as (_, client):
            body = (await client.get("/healthz")).json()
            assert body["corpus"] == fingerprint and body["status"] == "ok" and "version" in body
        async with client_for(settings) as (_, client):
            assert (await client.get("/healthz")).json()["corpus"] is None
    asyncio.run(scenario())


def test_corpus_fingerprint_changes_with_the_passage_set():
    a = runtime.corpus_fingerprint({"p1:aa": {}, "p2:bb": {}}, {"c1": 1})
    assert a == runtime.corpus_fingerprint({"p2:bb": {}, "p1:aa": {}}, {"c1": 1})
    assert a["passages"] == 2 and a["chunks"] == 1
    assert a["passage_set_sha256"] != runtime.corpus_fingerprint({"p1:aa": {}, "p2:cc": {}}, {"c1": 1})["passage_set_sha256"]


def test_audit_record_carries_corpus_and_build_fallback(monkeypatch):
    res = {"run_id": "a1b2c3d4e5f6", "question": "q", "config": "c", "outcome": "abstained", "answer": None, "trace": [], "rounds": 0,
           "usage": {}, "seconds": 0.0, "corpus": {"passage_set_sha256": "abc123abc123", "passages": 3, "chunks": 2}}
    assert audit_log.run_record(res, "web")["version"]["corpus"] == res["corpus"]
    monkeypatch.setattr(audit_log.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("git")))
    monkeypatch.setenv("LABOURLENS_BUILD", "f7cab827deadbeefcafe")
    assert audit_log._version()["git_commit"] == "f7cab827dead"


# ---- run deadline in the default web runner ----------------------------------------------------------------------

def test_default_web_runner_passes_a_run_deadline(settings, monkeypatch):
    from labourlens.agent import graph

    seen = {}

    def fake(question, shared, cfg=None, save_trace=True, audit=None):
        seen["deadline"] = cfg.run_deadline_s
        return agent_result(question)

    monkeypatch.setattr(graph, "run_agent", fake)

    async def scenario():
        app = create_app(settings, shared_factory=lambda: NO_SHARED)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver") as client:
                await login(client)
                assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200
    asyncio.run(scenario())
    assert seen["deadline"] == settings.run_deadline_s == 80.0 and settings.run_deadline_s < settings.request_timeout


# ---- audit retention ---------------------------------------------------------------------------------------------

def test_prune_covers_events_and_old_feedback_records(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "DATA", tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(timespec="seconds")
    new = datetime.now(timezone.utc).isoformat(timespec="seconds")
    audit = audit_log.AUDIT_DIR
    audit.mkdir(parents=True)
    (audit / "feedback.jsonl").write_text(json.dumps({"ts": old, "run_id": "a"}) + "\n" + json.dumps({"ts": new, "run_id": "b"}) + "\n" + "not json\n")
    stale = audit / "events-2020-01-01.jsonl"
    fresh = audit / "events-2099-01-01.jsonl"
    for f in (stale, fresh):
        f.write_text("{}\n")
    long_ago = time.time() - 40 * 86400
    import os
    os.utime(stale, (long_ago, long_ago))
    gone = audit_log.prune(30)
    assert stale.name in gone and not stale.exists() and fresh.exists()
    kept = (audit / "feedback.jsonl").read_text().splitlines()
    assert [json.loads(x).get("run_id") for x in kept if x.startswith("{")] == ["b"] and "not json" in kept  # unreadable lines are kept
    assert any(g.startswith("feedback.jsonl (1 records)") for g in gone)


# ---- deploy: runtime data list, fail fast ------------------------------------------------------------------------

def _listed():
    return [x.strip() for x in (ROOT / "deploy/runtime-data.txt").read_text().splitlines() if x.strip() and not x.strip().startswith("#")]


def test_runtime_data_list_covers_every_local_passage_file_and_the_embedding_snapshot():
    listed = set(_listed())
    assert "data/index/embeddings/text-embedding-3-large/cache.npz" in listed  # preferred by VectorCache over the legacy pair
    assert not any(x.endswith(("keys.json", "vectors.npy")) for x in listed)
    local = sorted((ROOT / "data/passages").glob("*.jsonl")) if (ROOT / "data/passages").is_dir() else []
    if not local:
        pytest.skip("no local passages to compare with")
    assert {f"data/passages/{f.name}" for f in local} == {x for x in listed if x.startswith("data/passages/")}


@pytest.mark.corpus
def test_listed_runtime_files_alone_start_the_runtime_offline(tmp_path, monkeypatch):
    """Copy only the files in deploy/runtime-data.txt and start the world with embedding forbidden: the list is sufficient."""
    for rel in _listed():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, target)
    data = tmp_path / "data"
    for name, sub in (("DATA", ""), ("PASSAGES", "passages"), ("PROCESSED", "processed"), ("MANIFESTS", "manifests"), ("INDEX", "index")):
        monkeypatch.setattr(paths, name, data / sub if sub else data)
    monkeypatch.setenv("LABOURLENS_ALLOW_EMBED", "0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from labourlens.agent.tools import Shared

    shared = Shared()
    assert shared.corpus["chunks"] == len(shared.chunks_by_id) > 0 and len(shared.obs) > 0


def test_missing_chunk_vectors_stop_startup_without_calling_the_embeddings_api(tmp_path, monkeypatch):
    from labourlens.retrieval import dense

    chunk = SimpleNamespace(chunk_id="c1", text="some chunk text", document_title="t", section_heading="h")
    monkeypatch.setattr(paths, "INDEX", tmp_path / "index")
    monkeypatch.setattr(runtime.ck, "load_passages", lambda: [])
    monkeypatch.setattr(runtime.ck, "build_chunks", lambda cfg, passages: [chunk])
    monkeypatch.setattr(dense, "embed", lambda *a, **k: pytest.fail("embeddings API must not be called at startup"))
    monkeypatch.setenv("LABOURLENS_ALLOW_EMBED", "0")
    with pytest.raises(dense.EmbeddingError, match="1 of 1 chunks"):
        runtime.load_world()


def test_container_defaults_forbid_startup_embedding():
    assert "LABOURLENS_ALLOW_EMBED=0" in (ROOT / "Dockerfile").read_text()
    assert 'LABOURLENS_ALLOW_EMBED: "0"' in (ROOT / "deploy/docker-compose.yml").read_text()
