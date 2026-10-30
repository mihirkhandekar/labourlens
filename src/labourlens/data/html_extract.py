"""Passage extraction for official MOM press-release HTML.

HTML has no pages, so the locator is "section: <heading>, item <n>". HTML is used for advance releases
(there is no standalone PDF) and for final press releases that pair with them.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from labourlens.models import DocumentPassage, PARSER_VERSION, sha256_hex

EXTRACTION_METHOD = "bs4-sections"
MIN_CHARS = 30
STOP_HEADINGS = {"information and services", "social media"}
_DATE = re.compile(r"\b(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) (20\d{2})\b")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()

def page_date(root: Tag) -> str | None:
    """First 'D Month YYYY' string in the content region, as ISO date. Cross-checks the catalog date."""
    text = _norm(root.get_text(" "))
    m = _DATE.search(text)
    if not m:
        return None
    return datetime.strptime(" ".join(m.groups()), "%d %B %Y").date().isoformat()

def extract_html(path: Path, *, source_id: str, snapshot_id: str, original_url: str, title: str,
                 publication_date: str | None, release_stage: str, rights_status: str,
                 commit_text: bool) -> tuple[list[DocumentPassage], dict]:
    soup = BeautifulSoup(path.read_bytes().decode("utf-8", "replace"), "lxml")
    for t in soup(["script", "style", "noscript", "nav", "footer"]):
        t.decompose()
    for sup in soup.find_all("sup"):
        if re.fullmatch(r"(st|nd|rd|th)", sup.get_text(strip=True)):
            sup.replace_with(sup.get_text(strip=True))  # "19" + "th" -> "19th"
    soup.smooth()
    h1 = soup.find("h1")
    root: Tag = soup.body or soup
    if h1 is not None:
        # smallest ancestor of the h1 that also contains the body text blocks
        node: Tag = h1
        while node.parent is not None and len(node.find_all(["p", "li"])) < 8 and isinstance(node.parent, Tag):
            node = node.parent
        root = node
    time_tag = root.find("time") or soup.find("time")
    observed_date = None
    if time_tag is not None:
        m = _DATE.search(_norm(time_tag.get_text(" ")))
        if m:
            observed_date = datetime.strptime(" ".join(m.groups()), "%d %B %Y").date().isoformat()
    if observed_date is None:
        observed_date = page_date(root)

    # Units are (kind, text): kind is 'h' for a heading, 'p' for body text.
    units: list[tuple[str, str]] = []
    if len(root.find_all("p")) >= 8:
        for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"]):
            if el.name in ("h1", "h2", "h3", "h4"):
                units.append(("h", _norm(el.get_text(" "))))
            elif el.name in ("li", "td") and el.find("p"):
                continue  # its <p> children are captured individually
            else:
                units.append(("p", _norm(el.get_text(" "))))
    else:
        # Some pages put text in bare divs separated by <br> with <strong> section labels, not <p>.
        strong = {_norm(s.get_text(" ")) for s in root.find_all(["strong", "b"])}
        for br in root.find_all("br"):
            br.replace_with("\n")
        for line in root.get_text(" ").split("\n"):
            t = _norm(line)
            if not t:
                continue
            units.append(("h" if (t in strong and len(t) < 80) else "p", t))

    passages: list[DocumentPassage] = []
    heading = _norm(h1.get_text(" ")) if h1 else ""
    section_idx = 0
    item = 0
    seen_text: set[str] = set()
    for kind, text in units:
        if kind == "h":
            if text.lower() in STOP_HEADINGS:
                break
            heading = text
            section_idx += 1
            item = 0
            continue
        if len(text) < MIN_CHARS or text in seen_text:
            continue
        seen_text.add(text)
        item += 1
        th = sha256_hex(text.encode())
        passages.append(
            DocumentPassage(
                passage_id=f"{source_id}:s{section_idx:02d}:i{item:03d}:{th[:8]}",
                source_id=source_id,
                snapshot_id=snapshot_id,
                original_url=original_url,
                document_title=title,
                publication_date=publication_date,
                release_stage=release_stage,  # type: ignore[arg-type]
                page_number=None,
                section_heading=heading,
                block_index=len(passages),
                text=text,
                text_sha256=th,
                extraction_method=EXTRACTION_METHOD,
                quality_flag="ok",
                locator=f"section: {heading or 'top'}, item {item}",
                parser_version=PARSER_VERSION,
                rights_status=rights_status,  # type: ignore[arg-type]
                commit_text=commit_text,
            )
        )
    stats = {
        "source_id": source_id,
        "passages": len(passages),
        "catalog_publication_date": publication_date,
        "page_first_date": observed_date,
        "date_matches_catalog": observed_date == publication_date,
    }
    return passages, stats
