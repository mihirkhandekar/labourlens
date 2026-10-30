from labourlens.retrieval import evaluate as ev
from labourlens.retrieval.bm25_index import BM25Config
from labourlens.retrieval.chunk import CONFIGS

from tests.retrieval.test_chunk_tokenize_index import _p


def _passages():
    ps = [_p("A", i, "H", 25, page=1 + i) for i in range(6)]
    ps[1]["text"] = "retrenchment rose in services during the quarter"
    ps[4]["text"] = "vacancies per unemployed person eased"
    return ps


def _case(cid, q, pid):
    return {"case_id": cid, "family": "factual_lookup", "question": q, "expected_behavior": "answer",
            "evidence_text": [{"source_id": "A", "passage_ids": [pid], "locator": "p", "primary": True, "why": ""}]}


def test_metrics_reflect_known_ranks():
    cases = [_case("c1", "retrenchment services", "A:1"), _case("c2", "vacancies unemployed person", "A:4"), _case("c3", "retrenchment", "A:5")]
    r = ev.run_config(CONFIGS["blocks"], BM25Config(), cases, _passages())
    m = r["metrics"]
    assert m["hit@1"] == round(2 / 3, 4)  # c3 asks for A:5 but only A:1 mentions retrenchment
    assert m["hit@10"] == round(2 / 3, 4)
    assert r["rows"][2]["first_relevant_rank"] is None
    assert m["mrr"] == round(2 / 3, 4)


def test_chunk_variants_are_scored_on_passage_labels():
    ps = _passages()
    case = _case("c1", "retrenchment services", "A:1")
    for name in ("blocks", "merge120", "fixed150"):
        r = ev.run_config(CONFIGS[name], BM25Config(), [case], ps)
        assert r["rows"][0]["first_relevant_rank"] == 1, name


def test_non_answer_cases_are_excluded_from_retrieval_scoring():
    answer = _case("c1", "x", "A:1")
    abstain = {**answer, "case_id": "c2", "expected_behavior": "abstain", "evidence_text": []}
    assert [c["case_id"] for c in ev.text_cases([answer, abstain])] == ["c1"]
