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
_PAGE_LABEL = re.compile(r"(?:\d{1,3}|A\d{1,3}|[ivxlc]{1,6})", re.I)


def has_controls(text: str) -> bool:
    return any((ord(c) < 32 and c not in "\n\r\t") or 127 <= ord(c) <= 159 for c in text)


def _clean_controls(text: str) -> tuple[str, tuple[str, ...]]:
    # A single trailing glyph is removable only when the remaining prose is legible.
    if text.endswith("\x01") and not has_controls(text[:-1]):
        rest = text[:-1].rstrip()
        if len(rest.split()) >= 4 and not looks_garbled(rest)[0]:
            return rest, ("strip_trailing_u0001",)
    return text, ()


@dataclass
class _Block:
    page: int
    index: int
    bbox: tuple[float, float, float, float]
    text: str
    max_size: float
    bold: bool


_PROSE_PUNCT = ".,;:%()'\"/&-+$–—’‘“”•·°@?!"
_STAT_ASCII = set("*<>=^_[]{}|~")


def _is_statistical_symbol(c: str) -> bool:
    """Characters that legitimately dominate significance legends and estimating equations.

    ASCII relation/footnote marks, Greek letters, mathematical operators (U+2200-22FF, includes the minus sign and summation)
    and mathematical alphanumerics (U+1D400-1D7FF, the italic letters of typeset equations).
    """
    o = ord(c)
    return c in _STAT_ASCII or c in "×±÷∼≈≠≤≥" or 0x0370 <= o <= 0x03FF or 0x2200 <= o <= 0x22FF or 0x1D400 <= o <= 0x1D7FF


def _symbol_counts(t: str) -> tuple[int, int]:
    """(all characters outside prose punctuation, the subset that is not a statistical symbol)."""
    weird = [c for c in t if not (c.isalnum() or c.isspace() or c in _PROSE_PUNCT)]
    return len(weird), sum(1 for c in weird if not _is_statistical_symbol(c))


def looks_garbled(text: str) -> tuple[bool, str]:
    """Heuristic for font-encoding garbage such as '+RZZRXOG\\RXUDWH' (seen on report pages that use
    an unmapped font, for example the reader-feedback form on the last page of the 2Q 2026 report).

    Three independent signals; any one flags the block:
      1. high share of characters outside normal prose punctuation, NOT counting statistical symbols
         (`*`, `<`, `=`, Greek letters, math operators and italics); a legend such as 'p<0.01' or an estimating
         equation is legible text, see `symbolic_note`
      2. many very long letter-only tokens (words run together by a broken font map)
      3. many tokens that mix lower->upper case inside a word
    A low rate of English function words is deliberately NOT used: legitimate abbreviation lists and
    glossaries have none and would be flagged falsely.
    """
    t = text.strip()
    if has_controls(text):
        return True, "C0/C1 control characters; wording not decoded"
    if len(t) < 60:
        return False, ""
    _, unexplained = _symbol_counts(t)
    if unexplained / len(t) > 0.04:
        return True, f"symbol_ratio={unexplained / len(t):.3f}"
    tokens = re.findall(r"[A-Za-z][A-Za-z'\-]*", t)
    if len(tokens) >= 8:
        long_rate = sum(1 for w in tokens if len(w) > 16 and w.isalpha()) / len(tokens)
        mixed = sum(1 for w in tokens if len(w) > 3 and re.search(r"[a-z][A-Z]", w)) / len(tokens)
        if long_rate > 0.2 or mixed > 0.25:
            return True, f"long_token_rate={long_rate:.3f};mixed_case_rate={mixed:.3f}"
    return False, ""


def symbolic_note(text: str) -> str:
    """Non-empty when the block is legible but symbol-dense only because of statistical symbols (legend or equation)."""
    t = text.strip()
    if len(t) < 60 or has_controls(text):
        return ""
    weird, unexplained = _symbol_counts(t)
    if weird / len(t) > 0.04 and unexplained / len(t) <= 0.04:
        return f"symbolic text (statistical legend or equation); symbol_ratio={weird / len(t):.3f}"
    return ""


def looks_tabular(text: str) -> bool:
    toks = text.split()
    if len(toks) < 6:
        return False
    num = sum(1 for w in toks if re.fullmatch(r"[+\-–]?[\d,]+(\.\d+)?%?\**", w))  # trailing * = significance stars
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
            lt = "".join(s["text"] for s in spans).strip(" \t\r\n")
            if lt:
                lines.append(lt)
            for s in spans:
                if s["text"].strip(" \t\r\n"):
                    sizes.append(s["size"])
                    if s["flags"] & 16 or "bold" in s["font"].lower():
                        bold = True
        text = re.sub(r"[ \t]+", " ", "\n".join(lines)).strip(" \t\r\n")
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
    for b in reversed(blocks):
        last = b.text.splitlines()[-1].strip()
        appendix = re.fullmatch(r"A\d{1,3}", last, re.I)
        if appendix and b.bbox[3] > page.rect.height * 0.86:
            return last
        if b.bbox[1] > page.rect.height * 0.90 and len(b.text) <= 6 and _PAGE_LABEL.fullmatch(last):
            return last
    return None


def _is_heading(b: _Block, body: float, previous: _Block | None) -> bool:
    text = b.text.strip()
    semantic = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", text)
    if (len(text) >= 120 or "\n" in text or _PAGE_LABEL.fullmatch(text)
            or re.search(r"[.!?;,:]", semantic) or has_controls(text) or looks_tabular(text)):
        return False
    gap = b.bbox[1] - previous.bbox[3] if previous else b.bbox[1]
    # Body-sized bold labels need separation; large titles must actually exceed the page body.
    return (b.max_size >= body * 1.15 and (gap >= 4 or b.bbox[1] < 100)
            or b.bold and b.max_size >= body and gap >= 4)


def extract_pdf(path: Path, *, source_id: str, snapshot_id: str, original_url: str, title: str,
                publication_date: str | None, release_stage: str, rights_status: str,
                commit_text: bool) -> tuple[list[DocumentPassage], dict]:
    doc = pymupdf.open(path)
    all_blocks: list[tuple[_Block, str | None, float, _Block | None, list[_Block]]] = []
    for pno, page in enumerate(doc, start=1):
        blocks = _page_blocks(page, pno)
        label = _printed_label(page, blocks)
        prose = [b for b in blocks if len(b.text) >= 40 and not looks_tabular(b.text)]
        sizes = [b.max_size for b in prose for _ in range(max(1, len(b.text) // 40))]
        body = statistics.median(sizes) if sizes else 10.0
        previous = None
        for b in blocks:
            all_blocks.append((b, label, body, previous, blocks))
            previous = b

    passages: list[DocumentPassage] = []
    heading = ""
    dropped_short = 0
    flags = {"ok": 0, "garbled": 0, "table_unreliable": 0, "multicolumn_uncertain": 0, "empty": 0}
    for b, label, body, previous, page_blocks in all_blocks:
        raw_hash = sha256_hex(b.text.encode())
        text, transformations = _clean_controls(b.text)
        if label and text.splitlines()[-1].strip() == label:
            text = "\n".join(text.splitlines()[:-1]).rstrip()
            transformations += ("remove_printed_page_footer",)
        if not text:
            continue
        candidate = _Block(b.page, b.index, b.bbox, text, b.max_size, b.bold)
        if _is_heading(candidate, body, previous):
            heading = re.sub(r"\s+", " ", text).strip()
            continue
        if len(text) < MIN_PASSAGE_CHARS and not has_controls(text):
            dropped_short += 1
            continue
        garbled, why = looks_garbled(text)
        flag, note = "ok", ""
        if garbled:
            flag, note = "garbled", why
        elif looks_tabular(text):
            flag, note = "table_unreliable", "numeric-dense block; do not use for numerical answers"
        else:
            note = symbolic_note(text)
        # Adjacent small-font note blocks can start/end inside a numbered note. Preserve
        # the original target and geometry, explicitly require its linked neighbours.
        neighbours = [x.index for x in page_blocks if x.index != b.index
                      and abs(x.index - b.index) == 1 and abs(x.max_size - b.max_size) < 0.2
                      and min(abs(x.bbox[1] - b.bbox[3]), abs(b.bbox[1] - x.bbox[3])) < 12]
        fragment = bool(neighbours and b.max_size <= 9 and not looks_tabular(text)
                        and (re.search(r"\(\d+\)", text) or not text[0].isupper()))
        if fragment:
            note = (note + "; " if note else "") + "note fragment; requires adjacent source blocks"
        flags[flag] += 1
        text_hash = sha256_hex(text.encode())
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
                text=text,
                text_sha256=text_hash,
                extraction_method=EXTRACTION_METHOD,
                quality_flag=flag,  # type: ignore[arg-type]
                quality_note=note,
                raw_text_sha256=raw_hash,
                transformations=transformations,
                source_block_indices=(b.index, *neighbours) if fragment else (b.index,),
                context_required=fragment,
                dup_group=sha256_hex(" ".join(text.split()).encode()),
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
