#!/usr/bin/env python3
"""Hover and focus every popover trigger on every deck slide and count the words that actually render.

Run against a served deck, for example:
    uv run --with playwright python scripts/audit_deck_tips.py --url http://127.0.0.1:8996/deck.html --label after --out /tmp/deck_tips_after.json

Triggers: `.has-tip` (HTML popovers), `.is-tipped` (shared SVG popover) and `.pr-hit` (chart point tooltips).
For each trigger the script moves the pointer onto it, reads the popover that is on screen, then focuses the
trigger by keyboard and reads it again. The native `title` attribute and `aria-label` are counted too, because
browsers show `title` on hover. No network calls beyond the local deck; the report holds the project's own
tooltip text and word counts only.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

LIMIT = 30
TARGET = 20
TRIGGERS = ".has-tip, .is-tipped, .pr-hit"

# Runs in the page for one trigger; returns what is on screen right now.
READ_JS = """
(node) => {
  const own = node.querySelector(':scope > .deck-tip[role="tooltip"]');
  const host = node.closest('.has-tip-host');
  const visible = el => { if (!el) return false; const s = getComputedStyle(el); return s.visibility !== 'hidden' && s.display !== 'none' && Number(s.opacity) > 0.05; };
  const text = el => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim();
  let kind = 'html', tip = own;
  if (!tip && node.classList.contains('is-tipped')) { kind = 'svg'; tip = host && host.querySelector(':scope > .deck-tip.is-svg.is-on'); }
  if (!tip && node.classList.contains('pr-hit')) { kind = 'chart'; const root = node.closest('.pr-fig, .pr-host') || document; tip = root.querySelector('.pr-tip.is-on'); }
  const svgTitle = node.querySelector(':scope > title');
  return {kind, tip: tip ? text(tip) : '', tipVisible: visible(tip), title: node.getAttribute('title') || (svgTitle ? text(svgTitle) : ''), aria: node.getAttribute('aria-label') || ''};
}
"""


def words(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def summarise(rows: list[dict], field: str) -> dict:
    counts = [r[field] for r in rows]
    if not counts:
        return {"count": 0, "max": 0, "mean": 0.0, "over_30": 0, "over_20": 0}
    return {"count": len(counts), "max": max(counts), "mean": round(statistics.fmean(counts), 2),
            "over_30": sum(c > LIMIT for c in counts), "over_20": sum(c > TARGET for c in counts)}


def audit(url: str, width: int, height: int, chrome: str | None) -> dict:
    from playwright.sync_api import sync_playwright

    rows: list[dict] = []
    notes_detail: dict[int, int] = {}
    with sync_playwright() as p:
        kwargs = {"headless": True}
        if chrome:
            kwargs["executable_path"] = chrome
        else:
            kwargs["channel"] = "chrome"
        browser = p.chromium.launch(**kwargs)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector(".reveal .slides > section")
        total = page.locator(".reveal .slides > section").count()
        page.add_style_tag(content="*{transition:none!important;animation:none!important}")
        for number in range(1, total + 1):
            page.goto(f"{url.split('#')[0]}#/{number}")
            page.wait_for_timeout(250)
            slide = page.locator(".reveal .slides > section.present").first
            heading = (slide.locator("h1, h2").first.inner_text() if slide.locator("h1, h2").count() else "").strip()
            notes_detail[number] = slide.locator("aside.notes p", has_text="Popover detail").count()
            handles = slide.locator(TRIGGERS)
            n = handles.count()
            for i in range(n):
                trigger = handles.nth(i)
                # Hover: pointer to the centre of the trigger. Clipped or hidden triggers fall back to focus only.
                hovered = False
                try:
                    trigger.scroll_into_view_if_needed(timeout=1500)
                    box = trigger.bounding_box()
                    if box and box["width"] > 0 and box["height"] > 0:
                        page.mouse.move(2, 2)
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=2)
                        page.wait_for_timeout(60)
                        hovered = True
                except Exception:
                    pass
                on_hover = trigger.evaluate(READ_JS) if hovered else None
                page.mouse.move(2, 2)
                try:
                    trigger.focus(timeout=1500)
                    page.wait_for_timeout(60)
                    on_focus = trigger.evaluate(READ_JS)
                except Exception:
                    on_focus = None
                base = on_hover or on_focus or {"kind": "unreachable", "tip": "", "tipVisible": False, "title": "", "aria": ""}
                texts = [t for t in (on_hover and on_hover["tip"], on_focus and on_focus["tip"]) if t]
                tip = max(texts, key=words) if texts else ""
                # aria-label on a tipped node is spoken, not seen, so it is reported but kept out of the headline figure.
                rows.append({
                    "slide": number, "heading": heading, "index": i, "kind": base["kind"], "hovered": hovered, "focused": on_focus is not None,
                    "tip_visible": bool((on_hover and on_hover["tipVisible"]) or (on_focus and on_focus["tipVisible"])),
                    "tip": tip, "tip_words": words(tip), "title": base["title"], "title_words": words(base["title"]),
                    "aria": base["aria"], "aria_words": words(base["aria"]),
                    "shown_words": max(words(tip), words(base["title"])),
                })
        browser.close()
    return {"url": url, "slides": total, "viewport": [width, height], "limit": LIMIT, "target": TARGET,
            "summary": {"shown (popover or title)": summarise(rows, "shown_words"), "popover": summarise(rows, "tip_words"),
                        "title attribute": summarise([r for r in rows if r["title"]], "title_words"),
                        "aria-label": summarise([r for r in rows if r["aria"]], "aria_words"),
                        "no popover text found": sum(1 for r in rows if not r["tip"]), "unreachable": sum(1 for r in rows if r["kind"] == "unreachable")},
            "popover_detail_notes_per_slide": notes_detail, "worst": sorted(rows, key=lambda r: -r["shown_words"])[:25], "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:8996/deck.html")
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", type=Path, default=None, help="JSON report path (default /tmp/deck_tips_<label>.json)")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--chrome", default=None, help="Chrome executable path; default uses the installed Chrome channel")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any shown popover or title exceeds 30 words")
    args = ap.parse_args()
    report = audit(args.url, args.width, args.height, args.chrome)
    report["label"] = args.label
    out = args.out or Path(f"/tmp/deck_tips_{args.label}.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"label": args.label, "slides": report["slides"], "summary": report["summary"], "report": str(out)}, indent=2))
    return 1 if args.strict and report["summary"]["shown (popover or title)"]["over_30"] else 0


if __name__ == "__main__":
    sys.exit(main())
