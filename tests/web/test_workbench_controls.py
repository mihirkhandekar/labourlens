"""Offline DOM and visual checks. Run with uv run --with playwright pytest tests/web.

All API routes are intercepted; no provider or external host is contacted.
Screenshots are written outside the repository for visual review.
"""
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def answered_fixture():
    """Synthetic public response; never a recorded model result."""
    return {
        "run_id": "offline-fixture",
        "answer": {"status": "answered", "summary": "Synthetic browser fixture: retrenchments increased by 140 persons.",
                   "claims": [{"text": "The fixture compares two quarterly counts.", "citations": [{"label": "O1"}, {"label": "C1"}, {"label": "P1", "quote": "Synthetic report context for browser checks."}]}], "caveats": []},
        "evidence": [
            {"kind": "statistic", "label": "O1", "source_title": "Quarterly retrenchments (synthetic fixture)", "publisher": "Fixture publisher",
             "period": "2026-Q1", "value": 3830, "unit": "persons", "release_stage": "dataset_snapshot", "population": "establishments", "adjustment": "not_applicable",
             "url": "https://example.org/statistic", "quotes": ["3830 persons dataset_snapshot not_applicable"]},
            {"kind": "calculation", "label": "C1", "source_title": "Quarterly change (synthetic fixture)", "release_stage": "calculated", "quotes": ["3830 - 3690 = 140 persons"]},
            {"kind": "report", "label": "P1", "source_title": "Synthetic report fixture", "publisher": "Fixture publisher", "release_stage": "final",
             "url": "https://example.org/report", "quotes": ["Synthetic report context for browser checks."]},
        ],
        "chart": {"series": [
            {"label": "Quarterly counts (synthetic fixture)", "unit": "persons", "points": [{"period": "2025-Q3", "value": 3500}, {"period": "2025-Q4", "value": 3690}, {"period": "2026-Q1", "value": 3830}]},
            {"label": "Quarterly comparison (synthetic fixture)", "unit": "persons", "points": [{"period": "2025-Q4", "value": 3690}, {"period": "2026-Q1", "value": 3830}]},
            {"label": "Rate (synthetic fixture)", "unit": "percent", "points": [{"period": "2025-Q3", "value": 2.8}, {"period": "2025-Q4", "value": 2.9}, {"period": "2026-Q1", "value": 3.0}]},
        ]}, "trace": [], "usage": {}, "seconds": 0,
    }


@pytest.fixture(scope="module")
def workbench_url():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=str(ROOT / "web"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    worker.join()
    server.server_close()


@pytest.mark.parametrize("width", [1440, 1024, 390])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_empty_examples_and_safe_clear_dialog(workbench_url, width, theme):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        errors, external, calls = [], [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)

        def intercept(route):
            url = route.request.url
            if not url.startswith(workbench_url + "/"):
                external.append(url)
                route.abort()
            elif "/api/" in url:
                calls.append(url)
                if url.endswith("/api/status"):
                    body = {"enabled": True, "authenticated": True}
                elif url.endswith("/api/ask"):
                    body = answered_fixture()
                else:
                    body = {}
                route.fulfill(content_type="application/json", body=json.dumps(body))
            else:
                route.continue_()

        page.route("**/*", intercept)
        page.add_init_script("localStorage.setItem('labourlens-theme', '" + theme + "')")
        page.goto(workbench_url + "/workbench.html")
        examples = page.locator(".wb-start-examples")
        examples.wait_for(state="visible")
        buttons = examples.locator("button")
        assert buttons.count() == 6
        assert buttons.evaluate_all("nodes => nodes.every(n => n.type === 'button' && n.children.length === 2 && n.querySelector('.wb-example-label') && n.querySelector('.wb-example-question'))")
        assert buttons.evaluate_all("nodes => nodes.every(n => n.querySelector('.wb-example-question').textContent.length <= 90)")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        output = Path("/tmp/labourlens-workbench-review")
        output.mkdir(exist_ok=True)
        page.screenshot(path=str(output / f"empty-{width}-{theme}.png"), full_page=True)
        expected = buttons.first.locator(".wb-example-question").inner_text()
        buttons.first.click()
        field = page.locator("#question-input")
        assert field.input_value() == expected
        assert field.evaluate("n => n === document.activeElement")
        assert not any(url.endswith("/api/ask") for url in calls)
        field.press("Enter")
        page.locator(".wb-message-user").wait_for()
        assert examples.count() == 0
        trigger = page.locator(".wb-composer-actions > button").first
        page.wait_for_function("!document.querySelector('.wb-composer-actions > button').disabled")
        assert field.input_value() == ""
        assert page.locator(".composer-meta .count").inner_text() == "0 / 1,000"
        assert page.locator(".wb-jump-latest").is_hidden()
        # The old second-card edge was the separate calculation/feedback stack.
        # Both now belong inside one answer card, with feedback collapsed.
        assert page.locator(".answer-stack > *").count() == 1
        assert page.locator(".skeleton").count() == 0
        assert not page.locator(".feedback-disclosure").evaluate("n => n.open")
        assert not page.locator(".calculation-disclosure").evaluate("n => n.open")
        assert page.locator(".answer-bezel").evaluate("n => n.scrollWidth <= n.clientWidth")
        page.wait_for_function("document.querySelector('.wb-message-user').getBoundingClientRect().top >= document.querySelector('.wb-messages').getBoundingClientRect().top")
        if width < 761:
            page.locator(".wb-panel-toggle").click()
        page.locator('[data-tab=\"sources\"]').click()
        sources = page.locator(".wb-source-panel")
        fields = sources.locator(".source-fields").first
        assert fields.locator("dt").all_text_contents() == ["Period", "Value", "Publisher", "Release stage", "Definition"]
        assert fields.locator("dd").all_text_contents() == ["2026-Q1", "3,830 persons", "Fixture publisher", "Dataset snapshot", "Establishments"]
        assert "dataset_snapshot" not in sources.inner_text()
        assert "not_applicable" not in sources.inner_text()
        assert sources.locator(".source-calculation").count() == 1
        assert sources.locator("blockquote").count() == 1
        assert sources.locator("a").count() == 2
        page.screenshot(path=str(output / f"answered-sources-{width}-{theme}.png"), full_page=True)
        page.locator('[data-tab=\"data\"]').click()
        counts = page.locator(".wb-data-panel figure").nth(0)
        page.wait_for_function("document.querySelector('.wb-data-panel figure').dataset.axisMinimum === '0'")
        assert counts.locator(".chart-axis-note").is_hidden()
        pair = page.locator(".wb-data-panel figure").nth(1)
        assert pair.get_attribute("data-presentation") == "before-after"
        assert pair.locator(".chart-pair dd").all_text_contents() == ["3,690 persons", "3,830 persons", "+140 persons"]
        assert pair.locator("svg.chart-svg").count() == 0
        pair.locator(".chart-tools button").click()
        assert pair.locator(".data-table tbody tr").count() == 2
        assert pair.locator(".table-wrap").is_visible()
        assert pair.locator(".chart-summary").inner_text()
        rate = page.locator(".wb-data-panel figure").nth(2)
        assert rate.locator(".chart-axis-note").is_visible()
        assert rate.get_attribute("data-axis-minimum") != "0"
        page.screenshot(path=str(output / f"answered-comparison-{width}-{theme}.png"), full_page=True)
        page.locator(".wb-panel").evaluate("n => { n.scrollTop = 0; }")
        page.screenshot(path=str(output / f"answered-data-{width}-{theme}.png"), full_page=True)
        if width < 761:
            page.locator(".wb-panel-close").click()
        for i in range(3):
            field.fill(f"Offline fixture follow-up {i}")
            field.press("Enter")
            page.wait_for_function("!document.querySelector('.composer-form button[type=submit]').disabled")
        messages = page.locator(".wb-messages")
        messages.evaluate("n => n.scrollTo({top: n.scrollHeight, behavior: 'instant'})")
        page.wait_for_function("document.querySelector('.wb-jump-latest').hidden")
        messages.hover()
        page.mouse.wheel(0, -1500)
        page.wait_for_function("!document.querySelector('.wb-jump-latest').hidden")
        jump = page.locator(".wb-jump-latest")
        assert jump.evaluate("n => !n.closest('.wb-messages') && !!n.closest('.wb-main')")
        assert jump.bounding_box()["y"] + jump.bounding_box()["height"] <= field.bounding_box()["y"]
        jump.click()
        page.wait_for_function("document.querySelector('.wb-jump-latest').hidden")
        trigger.click()
        dialog = page.locator("dialog.clear-confirm")
        assert dialog.is_visible()
        actions = dialog.locator(".dialog-actions")
        assert actions.locator(":scope > button").count() == 2
        assert actions.locator("button").first.evaluate("n => n.autofocus && n === document.activeElement")
        assert actions.locator("button").last.evaluate("n => n.classList.contains('btn-destructive') && !n.querySelector('.btn-ico')")
        assert actions.evaluate("n => parseFloat(getComputedStyle(n).gap) >= 10")
        dimensions = actions.locator("button").evaluate_all("nodes => nodes.map(n => { const s = getComputedStyle(n); return [n.getBoundingClientRect().height, s.borderRadius, s.paddingLeft, s.paddingRight, s.boxShadow]; })")
        assert dimensions[0] == dimensions[1]
        assert dimensions[0][2] == dimensions[0][3]
        assert dimensions[0][4] == "none"
        assert actions.locator("button").first.evaluate("n => getComputedStyle(n).outlineStyle !== 'none'")
        page.screenshot(path=str(output / f"dialog-{width}-{theme}.png"), full_page=True)
        page.keyboard.press("Escape")
        assert not dialog.is_visible()
        assert trigger.evaluate("n => n === document.activeElement")
        trigger.click()
        actions.locator(".btn-destructive").click()
        examples.wait_for(state="visible")
        assert page.locator(".wb-message-user").count() == 0
        assert field.input_value() == ""
        assert trigger.evaluate("n => n === document.activeElement")
        assert not errors
        assert not external
        browser.close()


def test_stop_aborts_and_later_turns_work_and_failed_send_restores_input(workbench_url):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        mode = ["hold"]
        pending = []
        page.add_init_script("""const originalFetch = window.fetch; window.fetch = (url, options) => { if (url === '/api/ask') window.lastAskSignal = options.signal; return originalFetch(url, options); };""")

        def intercept(route):
            url = route.request.url
            if not url.startswith(workbench_url + "/"):
                route.abort()
            elif url.endswith("/api/status"):
                route.fulfill(json={"enabled": True, "authenticated": True})
            elif url.endswith("/api/ask"):
                if mode[0] == "hold":
                    pending.append(route)
                elif mode[0] == "failure":
                    route.fulfill(status=503, json={"detail": "Synthetic start failure."})
                else:
                    route.fulfill(json=answered_fixture())
            elif "/api/" in url:
                route.fulfill(json={})
            else:
                route.continue_()

        page.route("**/*", intercept)
        page.goto(workbench_url + "/workbench.html")
        field = page.locator("#question-input")
        page.locator(".wb-example").first.click()
        field.press("Enter")
        stop = page.locator(".wb-stop")
        stop.wait_for(state="visible")
        assert field.input_value() == ""
        assert page.locator(".composer-form button[type=submit]").is_disabled()
        stop.click()
        page.locator(".wb-stopped").wait_for()
        assert page.locator(".skeleton").count() == 0
        assert stop.is_hidden()
        assert pending
        assert page.evaluate("window.lastAskSignal.aborted")
        pending[0].fulfill(json=answered_fixture())
        mode[0] = "answer"
        field.fill("A new offline question")
        field.press("Enter")
        page.locator(".answer-summary").wait_for()
        assert page.locator(".wb-turn").count() == 2
        assert field.input_value() == ""
        mode[0] = "failure"
        field.fill("Restore this offline question")
        field.press("Enter")
        page.locator(".answer-bezel.error").wait_for()
        assert field.input_value() == "Restore this offline question"
        assert page.locator(".composer-form button[type=submit]").is_enabled()
        browser.close()
