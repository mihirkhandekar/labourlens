"""Synthetic source fixtures; no publisher prose or PDFs are committed."""
from pathlib import Path

import pymupdf
import pytest

from labourlens.data.pdf_extract import (
    _Block, _clean_controls, _is_heading, _printed_label, extract_pdf, has_controls, looks_garbled, looks_tabular, symbolic_note,
)
from labourlens.data.html_extract import extract_html

COMMON = dict(source_id="synthetic", snapshot_id="fixture", original_url="https://example.org",
              title="Synthetic report", publication_date=None, release_stage="final",
              rights_status="unresolved", commit_text=False)


@pytest.mark.parametrize("control", ["\x00", "\x01", "\x14", "\x7f", "\x85", "\x9f"])
def test_controls_flagged_at_any_length(control):
    assert looks_garbled("short" + control)[0]
    assert looks_garbled(control + "long synthetic prose " * 20)[0]


def test_trailing_control_transformation_is_conservative():
    text, changes = _clean_controls("A synthetic readable sentence ends here.\x01")
    assert not has_controls(text)
    assert changes == ("strip_trailing_u0001",)
    assert _clean_controls("bad\x14text\x01")[1] == ()
    assert _clean_controls("bad\x01")[1] == ()


LEGEND = "Signif. codes: * p<0.10, ** p<0.05, *** p<0.01. Synthetic legend sentence that explains the base category used."
EQUATION = "𝑙𝑛(Z𝑗s) = ∑ θm group𝑗s × period𝑗s + ζ𝑗s = μ × η𝑗s ∑ ρ ∼ N[0, 1] where j is a unit"
COEF_ROW = "lag(synthetic term)\n0.125***\n0.095***\n0.115***\n0.002\n0.009\n0.035\n0.237"


@pytest.mark.parametrize("text", [LEGEND, EQUATION, COEF_ROW])
def test_statistical_symbols_alone_are_not_garbled(text):
    assert not looks_garbled(text)[0]
    if text is COEF_ROW:
        assert looks_tabular(text)
    else:
        assert symbolic_note(text).startswith("symbolic text")


@pytest.mark.parametrize("text", [
    "+RZZRXOG\\RXUDWH WKLV SXEOLFDWLRQ LQ WHUPV RI [ #  @ ~ ` \\ \\ \\ \\ ",
    "Synthetic prose with stray font debris \\ \\ \\ \\ \\ \\ ` ` ` ` ` # # # # inside the block of text.",
    "bad\x01control in a long synthetic legend: *** p<0.01, ** p<0.05, * p<0.1 and more words here",
])
def test_real_garble_is_still_flagged(text):
    assert looks_garbled(text)[0]
    assert not symbolic_note(text)

def test_page_body_font_not_document_table_font(tmp_path):
    doc = pymupdf.open()
    page = doc.new_page()
    for y, text in [(110, "Synthetic prose explains changes across several groups"),
                    (130, "and continues into another short body block."),
                    (150, "A further sentence remains narrative rather than a title.")]:
        page.insert_text((55, y), text, fontsize=11)
    path = tmp_path / "fixture.pdf"
    doc.save(path)
    doc.close()
    passages, _ = extract_pdf(path, **COMMON)
    assert len(passages) == 3
    assert all(not p.section_heading for p in passages)


def test_heading_layout_and_punctuation():
    previous = _Block(1, 0, (50, 80, 500, 100), "previous", 11, False)
    assert _is_heading(_Block(1, 1, (50, 120, 300, 135), "Synthetic findings", 14, True), 11, previous)
    assert not _is_heading(_Block(1, 1, (50, 120, 300, 135), "A sentence ends here.", 14, True), 11, previous)
    assert not _is_heading(_Block(1, 1, (50, 750, 80, 765), "A27", 14, True), 11, previous)


def test_appendix_footer_inside_note(tmp_path):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((55, 710), "Synthetic notes describe survey coverage and limitations.\nA20", fontsize=9)
    path = tmp_path / "footer.pdf"
    doc.save(path)
    doc.close()
    passages, _ = extract_pdf(path, **COMMON)
    assert passages[0].printed_page_label == "A20"
    assert not passages[0].text.endswith("A20")
    assert "remove_printed_page_footer" in passages[0].transformations
    assert passages[0].raw_text_sha256 != passages[0].text_sha256


def test_article_boundary_superscript_rights_and_revisions(tmp_path):
    path = tmp_path / "fixture.html"
    path.write_text('''<body><p>Obsolete browser instructions must never become evidence.</p>
    <nav><p>Navigation categories and miscellaneous links.</p></nav><article>
    <h1>Synthetic publication</h1><h2>Key findings<sup>3</sup></h2>
    <p>This synthetic narrative is deliberately long enough to retain.</p>
    <p>Revised figures replace preliminary figures in this release.</p>
    <p>Copyright restrictions require permission for reproduction.</p>
    </article></body>''')
    passages, stats = extract_html(path, **COMMON)
    assert len(passages) == 2
    assert all(p.section_heading == "Key findings" for p in passages)
    assert any("Revised" in p.text for p in passages)
    assert len(stats["rights_notices"]) == 1
    assert all("browser" not in p.text for p in passages)


def test_duplicate_metadata_preserves_every_target(tmp_path):
    path = tmp_path / "duplicate.html"
    path.write_text('<article><h1>Synthetic findings</h1>' +
                    '<p>Repeated synthetic definitions remain individually citeable.</p>' * 2 + '</article>')
    passages, _ = extract_html(path, **COMMON)
    assert len(passages) == 2
    assert passages[0].passage_id != passages[1].passage_id
    assert passages[0].dup_group == passages[1].dup_group


def test_context_dedupe_does_not_hide_revisions():
    from labourlens.answer.context import build_context
    base = dict(source_id="synthetic", snapshot_id="v1", document_title="Fixture",
                publication_date=None, release_stage="final", locator="item 1",
                text="Identical synthetic definition.")
    passages = {"a": base, "b": {**base, "text": "Identical  synthetic definition."},
                "c": {**base, "snapshot_id": "v2"}}
    ctx = build_context([], passages, first_ids=["a", "b", "c"])
    assert [p.passage_id for p in ctx] == ["a", "c"]
    assert len(passages) == 3


def test_adjacent_note_fragments_keep_geometry_and_links(tmp_path):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((55, 510), "(2) Synthetic notes describe a changing sample population", fontsize=8)
    page.insert_text((55, 530), "and continue across independently extracted source blocks.", fontsize=8)
    path = tmp_path / "notes.pdf"
    doc.save(path)
    doc.close()
    passages, _ = extract_pdf(path, **COMMON)
    assert len(passages) == 2
    assert all(p.context_required and set(p.source_block_indices) == {0, 1} for p in passages)
    assert all(p.bbox is not None for p in passages)


@pytest.mark.corpus
def test_real_corpus_extraction_regressions():
    from labourlens import paths
    import json
    if not (paths.PASSAGES / "mom-2025-q3-final.jsonl").exists():
        pytest.skip("Local corpus required")
    def load(sid):
        return [json.loads(line) for line in (paths.PASSAGES / f"{sid}.jsonl").read_text().splitlines()]
    p30 = [p for p in load("mom-2025-q3-final") if p["page_number"] == 30]
    assert len(p30) >= 5
    assert sum(len(p["text"]) for p in p30) >= 500
    from labourlens.data import raw_store
    from labourlens.data.pdf_extract import _page_blocks
    manifest = raw_store.load_manifest()
    with pymupdf.open(paths.ROOT / manifest["mom-2025-q3-final"].raw_path) as doc:
        narrative = [b.text for b in _page_blocks(doc[29], 30) if 10.9 < b.max_size < 11.1]
    assert len(narrative) == 7
    assert all(text in {p["text"] for p in p30} for text in narrative)
    q1 = [p for p in load("mom-2026-q1-final") if p["page_number"] == 56]
    assert q1 and all(p["printed_page_label"] == "A28" for p in q1)
    assert all(p["section_heading"] != "A27" for p in q1)
    q2 = load("mom-2026-q2-final")
    footer = next(p for p in q2 if p["page_number"] == 48 and p["block_index"] == 49)
    assert footer["printed_page_label"] == "A20"
    assert not footer["text"].endswith("A20")
    fragment = next(p for p in q2 if p["page_number"] == 22 and p["block_index"] == 20)
    assert fragment["context_required"] and {19, 20, 21} <= set(fragment["source_block_indices"])
    for path in paths.PASSAGES.glob("*.jsonl"):
        for p in map(json.loads, path.read_text().splitlines()):
            assert p["quality_flag"] != "ok" or not has_controls(p["text"])
    advance = load("mom-2025-q3-advance")
    assert any(p["section_heading"] == "Main Findings" for p in advance)
    assert not any(p["section_heading"] == "Main Findings 3" for p in advance)
