"""Rights scan: find verbatim runs of MOM/MTI passage text in git-tracked files (D-001/D-004).

A hit is a run of at least ``SHINGLE`` consecutive normalised words (lower-cased
alphanumerics; URLs ignored; windows of mostly bare numbers ignored) that also occurs consecutively in any passage under data/passages.
The policy allows quotes of at most six consecutive words, so a seven-word match is a violation.
Reports only locations and run lengths, never the matched text.
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from labourlens import paths

SHINGLE = 7
ALLOWLIST = paths.SPECS / "rights-scan-allowlist.txt"
MAX_BYTES = 5_000_000
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2", ".parquet", ".duckdb", ".zip", ".gz", ".lock"}
_WORD = re.compile(r"[a-z0-9]+")
_URL = re.compile(r"https?://\S+")
MIN_ALPHA = 4  # a window needs this many words containing a letter; pure number runs are data, not prose


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    run_words: int


def words(text: str) -> list[str]:
    return _WORD.findall(_URL.sub(" ", text).lower())


def _passage_texts(passages_dir: Path):
    for f in sorted(passages_dir.glob("*.jsonl")):
        with f.open(encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if raw:
                    yield json.loads(raw).get("text") or ""


def build_shingles(passages_dir: Path, n: int = SHINGLE) -> set[int]:
    out: set[int] = set()
    for text in _passage_texts(passages_dir):
        w = words(text)
        for i in range(len(w) - n + 1):
            out.add(hash(tuple(w[i : i + n])))
    return out


def load_allowlist(path: Path = ALLOWLIST) -> list[tuple[str, str]]:
    """Lines: ``<glob> | <reason>``; blank lines and ``#`` comments ignored. Reason is mandatory."""
    if not path.exists():
        return []
    entries = []
    for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        glob, sep, reason = (x.strip() for x in s.partition("|"))
        if not sep or not reason:
            raise ValueError(f"{path.name}:{ln}: allowlist entry needs '<glob> | <reason>'")
        entries.append((glob, reason))
    return entries


def scan_text(text: str, shingles: set[int], n: int = SHINGLE) -> list[tuple[int, int]]:
    """Return (first_line, run_words) for every maximal matching run in ``text``."""
    toks: list[tuple[str, int]] = []
    for ln, line in enumerate(text.splitlines(), 1):
        toks.extend((w, ln) for w in words(line))
    covered = [False] * len(toks)
    for i in range(len(toks) - n + 1):
        win = tuple(t for t, _ in toks[i : i + n])
        if sum(not t.isdigit() for t in win) >= MIN_ALPHA and hash(win) in shingles:
            for j in range(i, i + n):
                covered[j] = True
    runs, i = [], 0
    while i < len(toks):
        if covered[i]:
            j = i
            while j < len(toks) and covered[j]:
                j += 1
            runs.append((toks[i][1], j - i))
            i = j
        else:
            i += 1
    return runs


def tracked_files(root: Path = paths.ROOT) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def scan(files: list[str], shingles: set[int], root: Path = paths.ROOT, allow: list[tuple[str, str]] | None = None) -> list[Hit]:
    allow = allow or []
    hits: list[Hit] = []
    for rel in files:
        fp = root / rel
        if fp.suffix.lower() in SKIP_SUFFIXES or not fp.is_file() or fp.stat().st_size > MAX_BYTES:
            continue
        if any(fnmatch.fnmatch(rel, g) for g, _ in allow):
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits.extend(Hit(rel, ln, n) for ln, n in scan_text(text, shingles))
    return hits


def run(passages_dir: Path | None = None, root: Path | None = None, files: list[str] | None = None) -> int:
    passages_dir = passages_dir or paths.PASSAGES
    root = root or paths.ROOT
    if not passages_dir.exists() or not any(passages_dir.glob("*.jsonl")):
        print(f"rights-scan: {passages_dir} absent; skipped (nothing to compare against)")
        return 0
    shingles = build_shingles(passages_dir)
    allow = load_allowlist() if root == paths.ROOT else load_allowlist(root / "specs" / "rights-scan-allowlist.txt")
    hits = scan(files if files is not None else tracked_files(root), shingles, root, allow)
    for h in sorted(hits, key=lambda h: (h.path, h.line)):
        print(f"{h.path}:{h.line}: verbatim run of {h.run_words} words (limit {SHINGLE - 1})")
    by_file = len({h.path for h in hits})
    print(f"rights-scan: {len(hits)} hit(s) in {by_file} file(s); allowlisted globs: {len(allow)}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(run())
