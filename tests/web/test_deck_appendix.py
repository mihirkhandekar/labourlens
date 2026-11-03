"""Rendered appendix navigation, using the existing offline static-server fixture.

No provider calls are made. Run with Playwright installed and Chromium available.
"""
import pytest

from test_workbench_controls import workbench_url  # noqa: F401


@pytest.fixture
def deck_page(workbench_url):  # noqa: F811
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.goto(workbench_url + "/deck.html")
        page.wait_for_selector(".reveal.ready")
        page.wait_for_function("document.querySelector('.deck-counter').textContent.includes(' / ')")
        yield page
        browser.close()


def counts(page):
    return page.evaluate("""() => {
      const slides = [...document.querySelectorAll('.slides > section')];
      return {total: slides.length, appendix: slides.filter(s => 'appendix' in s.dataset).length,
              counter: document.querySelector('.deck-counter').textContent,
              current: slides.indexOf(document.querySelector('.slides > section.present')) + 1};
    }""")


def press_a(page, times, **flags):
    """Control the monotonic clock, without sleeps or depending on keyboard execution speed."""
    page.evaluate("""({times, flags}) => {
      const original = performance.now;
      try {
        for (const time of times) {
          performance.now = () => time;
          (document.activeElement || document.body).dispatchEvent(new KeyboardEvent('keydown',
            {key: 'a', code: 'KeyA', keyCode: 65, bubbles: true, cancelable: true, ...flags}));
        }
      } finally { performance.now = original; }
    }""", {"times": times, "flags": flags})


def test_default_deck_excludes_appendices_from_navigation_progress_and_overview(deck_page):
    page = deck_page
    main = counts(page)["total"]
    assert main > 1 and counts(page)["appendix"] == 0
    assert counts(page)["counter"] == f"1 / {main}"
    page.keyboard.press("Shift+ArrowRight")
    assert counts(page)["counter"] == f"{main} / {main}"
    assert page.get_by_role("button", name="Next slide", exact=True).is_disabled()
    assert page.locator(".progress span").evaluate("n => n.style.transform") == "scaleX(1)"
    page.keyboard.press("ArrowRight")
    assert counts(page)["current"] == main
    page.keyboard.press("ArrowLeft")
    assert counts(page)["counter"] == f"{main - 1} / {main}"
    page.keyboard.press("o")
    assert page.locator(".reveal").evaluate("n => n.classList.contains('overview')")
    assert page.locator(".slides > section[data-appendix]").count() == 0
    assert page.locator(".slides > section").count() == main


def test_double_a_timing_and_no_auto_slide_conflict(deck_page):
    page = deck_page
    main = counts(page)["total"]
    press_a(page, [0])
    assert counts(page)["total"] == main
    press_a(page, [401])
    assert counts(page)["total"] == main
    press_a(page, [801])  # Inclusive 400 ms boundary; the first press at time zero is valid.
    shown = counts(page)
    assert shown["appendix"] > 0
    assert shown["total"] == main + shown["appendix"]
    assert shown["counter"] == f"1 / {shown['total']}"
    assert page.locator(".playback").count() == 0
    page.keyboard.press("o")
    press_a(page, [1000, 1200])
    assert counts(page)["total"] == main
    assert page.locator(".slides > section[data-appendix]").count() == 0


def test_double_a_ignores_repeats_modifiers_editable_fields_and_interrupted_pairs(deck_page):
    page = deck_page
    main = counts(page)["total"]
    press_a(page, [1000, 1100], repeat=True)
    press_a(page, [2000, 2100], ctrlKey=True)
    press_a(page, [3000, 3100], metaKey=True)
    press_a(page, [4000, 4100], altKey=True)
    page.evaluate("""() => { const field = document.createElement('input'); document.body.append(field); field.focus(); }""")
    press_a(page, [5000, 5100])
    page.locator("input").evaluate("n => n.remove()")
    press_a(page, [6000])
    page.keyboard.press("Shift")
    press_a(page, [6100])
    assert counts(page)["total"] == main


def test_hiding_from_appendix_returns_to_final_main_slide_and_updates_counts(deck_page):
    page = deck_page
    main = counts(page)["total"]
    press_a(page, [1000, 1100])
    page.keyboard.press("Shift+ArrowRight")
    assert page.locator(".slides > section.present").get_attribute("data-chapter") == "Appendix"
    press_a(page, [2000, 2100])
    assert counts(page) == {"total": main, "appendix": 0, "counter": f"{main} / {main}", "current": main}
    assert page.get_by_role("button", name="Next slide", exact=True).is_disabled()
    assert page.locator(".progress span").evaluate("n => n.style.transform") == "scaleX(1)"
    page.keyboard.press("ArrowLeft")
    assert counts(page)["current"] == main - 1
    press_a(page, [3000, 3100])
    assert counts(page)["appendix"] > 0
    assert counts(page)["current"] == main - 1
    assert page.locator(".slides > section").evaluate_all("nodes => nodes.slice(nodes.findIndex(n => 'appendix' in n.dataset)).every(n => 'appendix' in n.dataset)")


@pytest.mark.parametrize("target", ["appendix", "decisions-api", "numeric"])
def test_initial_appendix_hash_reveals_and_jumps(deck_page, target):
    page = deck_page
    main = counts(page)["total"]
    destination = str(main + 2) if target == "numeric" else target
    page.goto(page.url.split("#", 1)[0] + "#/" + destination)
    # Reload is necessary: goto with only a hash difference is a same-document navigation.
    page.reload()
    page.wait_for_selector(".reveal.ready")
    page.wait_for_function("document.querySelector('.slides > section.present')?.dataset.chapter === 'Appendix'")
    assert counts(page)["appendix"] > 0
    if target == "numeric":
        assert counts(page)["current"] == main + 2
    else:
        assert page.locator(".slides > section.present").get_attribute("id") == target


@pytest.mark.parametrize("target", ["appendix", "decisions-api", "numeric"])
def test_hash_changes_and_main_slide_hotlinks_reveal_and_jump(deck_page, target):
    page = deck_page
    main = counts(page)["total"]
    destination = str(main + 2) if target == "numeric" else target
    # Exercise a real main-slide hotlink, including the default appendix index link shape.
    page.evaluate("""destination => {
      const link = document.createElement('a'); link.href = '#/' + destination;
      document.querySelector('.slides > section.present').append(link); link.click(); link.remove();
    }""", destination)
    page.wait_for_function("document.querySelector('.slides > section.present')?.dataset.chapter === 'Appendix'")
    assert counts(page)["appendix"] > 0
    if target == "numeric":
        assert counts(page)["current"] == main + 2
    else:
        assert page.locator(".slides > section.present").get_attribute("id") == target
    press_a(page, [1000, 1100])
    assert counts(page)["total"] == main
    page.evaluate("destination => { location.hash = '#/' + destination; }", destination)
    page.wait_for_function("document.querySelector('.slides > section.present')?.dataset.chapter === 'Appendix'")
    assert counts(page)["appendix"] > 0


def test_help_explains_appendix_and_notes_keys(deck_page):
    page = deck_page
    page.keyboard.press("Shift+/")
    assert page.get_by_text("Show or hide appendices (double press within 400 ms)", exact=True).is_visible()
    assert page.get_by_text("Show or hide speaker notes (double press within 450 ms)", exact=True).is_visible()
    assert page.get_by_text("A A", exact=True).is_visible()
    assert page.get_by_text("X X", exact=True).is_visible()
