"""Corpus-v3 batch (heldout-v2 sources): host allow-list, catalog metadata, adapters on synthetic CSVs, and additivity.

No publisher text is committed: PDFs and CSV rows here are synthetic. Only the last test reads local build outputs (marked corpus).
"""
import json
import hashlib
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pymupdf
import pytest

from labourlens import paths
from labourlens.data import acquire, catalog, fingerprint, normalize as n, validate
from labourlens.data import build as data_build
from labourlens.data import fetch, raw_store
from labourlens.retrieval import chunk as ck

BATCH_DOCS = {"mom-wage-practices2025", "mom-nwc-lower-wage2025", "mti-2026-q2-feature-ai-employment"}
V4_DOCS = {d["source_id"] for d in __import__("yaml").safe_load((paths.SPECS / "sources.d" / "documents-2020-2022.yaml").read_text())["documents"]}  # D-080
BATCH_DATASETS = {"unit_labour_cost_index_quarterly", "value_added_per_worker_quarterly", "avg_weekly_paid_hours_quarterly"}
FIRST = {"unit_labour_cost_index_quarterly": "1980-Q1", "value_added_per_worker_quarterly": "1991-Q1", "avg_weekly_paid_hours_quarterly": "1998-Q1"}


# ---- host allow-list -------------------------------------------------------------------------------------------------------------------

def test_mti_pdf_host_is_allowed_over_https_only():
    url = "https://isomer-user-content.by.gov.sg/1004/00000000-0000-0000-0000-000000000000/FA_2Q26.pdf"
    acquire._check_host(url)
    with pytest.raises(acquire.AcquisitionError):
        acquire._check_host(url.replace("https://", "http://"))


@pytest.mark.parametrize("url", [
    "https://isomer-user-content.by.gov.sg.evil.example/x.pdf",
    "https://evil.example/isomer-user-content.by.gov.sg/x.pdf",
    "https://www.mti.gov.sg/resources/x",  # the MTI page host is not allow-listed; only the PDF host is
    "https://isomer-user-content.by.gov.sg@evil.example/x.pdf",
])
def test_lookalike_and_page_hosts_are_refused(url):
    with pytest.raises(acquire.AcquisitionError):
        acquire._check_host(url)


def test_every_new_download_host_is_allowed():
    for d in catalog.documents():
        if d["source_id"] in BATCH_DOCS:
            acquire._check_host(d["download_url"])


# ---- catalog metadata ------------------------------------------------------------------------------------------------------------------

def test_batch_is_exactly_the_approved_labour_only_set():
    docs = {d["source_id"] for d in catalog.documents() if d.get("expansion_batch") == "heldout-v2"}
    sets = {d["source_id"] for d in catalog.datasets() if d.get("expansion_batch") == "heldout-v2"}
    assert docs == BATCH_DOCS and sets == BATCH_DATASETS
    everything = {e["source_id"] for k in ("documents", "datasets") for e in catalog.sources()[k]}
    assert not {i for i in everything if i.startswith("mti-") and i != "mti-2026-q2-feature-ai-employment"}, "no MTI GDP advance/survey sources"


def test_new_documents_are_local_only_with_complete_metadata():
    for d in catalog.documents():
        if d["source_id"] not in BATCH_DOCS:
            continue
        assert d["rights_status"] in {"unresolved", "verified_all_rights_reserved"}  # never verified_open_licence: build marks only that committable
        assert "Local-only" in d["rights_note"]
        assert d["publisher"] and d["canonical_url"].startswith("https://") and d["source_type"] == "report_pdf"
        assert date.fromisoformat(d["publication_date"]) and date.fromisoformat(d["period_start"]) <= date.fromisoformat(d["period_end"])
    mti = next(d for d in catalog.documents() if d["source_id"] == "mti-2026-q2-feature-ai-employment")
    assert mti["rights_status"] == "unresolved"


def test_new_datasets_flag_licence_for_verification_and_have_adapters():
    for d in catalog.datasets():
        if d["source_id"] not in BATCH_DATASETS:
            continue
        assert "to verify on dataset page" in d["rights_note_extra"]
        assert "to verify on dataset page" in fetch.dataset_rights_note(d)
        assert fetch.ODL_NOTE in fetch.dataset_rights_note(d)
        spec = catalog.adapter_spec(d["source_id"])
        assert spec["source_id"] == d["source_id"]
        assert spec["expected_first_period"] == FIRST[d["source_id"]] and spec["expected_last_period"] == "2026-Q2"


def test_existing_datasets_keep_the_original_rights_note():
    assert fetch.dataset_rights_note({"source_id": "x"}) == fetch.ODL_NOTE


# ---- adapters on synthetic fixtures ----------------------------------------------------------------------------------------------------

def _quarters(first: str, last: str):
    y, q = int(first[:4]), int(first[-1])
    while f"{y}-Q{q}" <= last:
        yield y, q
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)


def _wide(first: str, last: str, rows: dict[str, list[str]], first_na: int = 0, spec_id: str = "unit_labour_cost_index_quarterly"):
    """Wide table, one column per quarter; `rows` maps label -> constant value, the first `first_na` quarters are 'na'."""
    cols = list(_quarters(first, last))
    header = ["DataSeries"] + [f"{y}{q}Q" for y, q in cols]
    body = [[label] + (["na"] * first_na + [vals[0]] * (len(cols) - first_na)) for label, vals in rows.items()]
    return header, body


def _checks(spec_id: str, rows_header_body, extra_ok=True):
    spec = catalog.adapter_spec(spec_id)
    header, body = rows_header_body
    res = n.NormResult(spec_id, "snap-test", rows_read=len(body))
    (n._sector_wide if spec["adapter"] == "sector_wide" else n._long)(spec, "snap-test", header, body, res)
    obs = pd.DataFrame([o.model_dump(mode="json") for o in res.observations])
    quarantine = pd.DataFrame([q.__dict__ for q in res.quarantined], columns=["source_id", "snapshot_id", "locator", "raw_value", "reason"])
    per_source = {spec_id: {"status": "ok"}}
    out = {c["name"]: c for c in validate.check_datasets(obs, quarantine, per_source) if c["name"].startswith(f"dataset.{spec_id}.")}
    return res, out


@pytest.mark.parametrize("sid,total,child", [("unit_labour_cost_index_quarterly", "100.0", "90.0"), ("value_added_per_worker_quarterly", "30000", "25000")])
def test_wide_adapters_accept_a_complete_synthetic_table(sid, total, child):
    spec = catalog.adapter_spec(sid)
    w = spec["indent_width"]
    h, b = _wide(spec["expected_first_period"], "2026-Q2", {"Total": [total], " " * w + "Services": [child]})
    res, c = _checks(sid, (h, b))
    assert not res.quarantined
    assert {o.unit for o in res.observations} == {spec["measures"][0]["unit"]}
    assert all(v["status"] == "pass" for k, v in c.items() if k.endswith(("first_last_period", "values_in_plausible_range", "in_scope_rows_cover_declared_quarters", "no_duplicate_keys")))


@pytest.mark.parametrize("sid", ["unit_labour_cost_index_quarterly", "value_added_per_worker_quarterly"])
def test_wide_adapters_enforce_exact_first_and_last_period(sid):
    spec = catalog.adapter_spec(sid)
    first = spec["expected_first_period"]
    # first quarter is 'na', so the first published period is the next quarter: the expected first period must NOT be silently accepted
    h, b = _wide(first, "2026-Q2", {"Total": ["100.0" if sid.startswith("unit") else "30000"]}, first_na=1)
    _, c = _checks(sid, (h, b))
    assert c[f"dataset.{sid}.first_last_period"]["status"] == "fail"
    # table ends one quarter early
    h, b = _wide(first, "2026-Q1", {"Total": ["100.0" if sid.startswith("unit") else "30000"]})
    _, c = _checks(sid, (h, b))
    assert c[f"dataset.{sid}.first_last_period"]["status"] == "fail"


def test_wide_adapter_plausible_range_applies_to_total_rows():
    sid = "value_added_per_worker_quarterly"
    h, b = _wide("1991-Q1", "2026-Q2", {"Total": ["999999"]})
    _, c = _checks(sid, (h, b))
    assert c[f"dataset.{sid}.values_in_plausible_range"]["status"] == "fail"


def test_wide_adapter_in_scope_gap_is_reported_not_zero_filled():
    sid = "unit_labour_cost_index_quarterly"
    h, b = _wide("1980-Q1", "2026-Q2", {"Total": ["100.0"]})
    b[0][-1] = "na"  # latest quarter has no number
    res, c = _checks(sid, (h, b))
    last = [o for o in res.observations if o.period == "2026-Q2"][0]
    assert last.value is None and last.missing_reason
    assert c[f"dataset.{sid}.in_scope_values_present"]["status"] == "warn"
    assert c[f"dataset.{sid}.first_last_period"]["status"] == "fail"  # last published period is 2026-Q1, not the declared 2026-Q2


def test_undeclared_token_in_wide_table_is_quarantined_not_dropped():
    spec = catalog.adapter_spec("value_added_per_worker_quarterly")
    res = n.NormResult(spec["source_id"], "snap-test")
    n._sector_wide(spec, "snap-test", ["DataSeries", "20261Q", "20262Q"], [["Total", "oops", "30000"]], res)
    assert len(res.observations) == 1 and len(res.quarantined) == 1


def test_hours_adapter_exact_periods_range_and_drift():
    sid = "avg_weekly_paid_hours_quarterly"
    spec = catalog.adapter_spec(sid)
    assert spec["expected_columns"] == ["quarter", "total_paid_hours"]
    rows = [[f"{y}-Q{q}", "44.1"] for y, q in _quarters("1998-Q1", "2026-Q2")]
    res, c = _checks(sid, (spec["expected_columns"], rows))
    assert {o.unit for o in res.observations} == {"hours_per_week"} and {o.population for o in res.observations} == {"employees"}
    assert all(c[f"dataset.{sid}.{k}"]["status"] == "pass" for k in ("first_last_period", "values_in_plausible_range", "in_scope_rows_cover_declared_quarters"))
    _, c = _checks(sid, (spec["expected_columns"], rows[1:]))  # starts 1998-Q2
    assert c[f"dataset.{sid}.first_last_period"]["status"] == "fail"
    bad = rows[:-1] + [["2026-Q2", "70"]]
    _, c = _checks(sid, (spec["expected_columns"], bad))
    assert c[f"dataset.{sid}.values_in_plausible_range"]["status"] == "fail"
    with pytest.raises(n.SpecViolation):
        n._long(spec, "snap-test", ["quarter", "hours"], [], n.NormResult(sid, "snap-test"))


def test_new_observation_ids_never_collide_with_existing_sources():
    old = catalog.adapter_spec("employment_change_by_sector")
    new = catalog.adapter_spec("unit_labour_cost_index_quarterly")
    ids = []
    for spec in (old, new):
        res = n.NormResult(spec["source_id"], "snap-test")
        n._sector_wide(spec, "snap-test", ["DataSeries", "20261Q"], [["Total", "10"]], res)
        ids.append({o.observation_id for o in res.observations})
    assert ids[0] and ids[1] and not ids[0] & ids[1]


# ---- additivity: adding a source does not change existing passages or chunks ----------------------------------------------------------

def _pdf(path, words: str):
    doc = pymupdf.open()
    page = doc.new_page()
    for i in range(4):
        page.insert_textbox(pymupdf.Rect(50, 80 + i * 120, 540, 190 + i * 120),
                            f"Synthetic paragraph {i} about {words}. " * 4, fontsize=11)
    doc.save(path)
    doc.close()


def _entry(sid, path):
    return SimpleNamespace(source_id=sid, retrieval_status="ok", raw_path=str(path), snapshot_id=f"snap-{sid}",
                           canonical_url="https://example.org", title=f"Synthetic {sid}", publication_date="2026-01-01",
                           release_stage="final", rights_status="unresolved", source_type="report_pdf")


def _run_build(monkeypatch, tmp_path, name, sids, pdfs):
    out = tmp_path / name
    out.mkdir()
    docs = [{"source_id": s} for s in sids]
    manifest = {s: _entry(s, pdfs[s]) for s in sids}
    monkeypatch.setattr(catalog, "documents", lambda: docs)
    monkeypatch.setattr(raw_store, "load_manifest", lambda: manifest)
    monkeypatch.setattr(paths, "PASSAGES", out)
    passages, stats = data_build.build_passages()
    return out, passages, stats


def test_adding_a_document_leaves_existing_passages_and_chunks_byte_identical(monkeypatch, tmp_path):
    pdfs = {"mom-synth-a": tmp_path / "a.pdf", "mti-synth-b": tmp_path / "b.pdf"}
    _pdf(pdfs["mom-synth-a"], "unemployment and vacancies")
    _pdf(pdfs["mti-synth-b"], "productivity and labour costs")
    out_a, p_a, s_a = _run_build(monkeypatch, tmp_path, "only-a", ["mom-synth-a"], pdfs)
    out_ab, p_ab, s_ab = _run_build(monkeypatch, tmp_path, "a-and-b", ["mom-synth-a", "mti-synth-b"], pdfs)
    assert p_a, "fixture must yield passages"
    assert (out_a / "mom-synth-a.jsonl").read_bytes() == (out_ab / "mom-synth-a.jsonl").read_bytes()
    assert [p.passage_id for p in p_a] == [p.passage_id for p in p_ab if p.source_id == "mom-synth-a"]
    assert [p.text_sha256 for p in p_a] == [p.text_sha256 for p in p_ab if p.source_id == "mom-synth-a"]
    assert s_a[0] == s_ab[0]
    assert not {p.passage_id for p in p_a} & {p.passage_id for p in p_ab if p.source_id == "mti-synth-b"}
    load = lambda d: [json.loads(line) for f in sorted(d.glob("*.jsonl")) for line in f.read_text().splitlines()]
    cfg = ck.CONFIGS["merge200"]
    only = {c.chunk_id: c.text_sha256 for c in ck.build_chunks(cfg, load(out_a))}
    both = {c.chunk_id: c.text_sha256 for c in ck.build_chunks(cfg, load(out_ab)) if c.source_id == "mom-synth-a"}
    assert only and only == both


# ---- additivity on the real build outputs (needs the fetched/built corpus; skipped before the v3 fetch) --------------------------------

def _v3_built() -> bool:
    mf = paths.MANIFESTS / "manifest.json"
    return mf.exists() and all(s in mf.read_text() for s in BATCH_DOCS | BATCH_DATASETS)


def _hashes_as_extract_02() -> dict[str, str]:
    """File hashes with only the `parser_version` value reverted to extract-0.2 (corpus v3.1 bumped the parser; v1/v2/v3 baselines predate it)."""
    out = {}
    for f in sorted(paths.PASSAGES.glob("*.jsonl")):
        out[f.name] = hashlib.sha256(f.read_bytes().replace(b'"parser_version": "extract-0.3"', b'"parser_version": "extract-0.2"')).hexdigest()
    return out


@pytest.mark.corpus
@pytest.mark.skipif(not _v3_built(), reason="corpus v3 sources not fetched yet")
def test_corpus_v2_passages_and_observations_unchanged_after_v3_build():
    snaps = paths.EXPERIMENTS / "corpus-snapshots"
    v2 = json.loads((snaps / "v2.json").read_text())
    now = _hashes_as_extract_02()
    changed = [f for f, h in v2["passage_file_sha256"].items() if now.get(f) != h]
    assert not changed, f"corpus-v2 passage files changed: {changed}"
    assert len(now) == v2["document_files"] + len(BATCH_DOCS) + len(V4_DOCS)  # D-080 added the 2020 to 2022 documents; every earlier file is unchanged
    base = json.loads((snaps / "v2-observations.json").read_text())["observations"]
    cur = fingerprint.observation_hashes()
    assert {s: cur.get(s) for s in base} == base
    assert set(cur) - set(base) == BATCH_DATASETS


@pytest.mark.corpus
@pytest.mark.skipif(not _v3_built(), reason="corpus v3 sources not fetched yet")
def test_corpus_v3_1_changes_only_the_mti_feature_article():
    """Corpus v3.1 (extract-0.3, refined garbled-text rule): every passage file except the MTI feature article equals its v3 baseline once the
    parser_version value is reverted; no passage id changes; only the 246 control-character passages stay `garbled`; no passage became garbled."""
    snaps = paths.EXPERIMENTS / "corpus-snapshots"
    v3 = json.loads((snaps / "v3.json").read_text())
    now = _hashes_as_extract_02()
    changed = sorted(f for f, h in v3["passage_file_sha256"].items() if now.get(f) != h)
    assert changed == ["mti-2026-q2-feature-ai-employment.jsonl"], changed
    passages = [p for p in ck.load_passages() if p["source_id"] not in V4_DOCS]  # D-080 (corpus v4) only adds documents
    assert len(passages) == v3["passages"]
    assert {p["parser_version"] for p in passages} == {"extract-0.3"}
    garbled = [p for p in passages if p["quality_flag"] == "garbled"]
    assert garbled and all("control characters" in p["quality_note"] for p in garbled)
    assert not [p for p in passages if p["source_id"] == "mti-2026-q2-feature-ai-employment" and p["quality_flag"] == "garbled"]
    v31 = snaps / "v3.1.json"
    if v31.exists():
        assert json.loads(v31.read_text())["chunk_corpus_sha256"] == ck.corpus_hash(ck.build_chunks(ck.CONFIGS["merge200"], passages))


@pytest.mark.skipif(not _v3_built(), reason="corpus passages are local only")
def test_corpus_v4_only_adds_documents_and_changes_no_existing_passage_id():
    """D-080: the 2020 to 2022 documents are additive. Every v3.1 passage id survives, and the cached chunks of the earlier documents are unchanged."""
    snaps = paths.EXPERIMENTS / "corpus-snapshots"
    v31 = json.loads((snaps / "v3.1.json").read_text())
    passages = ck.load_passages()
    old = [p for p in passages if p["source_id"] not in V4_DOCS]
    assert len(old) == v31["passages"] 
    # Four fetched PDFs give no passage: their text layer is not read by the extractor (hidden or glyph-image text). Recorded in the data sheet, not repaired.
    assert V4_DOCS - {p["source_id"] for p in passages} == {"mom-lf2020-coverage-methodology", "mom-lf2021-survey-findings", "mom-lf2021-survey-highlights", "mom-lf2021-coverage-methodology"}
    assert ck.corpus_hash(ck.build_chunks(ck.CONFIGS["merge200"], old)) == v31["chunk_corpus_sha256"]
    v4 = json.loads((snaps / "v4.json").read_text())
    assert (v4["passages"], v4["document_files"]) == (len(passages), v31["document_files"] + len(V4_DOCS))


def test_corpus_fingerprint_content_hash_sees_a_reflag_that_passage_ids_do_not():
    from labourlens.retrieval import runtime

    a = runtime.corpus_fingerprint({"p1:aa": {"quality_flag": "garbled"}}, {})
    b = runtime.corpus_fingerprint({"p1:aa": {"quality_flag": "ok"}}, {})
    assert a["passage_set_sha256"] == b["passage_set_sha256"] and a["content_sha256"] != b["content_sha256"]
