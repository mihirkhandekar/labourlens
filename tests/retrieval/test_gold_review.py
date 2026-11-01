import json
from collections import Counter

import pytest

from labourlens import paths
from labourlens.retrieval import gold


def reviewed(source="owner_manual"):
    return {
        "review_status": "owner_reviewed", "reviewed_by": "Mihir",
        "owner_review": {"reviewer": "Mihir", "decision_source": source, "date": "2026-10-31"},
    }


@pytest.mark.parametrize("source", ["owner_manual", "agreed_with_ai_suggestion"])
def test_per_card_owner_actions_are_valid_not_independent_review(source):
    assert gold.review_errors(reviewed(source)) == []


def test_draft_without_owner_action_stays_null():
    assert gold.review_errors({"review_status": "draft", "reviewed_by": None}) == []
    assert gold.review_errors({"review_status": "draft", "reviewed_by": ""})
    assert gold.review_errors({"review_status": "draft", "reviewed_by": None, "owner_review": reviewed()["owner_review"]})


@pytest.mark.parametrize("field,value", [
    ("reviewer", "Someone else"), ("decision_source", "ai_only"),
    ("decision_source", "owner_endorsement"), ("date", "2026-02-30"),
    ("date", "20261031"), ("date", None), ("comment", "private comment"),
    ("decision_source", []), ("decision_source", {}), ("date", 20261031),
])
def test_review_provenance_rejects_invalid_or_private_fields(field, value):
    case = reviewed()
    case["owner_review"][field] = value
    assert gold.review_errors(case)


@pytest.mark.parametrize("updates", [
    {"review_status": "independently_reviewed"}, {"reviewed_by": None},
    {"reviewed_by": " "}, {"owner_review": None}, {"owner_review": {}},
])
def test_review_requires_explicit_matching_owner_provenance(updates):
    case = reviewed()
    case.update(updates)
    assert gold.review_errors(case)


def test_v35_review_scope_and_owner_confirmed_labels():
    cases = [json.loads(line) for line in (paths.EXPERIMENTS / "gold/draft_cases.jsonl").read_text().splitlines() if line.strip()]
    assert len(cases) == 268
    assert Counter(c["review_status"] for c in cases) == {"owner_reviewed": 45, "draft": 223}
    assert all(not gold.review_errors(c) for c in cases)
    reviewed_cases = [c for c in cases if c["review_status"] == "owner_reviewed"]
    assert Counter(c["owner_review"]["decision_source"] for c in reviewed_cases) == {"owner_manual": 3, "agreed_with_ai_suggestion": 42}
    assert Counter(c["split"] for c in reviewed_cases) == {"dev": 14, "heldout": 31}
    by_id = {c["case_id"]: c for c in cases}
    assert by_id["HO-022"]["expected_behavior"] == "answer"
    assert by_id["HO-022"]["abstain_reason"] is None
    assert by_id["DEV-018"]["expected_behavior"] == "clarify"
    assert "period" in by_id["DEV-018"]["abstain_reason"]
    assert "overrides the export" in by_id["DEV-018"]["notes"]
    assert by_id["DEV-018"]["evidence_text"] == by_id["DEV-018"]["evidence_data"] == []


def test_generated_review_sheet_does_not_claim_unreviewed_or_independent():
    sheet = gold.review_sheet()
    assert "not independent inter-rater evidence" in sheet
    assert "gold v3.7" in sheet
    assert "not reviewed by a human" not in sheet


def test_v36_changes_only_evidence_ids_with_complete_audit():
    import copy
    import hashlib

    path = paths.EXPERIMENTS / "gold/draft_cases.jsonl"
    audit = json.loads((path.parent / "evidence-migration-v3.6.json").read_text())
    cases = [json.loads(line) for line in path.read_text().splitlines()]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == audit["after_gold_sha256"]
    assert len(audit["missing_ids"]) == 61
    assert len(audit["surviving_metadata_changes"]) == 67
    assert audit["unmapped_ids"] == []
    assert audit["cases_changed"] == 96
    assert sum(row["exact_joined_text"] for row in audit["missing_ids"]) == 54
    by_case = {case["case_id"]: case for case in cases}
    for row in audit["missing_ids"]:
        assert row["old_word_overlap"] / row["old_word_count"] >= 0.97
        assert row["references"]
        for ref in row["references"]:
            ids = {pid for evidence in by_case[ref["case_id"]][ref["field"]]
                   for pid in evidence["passage_ids"]}
            assert row["old_passage_id"] not in ids
            assert set(row["new_passage_ids"]) <= ids
    projection = copy.deepcopy(cases)

    def strip(value):
        if isinstance(value, dict):
            value.pop("passage_ids", None)
            for child in value.values():
                strip(child)
        elif isinstance(value, list):
            for child in value:
                strip(child)

    strip(projection)
    digest = hashlib.sha256(json.dumps(projection, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert digest == audit["non_id_fields_sha256"]
    assert len(audit["supplemental_ids_outside_branch_two_field_scan"]) == 3
