"""Block- and position-aware PDF passage extraction with explicit quality flags (PyMuPDF).

Why not plain page text: page.get_text() makes no reading-order guarantee, and the MOM reports mix
multi-column prose, infographic number panels, tables and footnotes. We read text blocks with their
bounding boxes, order them per page (column-aware), track section headings by font size/weight, and
flag - never silently repair - blocks that look garbled or like tables.

Numeric truth never comes from this module. Table-like and garbled blocks are kept (so reviewers can
see them) but flagged, and downstream retrieval must treat them as unsuitable for numerical answers.
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from labourlens.models import DocumentPassage, PARSER_VERSION, sha256_hex

MIN_PASSAGE_CHARS = 40
EXTRACTION_METHOD = "pymupdf-blocks-column-aware"

_STOP = set(
    "the of and to in a is for on that with as by at from was were be are this it an or which has have had "
    "not but their its also more than into over during per about between while compared up down rate "
    "employment total quarter increase decrease rose fell grew labour market".split()
)
_ROMAN = re.compile(r"^(?=[ivxlc]+$)[ivxlc]{1,6}$", re.I)


@dataclass
class _Block:
    page: int
    index: int
    bbox: tuple[float, float, float, float]
    text: str
    max_size: float
    bold: bool


def looks_garbled(text: str) -> tuple[bool, str]:
    """Heuristic for font-encoding garbage such as '+RZZRXOG\\RXUDWH' (seen on report pages that use
    an unmapped font, for example the reader-feedback form on the last page of the 2Q 2026 report).

    Three independent signals; any one flags the block:
      1. high share of characters outside normal prose punctuation
      2. many very long letter-only tokens (words run together by a broken font map)
      3. many tokens that mix lower->upper case inside a word
    A low rate of English function words is deliberately NOT used: legitimate abbreviation lists and
    glossaries have none and would be flagged falsely.
    """
    t = text.strip()
    if len(t) < 60:
        return False, ""
    weird = sum(1 for c in t if not (c.isalnum() or c.isspace() or c in ".,;:%()'\"/&-+$–—’‘“”•·°@?!"))
    if weird / len(t) > 0.04:
        return True, f"symbol_ratio={weird / len(t):.3f}"
    tokens = re.findall(r"[A-Za-z][A-Za-z'\-]*", t)
    if len(tokens) >= 8:
        long_rate = sum(1 for w in tokens if len(w) > 16 and w.isalpha()) / len(tokens)
        mixed = sum(1 for w in tokens if len(w) > 3 and re.search(r"[a-z][A-Z]", w)) / len(tokens)
        if long_rate > 0.2 or mixed > 0.25:
            return True, f"long_token_rate={long_rate:.3f};mixed_case_rate={mixed:.3f}"
    return False, ""


def looks_tabular(text: str) -> bool:
    toks = text.split()
    if len(toks) < 6:
        return False
    num = sum(1 for w in toks if re.fullmatch(r"[+\-–]?[\d,]+(\.\d+)?%?", w))
    return num / len(toks) > 0.45


def _page_blocks(page: pymupdf.Page, page_no: int) -> list[_Block]:
    d = page.get_text("dict")
    blocks: list[_Block] = []
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        lines: list[str] = []
        sizes: list[float] = []
        bold = False
        for ln in b["lines"]:
            spans = ln["spans"]
            lt = "".join(s["text"] for s in spans).strip()
            if lt:
                lines.append(lt)
            for s in spans:
                if s["text"].strip():
                    sizes.append(s["size"])
                    if s["flags"] & 16 or "bold" in s["font"].lower():
                        bold = True
        text = re.sub(r"[ \t]+", " ", "\n".join(lines)).strip()
        if not text:
            continue
        blocks.append(_Block(page_no, 0, tuple(round(v, 1) for v in b["bbox"]), text, max(sizes or [0]), bold))
    return _reading_order(blocks, page.rect.width)


def _reading_order(blocks: list[_Block], width: float) -> list[_Block]:
    """Column-aware order: if the page has a clear left and right column of narrow blocks, read left
    column top-to-bottom then right column; otherwise top-to-bottom, left-to-right."""
    mid = width / 2
    narrow = [b for b in blocks if (b.bbox[2] - b.bbox[0]) < width * 0.55]
    left = [b for b in narrow if b.bbox[2] <= mid + 8]
    right = [b for b in narrow if b.bbox[0] >= mid - 8]
    two_col = len(left) >= 3 and len(right) >= 3 and (len(left) + len(right)) >= 0.6 * len(blocks)
    if two_col:
        spanning = [b for b in blocks if b not in left and b not in right]
        top_span = sorted([b for b in spanning if b.bbox[1] < min(x.bbox[1] for x in left + right)], key=lambda b: b.bbox[1])
        rest_span = sorted([b for b in spanning if b not in top_span], key=lambda b: b.bbox[1])
        ordered = top_span + sorted(left, key=lambda b: b.bbox[1]) + sorted(right, key=lambda b: b.bbox[1]) + rest_span
    else:
        ordered = sorted(blocks, key=lambda b: (round(b.bbox[1] / 6), b.bbox[0]))
    for i, b in enumerate(ordered):
        b.index = i
    return ordered


def _printed_label(page: pymupdf.Page, blocks: list[_Block]) -> str | None:
    h = page.rect.height
    for b in reversed(blocks):
        if b.bbox[1] > h * 0.90 and len(b.text) <= 6:
            t = b.text.strip()
            if re.fullmatch(r"\d{1,3}", t) or _ROMAN.match(t):
                return t
    return None


def extract_pdf(path: Path, *, source_id: str, snapshot_id: str, original_url: str, title: str,
                publication_date: str | None, release_stage: str, rights_status: str,
                commit_text: bool) -> tuple[list[DocumentPassage], dict]:
    doc = pymupdf.open(path)
    all_blocks: list[tuple[_Block, str | None]] = []
    for pno, page in enumerate(doc, start=1):
        blocks = _page_blocks(page, pno)
        label = _printed_label(page, blocks)
        for b in blocks:
            all_blocks.append((b, label))
    sizes = [b.max_size for b, _ in all_blocks if len(b.text) > 120]
    body = statistics.median(sizes) if sizes else 10.0

    passages: list[DocumentPassage] = []
    heading = ""
    dropped_short = 0
    flags = {"ok": 0, "garbled": 0, "table_unreliable": 0, "multicolumn_uncertain": 0, "empty": 0}
    for b, label in all_blocks:
        is_heading = len(b.text) < 120 and "\n" not in b.text.strip() and (b.max_size >= body * 1.15 or (b.bold and b.max_size >= body))
        if is_heading and not looks_tabular(b.text):
            heading = re.sub(r"\s+", " ", b.text).strip()
            continue
        if len(b.text) < MIN_PASSAGE_CHARS:
            dropped_short += 1
            continue
        garbled, why = looks_garbled(b.text)
        flag, note = "ok", ""
        if garbled:
            flag, note = "garbled", why
        elif looks_tabular(b.text):
            flag, note = "table_unreliable", "numeric-dense block; do not use for numerical answers"
        flags[flag] += 1
        text_hash = sha256_hex(b.text.encode())
        pid = f"{source_id}:p{b.page:03d}:b{b.index:03d}:{text_hash[:8]}"
        passages.append(
            DocumentPassage(
                passage_id=pid,
                source_id=source_id,
                snapshot_id=snapshot_id,
                original_url=original_url,
                document_title=title,
                publication_date=publication_date,
                release_stage=release_stage,  # type: ignore[arg-type]
                page_number=b.page,
                printed_page_label=label,
                section_heading=heading,
                block_index=b.index,
                bbox=b.bbox,
                text=b.text,
                text_sha256=text_hash,
                extraction_method=EXTRACTION_METHOD,
                quality_flag=flag,  # type: ignore[arg-type]
                quality_note=note,
                locator=f"p.{b.page}" + (f" (printed {label})" if label else ""),
                parser_version=PARSER_VERSION,
                rights_status=rights_status,  # type: ignore[arg-type]
                commit_text=commit_text,
            )
        )
    stats = {
        "source_id": source_id,
        "pages": doc.page_count,
        "passages": len(passages),
        "flags": flags,
        "dropped_short_blocks": dropped_short,
        "body_font_size_median": round(body, 2),
    }
    doc.close()
    return passages, stats


def write_passages(passages: list[DocumentPassage], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for p in passages:
            f.write(json.dumps(p.model_dump(mode="json"), ensure_ascii=False) + "\n")
