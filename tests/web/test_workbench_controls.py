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
        page = browser.new_page(viewport={"width": width, "height": 1000}, reduced_motion="reduce")
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
                    body = {"run_id": "offline-fixture", "answer": {"status": "abstained", "summary": "", "reason": "Offline browser fixture.", "claims": [], "caveats": []}, "evidence": [], "trace": [], "usage": {}, "seconds": 0}
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
