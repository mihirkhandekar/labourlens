"""Rights scan checker, exercised on synthetic passages only."""
import json

from labourlens.data import rights_scan as rs

PASSAGE = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"


def _passages(tmp_path):
    d = tmp_path / "passages"
    d.mkdir()
    (d / "x.jsonl").write_text(json.dumps({"text": PASSAGE}) + "\n")
    return d


def test_six_word_quote_passes_seven_fails(tmp_path):
    sh = rs.build_shingles(_passages(tmp_path))
    assert rs.scan_text("see alpha bravo charlie delta echo foxtrot [...]", sh) == []
    assert rs.scan_text("x\nAlpha, bravo charlie delta echo foxtrot golf!", sh) == [(2, 7)]


def test_longest_run_and_cross_line(tmp_path):
    sh = rs.build_shingles(_passages(tmp_path))
    runs = rs.scan_text("alpha bravo charlie delta\necho foxtrot golf hotel india", sh)
    assert runs == [(1, 9)]


def test_run_reports_hits_and_exit_code(tmp_path, capsys):
    d = _passages(tmp_path)
    (tmp_path / "a.md").write_text("ok\n" + PASSAGE + "\n")
    (tmp_path / "b.md").write_text("clean text only\n")
    assert rs.run(d, tmp_path, ["a.md", "b.md"]) == 1
    out = capsys.readouterr().out
    assert "a.md:2:" in out and "b.md" not in out and "juliet" not in out


def test_allowlist_and_missing_passages(tmp_path, capsys):
    d = _passages(tmp_path)
    (tmp_path / "a.md").write_text(PASSAGE)
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "rights-scan-allowlist.txt").write_text("a.md | legal notice\n")
    assert rs.run(d, tmp_path, ["a.md"]) == 0
    assert rs.run(tmp_path / "nope", tmp_path, ["a.md"]) == 0
    assert "NOT CHECKED" in capsys.readouterr().out
    assert rs.run(tmp_path / "nope", tmp_path, ["a.md"], require_corpus=True) == 2


def test_allowlist_requires_reason(tmp_path):
    f = tmp_path / "al.txt"
    f.write_text("a.md\n")
    try:
        rs.load_allowlist(f)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
