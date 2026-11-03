"""Served-only narrow missing-period contradiction check (D-084). No model call."""
from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer
from labourlens.answer.validate import missing_period_errors


def answer(reason):
    return Answer(status="abstained", summary="", claims=[], caveats=[], reason=reason, clarification_question="")


def obs(text="Rate | 2021-Q3 | 3.5%", label="O1"):
    return ContextPassage(label, "id", "source", "title", None, "dataset_snapshot", "2021-Q3", text)


def test_explicit_missing_quarter_contradiction():
    errors = missing_period_errors(answer("No data for 2021-Q3."), [obs()])
    assert len(errors) == 1 and "published observation" in errors[0]
    assert missing_period_errors(answer("No quarterly values are available for 2021-Q3."), [obs()])


def test_missing_method_or_report_is_not_missing_statistics():
    for reason in ("No tool computes this quantity.", "No report commentary is available for 2021-Q3.", "No data for 2020-Q1."):
        assert not missing_period_errors(answer(reason), [obs()])


def test_missing_values_and_passages_do_not_prove_observation_exists():
    a = answer("No data for 2021-Q3.")
    assert not missing_period_errors(a, [obs("Rate | 2021-Q3 | no published number (dash)")])
    assert not missing_period_errors(a, [obs(label="P1")])
    assert not missing_period_errors(a, [])
