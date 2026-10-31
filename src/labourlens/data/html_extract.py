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
from labourlens.data.pdf_extract import has_controls, looks_garbled

EXTRACTION_METHOD = "bs4-sections"
MIN_CHARS = 30
STOP_HEADINGS = {"information and services", "social media"}
_DATE = re.compile(r"\b(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) (20\d{2})\b")


def _norm(s: str) -> str:
    return re.sub(r"[ \t\r\n]+", " ", s.replace("\xa0", " ")).strip(" \t\r\n")


def _heading_text(el: Tag) -> str:
    return _norm(" ".join(str(s) for s in el.strings if s.parent.name != "sup"))

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
    # Never widen to the page body merely to reach a paragraph-count threshold:
    # some official articles use bare divs and breaks rather than paragraphs.
    root = soup.select_one("article, .page-content, main, #MainContent")
    if root is None and h1 is not None:
        root = h1.parent
    if root is None:
        raise ValueError("No article content region found")
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
    if root.find(["p", "li", "td"]) and not root.find("br"):
        for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"]):
            if el.name in ("h1", "h2", "h3", "h4"):
                units.append(("h", _heading_text(el)))
            elif el.name in ("li", "td") and el.find("p"):
                continue  # its <p> children are captured individually
            else:
                units.append(("p", _norm(el.get_text(" "))))
    else:
        # Some pages put text in bare divs separated by <br> with <strong> section labels, not <p>.
        for el in root.find_all(["strong", "b", "h1", "h2", "h3", "h4"]):
            for sup in el.find_all("sup"):
                sup.decompose()
        strong = {_heading_text(s) for s in root.find_all(["strong", "b", "h1", "h2", "h3", "h4"])}
        for br in root.find_all("br"):
            br.replace_with("\n")
        for line in root.get_text(" ").split("\n"):
            t = _norm(line)
            if not t:
                continue
            units.append(("h" if (t in strong and len(t) < 80) else "p", t))

    passages: list[DocumentPassage] = []
    heading = _heading_text(h1) if h1 else ""
    section_idx = 0
    item = 0
    rights_notices: list[str] = []
    for kind, text in units:
        if kind == "h":
            if text.lower() in STOP_HEADINGS:
                break
            heading = text
            section_idx += 1
            item = 0
            continue
        if re.search(r"copyright|reproduction|reproduced.*permission", text, re.I):
            rights_notices.append(text)
            continue
        if len(text) < MIN_CHARS and not has_controls(text):
            continue
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
                quality_flag="garbled" if looks_garbled(text)[0] else "ok",
                quality_note=looks_garbled(text)[1],
                raw_text_sha256=th,
                dup_group=sha256_hex(" ".join(text.split()).encode()),
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
        "rights_notices": rights_notices,
    }
    return passages, stats
