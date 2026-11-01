"""The report's `serving` section: what the live app adds to the evaluated system, from committed measurement files."""

import re
from pathlib import Path

from labourlens.report.build import _serving

STATIC = Path(__file__).resolve().parents[2] / "web" / "static"


class Artifacts:
    def __init__(self, files):
        self.files = files

    def mapping(self, path):
        value = self.files.get(path)
        return value if isinstance(value, dict) else {}


def test_serving_projects_triage_corpus_and_rights_numbers_only():
    triage = {
        "n": 409,
        "false_out_of_scope_gold_v2": {"n": 333, "false_out_of_scope": 0, "failed_open": 0, "diverted_case_ids": []},
        "false_out_of_scope_threats": {"n": 36, "false_out_of_scope": 1, "diverted_case_ids": ["T-D05"]},
        "offtopic": {"n": 40, "expected_not_in_scope": 30, "recall_not_in_scope": 30, "by_kind": {"clear_offtopic": {"n": 14, "correct": 14}}},
        "cost_and_latency": {"calls": 409, "total_cost_usd": 0.050601, "latency_p50_s": 1.56, "latency_p95_s": 2.44},
        "config": {"model": "gpt-6-luna", "prompt": "triage_v1", "git_commit": "e361fcdaca4060014e0dc42aabfb860983e5bb30"},
    }
    snapshot = {"label": "v3.1", "document_files": 49, "passages": 16419, "chunks": 1847, "gold_sha256": "x" * 64}
    diff = {"parser_version": {"before": "extract-0.2", "after": "extract-0.3"}, "quality_flags": {"transitions": {"garbled->ok": 16}, "new_garbled": 0}}
    sources = {"metrics": {"sources": 85}, "rows": [
        {"type": "dataset_csv", "rights_status": "assumed_open_unverified"},
        {"type": "release_html", "rights_status": "unresolved"},
        {"type": "report_pdf", "rights_status": "unresolved"},
        {"type": "report_pdf", "rights_status": "verified_all_rights_reserved"},
    ]}
    section = _serving(Artifacts({
        "experiments/triage/triage-v1-luna/metrics.json": triage,
        "experiments/corpus-snapshots/v3.1.json": snapshot,
        "experiments/corpus-snapshots/v3.1-diff.json": diff,
    }), sources)
    assert section["status"] == "available"
    assert section["triage"]["gold_and_fresh"]["n"] == 333 and section["triage"]["gold_and_fresh"]["false_out_of_scope"] == 0
    assert section["triage"]["threats"]["false_out_of_scope"] == 1 and section["triage"]["diverted_threat_cases"] == ["T-D05"]
    assert section["triage"]["cost_and_latency"]["total_cost_usd"] == 0.050601
    assert section["rows"] == [{"kind": "clear_offtopic", "n": 14, "correct": 14, "provenance": ["experiments/triage/triage-v1-luna/metrics.json"]}]
    assert section["corpus"]["passages"] == 16419 and section["corpus"]["chunks"] == 1847 and section["corpus"]["sources"] == 85
    assert section["corpus"]["parser_after"] == "extract-0.3" and section["corpus"]["flag_transitions"] == {"garbled_to_ok": 16}
    assert section["rights"] == {"datasets_unverified": 1, "sources_unresolved": 2, "sources_all_rights_reserved": 1}
    assert "git_commit" not in str(section) and "gold_sha256" not in str(section)


def test_serving_is_missing_without_artifacts():
    assert _serving(Artifacts({}), {"rows": [], "metrics": {}})["status"] == "missing"


def test_serving_chapter_is_wired_into_deck_and_report():
    slides = (STATIC / "presentation" / "slides.js").read_text()
    pool = (STATIC / "js" / "report-pool.js").read_text()
    assert "renderServing" in slides and "renderServing" in pool
    assert re.search(r"appendix\('M', 'Live app against the evaluated system'", slides)
    assert "N. Cut from the talk" in slides and "M. Cut from the talk" not in slides
    chapter = (STATIC / "presentation" / "ch-serving.js").read_text()
    for needle in ("via MCP", "scope check", "small-talk", "provider-side spend cap", "Each configuration was run once", "Temperature and reasoning effort"):
        assert needle.lower() in chapter.lower(), needle
