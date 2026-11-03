"""Rendered report page: no content may sit under the fixed section menu or push the page sideways.

Regression: notes appended straight to a band lost the content column and rendered at the far left,
over the menu. Uses the existing offline static-server fixture; no network or model calls.
"""
import pytest

from test_workbench_controls import workbench_url  # noqa: F401

WIDE = [1920, 1568, 1280, 1200]
NARROW = [1024, 390]

# Text-bearing leaves and media, outside the menu itself. Full-bleed band backgrounds are not content.
CONTENT_OVER_MENU = """() => {
  const menu = document.querySelector('.rp-steps');
  const m = menu.getBoundingClientRect();
  const hits = [];
  for (const el of document.querySelectorAll('.rp-body *')) {
    if (menu.contains(el) || el.closest('.rp-steps')) continue;
    const kids = el.children.length;
    const text = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!(text || ['svg', 'img', 'canvas', 'table'].includes(el.tagName.toLowerCase()))) continue;
    if (kids && !text) continue;
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const x = Math.min(r.right, m.right) - Math.max(r.left, m.left);
    const y = Math.min(r.bottom, m.bottom) - Math.max(r.top, m.top);
    if (x > 1 && y > 1) hits.push(`${el.tagName.toLowerCase()}.${el.className || ''}: ${(el.textContent || '').trim().slice(0, 60)}`);
  }
  return hits;
}"""


@pytest.fixture
def report_page(workbench_url):  # noqa: F811
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        yield browser, workbench_url + "/"
        browser.close()


def open_report(browser, url, width):
    page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
    page.goto(url)
    page.wait_for_selector(".rp-band")
    page.add_style_tag(content="*{transition:none!important;animation:none!important}")
    return page


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width", WIDE)
def test_no_content_intersects_the_fixed_menu_at_any_scroll_position(report_page, width, theme):
    browser, url = report_page
    page = open_report(browser, url, width)
    page.evaluate("t => { document.documentElement.dataset.theme = t; }", theme)
    assert page.locator(".rp-steps").evaluate("n => getComputedStyle(n).position") == "fixed"
    tops = page.evaluate("() => [...document.querySelectorAll('.rp-band')].map(b => [b.offsetTop, b.offsetHeight])")
    stops = {0}
    for top, height in tops:
        stops.update({top, top + height // 3, top + 2 * height // 3, top + height - 500})
    for y in sorted(s for s in stops if s >= 0):
        page.evaluate("y => window.scrollTo(0, y)", y)
        hits = page.evaluate(CONTENT_OVER_MENU)
        assert not hits, f"{width}px {theme} at scroll {y}: {hits[:3]}"
    page.close()


@pytest.mark.parametrize("width", WIDE + NARROW)
def test_every_band_note_stays_in_the_content_column_and_the_page_never_scrolls_sideways(report_page, width):
    browser, url = report_page
    page = open_report(browser, url, width)
    assert page.evaluate("() => document.documentElement.scrollWidth") <= width
    lefts = page.evaluate("""() => {
      const inner = document.querySelector('.rp-band .rp-inner').getBoundingClientRect().left;
      return {inner, notes: [...document.querySelectorAll('.rp-band > .rp-note, .rp-band > .rp-more')].map(n => [n.textContent.trim().slice(0, 40), n.getBoundingClientRect().left, n.getBoundingClientRect().right])};
    }""")
    assert lefts["notes"], "expected notes appended directly to bands"
    for text, left, right in lefts["notes"]:
        assert left >= lefts["inner"] - 1, (text, left, lefts["inner"])
        assert right <= width + 1, (text, right)
    page.close()


@pytest.mark.parametrize("width", WIDE)
def test_tinted_bands_do_not_extend_behind_the_menu(report_page, width):
    browser, url = report_page
    page = open_report(browser, url, width)
    start = page.evaluate("() => document.querySelector('.rp-band .rp-inner').getBoundingClientRect().left")
    menu_right = page.locator(".rp-steps").evaluate("n => n.getBoundingClientRect().right")
    assert menu_right <= start
    images = page.evaluate("() => [...document.querySelectorAll('.rp-band.is-tint')].map(b => getComputedStyle(b).backgroundImage)")
    assert images and all("linear-gradient" in image for image in images)
    page.close()
