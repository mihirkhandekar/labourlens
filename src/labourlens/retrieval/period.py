"""Query metadata awareness (experiment R1, D-029): parse the period and release type a question names and map them to
catalogue documents. Deterministic, no model.

Rules (fixed before measurement; see docs/experiments/m6-retrieval-improvements.md):
  Period hint   an explicit quarter with a year: `1Q 2026`, `Q1 2026`, `2026 Q1`, `first quarter of 2026`, or a month
                with a year (`September 2025` -> 3Q 2025) unless the month follows publish/release/issued/dated words
                (then it names a publication date, not a reference period). `X to Y` / `X through Y` / `X - Y` between
                two period hints expands to every quarter between them. A bare `Q2`, a bare month or a bare year gives
                no hint. All quarters named are kept (a union), so a comparison across quarters keeps every named quarter.
  Stage hint    advance / preliminary -> `advance`; final / full report / labour market report -> `final`. If both
                families appear (e.g. a question comparing the advance release with the final one) the hint is
                CONFLICTING and no stage restriction is derived.
  Matching      a document matches the period hint when its coverage interval overlaps a named quarter, and the stage
                hint when its release_stage equals the hinted stage. Documents are the catalogue (specs/sources.yaml and specs/sources.d/*.yaml).
  Hard filter   candidates are restricted to documents matching every available hint; if no document matches, no filter.
  Soft boost    each available hint adds a bonus to chunks of documents that match that hint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from functools import cache

from labourlens.data import catalog as source_catalog

_ORD = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}
_MONTHS = {m: i for i, names in enumerate(
    [("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"), ("may",), ("jun", "june"), ("jul", "july"),
     ("aug", "august"), ("sep", "sept", "september"), ("oct", "october"), ("nov", "november"), ("dec", "december")], 1) for m in names}

_YEAR = r"(?:20\d\d|'\d\d)"
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(rf"\b([1-4])\s?Q\s?(?:of\s+)?({_YEAR})(?!\d)", re.I), "qy"),  # 1Q 2026, 1Q2026, 1Q'26
    (re.compile(rf"\bQ\s?([1-4])[\s,/-]*(?:of\s+)?({_YEAR})(?!\d)", re.I), "qy"),  # Q1 2026, Q1-2026, Q1'26
    (re.compile(r"\b(20\d\d)[\s-]*Q\s?([1-4])\b", re.I), "yq"),  # 2026-Q1, 2026 Q1
    (re.compile(rf"\b({'|'.join(_ORD)})\s+quarter(?:\s+of)?\s+(?:the\s+year\s+)?(20\d\d)\b", re.I), "ordy"),  # first quarter of 2026
    (re.compile(rf"\b({'|'.join(sorted(_MONTHS, key=len, reverse=True))})\.?\s*,?\s+(20\d\d)\b", re.I), "month"),  # September 2025
]
_PUBLICATION_WORDS = re.compile(r"(publish|releas|issue|dated)\w*\W+(?:\w+\W+){0,2}$", re.I)
_RANGE = re.compile(r"^\s*(?:to|through|until|till|-|–|—)\s*$", re.I)
_ADVANCE = re.compile(r"\b(advance|preliminary)\b", re.I)
_FINAL = re.compile(r"\b(final|full\s+report|labou?r\s+market\s+report)\b", re.I)
MAX_RANGE_QUARTERS = 12


@dataclass(frozen=True)
class Hints:
    quarters: frozenset[tuple[int, int]] = frozenset()  # (year, quarter)
    stage: str | None = None  # 'advance' | 'final' | None
    stage_conflict: bool = False

    def any(self) -> bool:
        return bool(self.quarters) or self.stage is not None


def _year(s: str) -> int:
    return 2000 + int(s[1:]) if s.startswith("'") else int(s)


def _qidx(y: int, q: int) -> int:
    return y * 4 + (q - 1)


def _from_idx(i: int) -> tuple[int, int]:
    return i // 4, i % 4 + 1


def parse(question: str) -> Hints:
    found: list[tuple[int, int, tuple[int, int]]] = []  # (start, end, (year, quarter))
    taken: list[tuple[int, int]] = []
    for pat, kind in _PATTERNS:
        for m in pat.finditer(question):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            if kind == "qy":
                yq = (_year(m.group(2)), int(m.group(1)))
            elif kind == "yq":
                yq = (int(m.group(1)), int(m.group(2)))
            elif kind == "ordy":
                yq = (int(m.group(2)), _ORD[m.group(1).lower()])
            else:
                if _PUBLICATION_WORDS.search(question[:m.start()]):
                    continue
                yq = (int(m.group(2)), (_MONTHS[m.group(1).lower()] - 1) // 3 + 1)
            taken.append((m.start(), m.end()))
            found.append((m.start(), m.end(), yq))
    found.sort()
    quarters: set[tuple[int, int]] = {yq for _, _, yq in found}
    for (_, e1, a), (s2, _, b) in zip(found, found[1:]):  # `X to Y` between two period hints
        if _RANGE.match(question[e1:s2]):
            lo, hi = sorted((_qidx(*a), _qidx(*b)))
            if hi - lo + 1 <= MAX_RANGE_QUARTERS:
                quarters |= {_from_idx(i) for i in range(lo, hi + 1)}
    adv, fin = bool(_ADVANCE.search(question)), bool(_FINAL.search(question))
    stage = "advance" if adv and not fin else "final" if fin and not adv else None
    return Hints(frozenset(quarters), stage, adv and fin)


@dataclass(frozen=True)
class Doc:
    source_id: str
    stage: str
    start: date
    end: date


@cache
def catalogue() -> tuple[Doc, ...]:
    return tuple(Doc(d["source_id"], d["release_stage"], date.fromisoformat(d["period_start"]), date.fromisoformat(d["period_end"]))
                 for d in source_catalog.documents())


def _quarter_span(y: int, q: int) -> tuple[date, date]:
    m = 3 * (q - 1) + 1
    end = date(y, m + 2, 30 if m + 2 in (6, 9) else 31)
    return date(y, m, 1), end


def period_match(doc: Doc, hints: Hints) -> bool | None:
    """None when the question names no period."""
    if not hints.quarters:
        return None
    return any(doc.start <= e and s <= doc.end for s, e in (_quarter_span(y, q) for y, q in hints.quarters))


def stage_match(doc: Doc, hints: Hints) -> bool | None:
    return None if hints.stage is None else doc.stage == hints.stage


def matching_sources(hints: Hints, docs: tuple[Doc, ...] | None = None) -> frozenset[str] | None:
    """Source ids matching every available hint, or None (no filter) when there is no hint or no document matches."""
    if not hints.any():
        return None
    out = frozenset(d.source_id for d in (docs or catalogue()) if period_match(d, hints) is not False and stage_match(d, hints) is not False)
    return out or None
