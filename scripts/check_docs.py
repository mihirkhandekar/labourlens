"""Check relative links and heading anchors in the tracked Markdown files. Offline; external URLs are not fetched.

Exit status 1 and a list of problems if a relative link points to a missing path or a '#anchor' matches no heading.
Anchors use GitHub's slug rule: lower case, punctuation dropped, spaces to hyphens.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)


def slug(heading: str) -> str:
    text = re.sub(r"[`*_]|<[^>]+>", "", heading).strip().lower()
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    body = FENCE.sub("", path.read_text(encoding="utf-8", errors="ignore"))
    seen: dict[str, int] = {}
    out = set()
    for line in body.splitlines():
        m = re.match(r"#{1,6}\s+(.*)", line)
        if m:
            s = slug(m.group(1))
            n = seen.get(s, 0)
            seen[s] = n + 1
            out.add(s if n == 0 else f"{s}-{n}")
    return out


def main() -> int:
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode().split("\0")
    tracked_set = {t for t in tracked if t}
    dirs = {str(p) for t in tracked_set for p in Path(t).parents if str(p) != "."}
    problems = []
    for rel in sorted(t for t in tracked_set if t.endswith(".md")):
        path = ROOT / rel
        text = FENCE.sub("", path.read_text(encoding="utf-8", errors="ignore"))
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, frag = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path
            try:
                dest_rel = str(dest.relative_to(ROOT))
            except ValueError:
                problems.append(f"{rel}: link leaves the repository: {target}")
                continue
            if file_part and dest_rel not in tracked_set and dest_rel not in dirs:
                problems.append(f"{rel}: missing target: {target}")
            elif frag and dest_rel.endswith(".md") and dest_rel in tracked_set and frag not in anchors(dest):
                problems.append(f"{rel}: no heading for anchor: {target}")
    for p in problems:
        print(p)
    print(f"docs-check: {len(problems)} problem(s) in {len([t for t in tracked_set if t.endswith('.md')])} Markdown files")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
