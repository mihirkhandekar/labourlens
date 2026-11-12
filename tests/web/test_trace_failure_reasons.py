"""A failed answer check is explained in the Activity trace by fixed categories only, never by the validator's free text."""
import asyncio
import json
import re
from pathlib import Path

from labourlens.answer import validate
from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer
from labourlens.report.app import _ERROR_CODES, public_trace_item
from test_app import QUESTION, agent_result, client_for, login, settings  # noqa: F401  (settings is a fixture)

STATIC = Path(__file__).resolve().parents[2] / "web" / "static"
PASSAGE = "Hiring in the services sector remained resilient while manufacturing demand softened across several export segments."


def test_every_validator_error_maps_to_a_known_category():
    errors = ["claim 1 has no citation", "claim 2 cites 'P9', which was not in the context", "claim 1 quote is not verbatim in P1",
              "claim 3 quote from P2 is longer than 40 words", "claim 1 cites P1, which is flagged as containing instructions and cannot be used as evidence",
              'summary copies a run of report wording: "SECRET PASSAGE TEXT"; paraphrase it in your own words', "status is answered but there are no claims",
              "status is abstained but claims were given", "output is not valid JSON", "output does not match the answer schema at: claims.0",
              "abstention says no data for 2025-Q4, but a published observation for that quarter is supplied; identify the missing method",
              "report search timed out and the question asks for reasons, but the answer does not say that report evidence could not be collected; state this",
              "something the validator never says"]
    kinds = validate.error_categories(errors)
    assert set(kinds) <= _ERROR_CODES
    assert kinds["other"] == 1 and kinds["incomplete_answer"] == 2 and kinds["bad_format"] == 2
    assert sum(kinds.values()) == len(errors)
    assert "SECRET" not in json.dumps(kinds)


def test_real_validator_failure_is_categorised():
    answer = Answer.model_validate(dict(status="answered", summary="Services hiring held up.", clarification_question="", reason="", caveats=[],
                                        claims=[dict(text="Services hiring held up.", citations=[dict(label="P1", quote="this quote is invented")])]))

    item = ContextPassage("P1", "p1", "s1", "Report", None, "final", "p. 1", PASSAGE)
    report = validate.check(answer, [item])
    assert report.errors and validate.error_categories(report.errors) == {"quote_not_found": 1}


def test_public_trace_item_exposes_only_codes_and_counts():
    event = {"node": "validate_answer", "event": "invalid", "detail": {
        "attempt": 1, "n_errors": 3, "errors": ["quote copied: SECRET"], "ungrounded_numbers": ["claim 1: 9,999"],
        "error_kinds": {"quote_not_found": 2, "copied_wording": 1, "SECRET": 5, "no_citation": "SECRET", "other": True}}}
    item = public_trace_item(event)
    assert item["detail"] == {"error_kinds": {"quote_not_found": 2, "copied_wording": 1}, "attempt": 1}
    assert "SECRET" not in json.dumps(item) and "9,999" not in json.dumps(item)


def test_other_nodes_do_not_gain_the_failure_fields():
    item = public_trace_item({"node": "execute_tool", "event": "ok", "detail": {"tool": "get_series", "error_kinds": {"other": 1}, "attempt": 1}})
    assert item["detail"] == {"tool": "get_series"}


def test_workbench_has_a_plain_label_for_every_server_category():
    js = (STATIC / "js" / "workbench.js").read_text(encoding="utf-8")
    block = js.split("const CHECK_FAILURE = {", 1)[1].split("};", 1)[0]
    labelled = set(re.findall(r"^\s*(\w+):", block, flags=re.M))
    assert labelled == _ERROR_CODES
    assert "Why the check failed" in js and "detail.error_kinds" in js


def test_api_returns_failure_categories_for_an_invalid_run_and_no_validator_text(settings):  # noqa: F811
    def runner(question, shared):
        raw = agent_result(question)
        raw.update(outcome="invalid", answer=None, errors=['summary copies a run of report wording: "SECRET PASSAGE TEXT"; paraphrase it'])
        raw["trace"] = [*raw.get("trace", []), {"node": "validate_answer", "event": "invalid", "detail": {
            "attempt": 2, "n_errors": 1, "errors": ["SECRET PASSAGE TEXT"], "error_kinds": {"copied_wording": 1}}}]
        return raw

    async def scenario():
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            assert response.status_code == 200, response.text
            body = response.json()
            step = next(e for e in body["trace"] if e["node"] == "validate_answer")
            assert step["event"] == "invalid" and step["detail"] == {"error_kinds": {"copied_wording": 1}, "attempt": 2}
            assert "SECRET" not in response.text
            assert body["answer"]["status"] == "abstained"

    asyncio.run(scenario())
