"""Deterministic answer checks (D-024). Hard errors make an answer invalid; soft findings are reported."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer

MAX_QUOTE_WORDS = 40
_NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+")
_YEAR = re.compile(r"^(?:19|20)\d\d$")


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = t.translate({0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0x2013: "-", 0x2014: "-", 0x00A0: " "})
    return re.sub(r"\s+", " ", t).strip().casefold()


def numbers(text: str) -> set[str]:
    """Numeric tokens with thousands separators removed. Years are dropped; they are not figures."""
    out = set()
    for m in _NUM.findall(text):
        v = m.replace(",", "")
        if not _YEAR.match(v):
            out.add(v)
    return out


def key_numbers(text: str) -> set[str]:
    """Figures worth requiring in an answer: decimals, comma-grouped numbers, or integers of 100 or more (not years)."""
    return {n for n in numbers(text) if "." in n or (n.isdigit() and int(n) >= 100)}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    ungrounded_numbers: list[str] = field(default_factory=list)
    cited_passage_ids: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def check(answer: Answer, ctx: list[ContextPassage]) -> Report:
    by_label = {p.label: p for p in ctx}
    rep = Report()
    cited: list[str] = []
    if answer.status == "answered":
        if not answer.claims:
            rep.errors.append("status is answered but there are no claims")
        if not answer.summary.strip():
            rep.errors.append("status is answered but the summary is empty")
    else:
        if answer.claims:
            rep.errors.append(f"status is {answer.status} but claims were given")
        if not answer.reason.strip():
            rep.errors.append(f"status is {answer.status} but no reason was given")
    if answer.status == "clarify" and not answer.clarification_question.strip():
        rep.errors.append("status is clarify but no clarification question was given")
    for i, c in enumerate(answer.claims):
        if not c.citations:
            rep.errors.append(f"claim {i + 1} has no citation")
        support = []
        for cit in c.citations:
            p = by_label.get(cit.label)
            if p is None:
                rep.errors.append(f"claim {i + 1} cites {cit.label!r}, which was not in the context")
                continue
            if len(cit.quote.split()) > MAX_QUOTE_WORDS:
                rep.errors.append(f"claim {i + 1} quote from {cit.label} is longer than {MAX_QUOTE_WORDS} words")
            if not cit.quote.strip() or norm(cit.quote) not in norm(p.text):
                rep.errors.append(f"claim {i + 1} quote is not verbatim in {cit.label}")
            else:
                cited.append(p.passage_id)
                support.append(norm(p.text))
        bad = sorted(n for n in numbers(c.text) if not any(n in numbers(s) for s in support))
        rep.ungrounded_numbers += [f"claim {i + 1}: {n}" for n in bad]
    rep.cited_passage_ids = list(dict.fromkeys(cited))
    return rep
