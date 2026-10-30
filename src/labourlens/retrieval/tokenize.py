"""Tokenisation for BM25. Every switch is a measured experiment factor (D-016), not a default belief.

Why custom: generic tokenisers split '2.9' and '11,400' and ignore that '2Q 2026', 'Q2 2026' and 'second
quarter of 2026' name the same period. A keyword retriever that cannot match period phrases fails on
exactly the questions this project asks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import Stemmer
from bm25s.stopwords import STOPWORDS_EN

_STEM = Stemmer.Stemmer("english")
_ORD = {"first": "1", "second": "2", "third": "3", "fourth": "4", "1st": "1", "2nd": "2", "3rd": "3", "4th": "4"}
_TOKEN = re.compile(r"\d+(?:\.\d+)?[a-z]*|[a-z]+\d*(?:[-'][a-z]+)*")
_NUM_COMMA = re.compile(r"(?<=\d),(?=\d{3}\b)")


@dataclass(frozen=True)
class TokConfig:
    stem: bool = False
    stopwords: bool = True
    period_normalise: bool = True

    def key(self) -> str:
        return f"stem{int(self.stem)}-stop{int(self.stopwords)}-per{int(self.period_normalise)}"


def _periods(text: str) -> str:
    # 'second quarter' / '2nd quarter' / 'quarter 2' / '2q' / 'q2' -> 'q2' (year tokens are left alone)
    t = re.sub(r"\b(first|second|third|fourth|1st|2nd|3rd|4th)[- ]quarter\b", lambda m: f" q{_ORD[m.group(1)]} ", text)
    t = re.sub(r"\bquarter ([1-4])\b", r" q\1 ", t)
    t = re.sub(r"\b([1-4])q\b", r" q\1 ", t)
    return t


def tokenize(text: str, cfg: TokConfig = TokConfig()) -> list[str]:
    t = _NUM_COMMA.sub("", text.lower().replace("\u00a0", " "))
    if cfg.period_normalise:
        t = _periods(t)
    toks = _TOKEN.findall(t)
    if cfg.stopwords:
        toks = [w for w in toks if w not in STOPWORDS_EN]
    if cfg.stem:
        toks = [w if w[0].isdigit() else _STEM.stemWord(w) for w in toks]
    return toks
