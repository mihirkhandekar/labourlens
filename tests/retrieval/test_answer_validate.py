from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer, Citation, Claim
from labourlens.answer.validate import check, key_numbers, norm, numbers

P1 = ContextPassage("P1", "doc:p1", "doc", "T", "2026-01-01", "final", "p.1",
                    "Synthetic test headcount rose by 11,400 in 2Q 2026, a “seasonally adjusted” rate of 2.9%.")


def ans(status="answered", claims=None, reason="", clar=""):
    return Answer(status=status, summary="s", claims=claims or [], caveats=[], clarification_question=clar, reason=reason)


def claim(text, label="P1", quote="rose by 11,400 in 2Q 2026"):
    return Claim(text=text, citations=[Citation(label=label, quote=quote)])


def test_valid_answer_with_curly_quotes_and_whitespace():
    r = check(ans(claims=[claim("Employment grew by 11,400.", quote='a  "seasonally adjusted" rate of 2.9%')]), [P1])
    assert r.valid and r.cited_passage_ids == ["doc:p1"] and not r.ungrounded_numbers


def test_quote_not_in_passage_is_invalid():
    r = check(ans(claims=[claim("x", quote="rose by 12,400 in 2Q 2026")]), [P1])
    assert any("not verbatim" in e for e in r.errors)


def test_label_not_in_context_is_invalid():
    r = check(ans(claims=[claim("x", label="P9")]), [P1])
    assert any("not in the context" in e for e in r.errors)


def test_status_rules():
    assert not check(ans(status="answered"), [P1]).valid  # no claims
    assert not check(ans(status="abstained"), [P1]).valid  # no reason
    assert check(ans(status="abstained", reason="missing"), [P1]).valid
    assert not check(ans(status="clarify", reason="r"), [P1]).valid  # no question
    assert not check(ans(status="refused", reason="r", claims=[claim("x")]), [P1]).valid


def test_ungrounded_number_is_soft_finding_not_error():
    r = check(ans(claims=[claim("Employment grew by 11,400, up 700 on the advance estimate.")]), [P1])
    assert r.valid and r.ungrounded_numbers == ["claim 1: 700"]


def test_number_helpers_ignore_years_and_small_integers():
    assert numbers("2Q 2026 grew 11,400 or 2.9%") == {"2", "11400", "2.9"}
    assert key_numbers("2Q 2026 grew 11,400 or 2.9% in 3 sectors") == {"11400", "2.9"}
    assert norm("A\u00a0 B") == "a b"
