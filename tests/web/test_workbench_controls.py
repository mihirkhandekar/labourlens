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
            {"kind": "statistic", "label": "O1", "source_id": "stat-a", "source_title": "Quarterly retrenchments (synthetic fixture)", "publisher": "Fixture publisher",
             "period": "2026-Q1", "value": 3830, "unit": "persons", "release_stage": "dataset_snapshot", "population": "establishments", "adjustment": "not_applicable",
             "url": "https://example.org/statistic", "quotes": ["3830 persons dataset_snapshot not_applicable"]},
            {"kind": "calculation", "label": "C1", "source_id": "calc-a", "source_title": "Quarterly change (synthetic fixture)", "release_stage": "calculated", "quotes": ["3830 - 3690 = 140 persons"]},
            {"kind": "report", "label": "P1", "source_id": "report-a", "source_title": "Synthetic report fixture", "publisher": "Fixture publisher", "release_stage": "final", "date": "2026-09-22", "locator": "p. 1",
             "url": "https://example.org/report", "quotes": ["Synthetic report context for browser checks."]},
            *[{"kind": "report", "label": f"P{n}", "source_id": "report-a" if n < 8 else "report-b", "source_title": "Synthetic report fixture" if n < 8 else "Second synthetic report", "publisher": "Fixture publisher",
               "release_stage": "final", "date": "2026-09-22", "locator": f"p. {n}", "url": "https://example.org/report" if n < 8 else "https://example.org/second",
               "quotes": [f"Uncited synthetic passage {n}."]} for n in range(2, 13)],
        ],
        "chart": {"series": [
            {"label": "Quarterly counts (synthetic fixture)", "unit": "persons", "points": [{"period": "2025-Q3", "value": 3500}, {"period": "2025-Q4", "value": 3690}, {"period": "2026-Q1", "value": 3830}]},
            {"label": "Quarterly comparison (synthetic fixture)", "unit": "persons", "points": [{"period": "2025-Q4", "value": 3690}, {"period": "2026-Q1", "value": 3830}]},
            {"label": "Rate (synthetic fixture)", "unit": "percent", "points": [{"period": "2025-Q3", "value": 2.8}, {"period": "2025-Q4", "value": 2.9}, {"period": "2026-Q1", "value": 3.0}]},
        ]}, "trace": [{"node": "execute_tool", "event": "ok", "detail": {"tool": "search_reports", "new_items": [f"P{n}" for n in range(1, 13)], "seconds": 0.1}}], "usage": {}, "seconds": 0,
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


@pytest.mark.parametrize("width", [1920, 1440, 1024, 390])
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
        trigger = page.get_by_role("button", name="Clear chat", exact=True)
        page.wait_for_function("![...document.querySelectorAll('.wb-composer-actions > button')].find(b => b.textContent === 'Clear chat').disabled")
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
        assert page.locator('[data-tab="data"]').get_attribute("aria-selected") == "true"
        sources = page.locator(".wb-source-panel")
        assert sources.is_visible() and page.locator(".wb-data-panel").is_visible()
        assert sources.evaluate("n => !n.closest('.wb-panel') && getComputedStyle(n).overflowY === 'auto'")
        assert page.locator(".wb-tabs [role=tab]").all_text_contents() == ["Activity", "Data", "MCP"]
        statistic = sources.locator('[data-source-key="stat-a"] .source-fields')
        assert statistic.locator("dt").all_text_contents() == ["Period", "Value", "Publisher", "Release stage", "Definition"]
        assert statistic.locator("dd").all_text_contents() == ["2026-Q1", "3,830 persons", "Fixture publisher", "Dataset snapshot", "Establishments"]
        assert "dataset_snapshot" not in sources.inner_text()
        assert "not_applicable" not in sources.inner_text()
        assert sources.locator(".source-group").count() == 4
        assert sources.locator('[data-source-key="report-a"]').count() == 1
        assert sources.locator('[data-source-key="report-a"] .source-item').count() == 1
        assert "7 passages retrieved; 1 cited" in sources.locator('[data-source-key="report-a"] .source-meta').inner_text()
        assert sources.locator('[data-source-key="report-b"]').evaluate("n => !n.open && !!n.closest('.source-uncited')")
        assert sources.locator("blockquote").count() == 12
        assert sources.locator(".source-calculation").count() == 1
        activity = page.locator('[data-tab="activity"]'); activity.click()
        step = page.locator(".steps .step", has_text="search_reports")
        assert "12 passages from 2 sources" in step.inner_text()
        assert "P1, P2" not in step.inner_text()
        assert step.locator(".step-evidence li").count() == 12
        page.locator('[data-tab="data"]').click()
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


# ---- streaming run (D-079): a small real HTTP server, because Playwright cannot fulfil a route incrementally ----------------------------------

def frame(name, data):
    return f"event: {name}\ndata: {json.dumps(data)}\n\n".encode()


@pytest.fixture
def stream_server():
    """Serves web/ plus a scripted /api/status, /api/ask/stream and /api/ask. `state["mode"]` picks the stream behaviour; `state["release"]` holds the
    stream open after its first frames so the test can look at the page mid-run. The stream body has no length: it ends when the handler closes."""
    state = {"mode": "ok", "release": threading.Event(), "asks": 0, "streams": 0}

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_json(self, status, payload):
            raw = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == "/api/status":
                return self.send_json(200, {"enabled": True, "authenticated": True})
            if self.path.startswith("/api/"):
                return self.send_json(200, {})
            return super().do_GET()

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            if self.path == "/api/ask":
                state["asks"] += 1
                return self.send_json(200, answered_fixture())
            if self.path != "/api/ask/stream":
                return self.send_json(200, {})
            state["streams"] += 1
            if state["mode"] == "missing":
                return self.send_json(404, {"detail": "Not Found"})
            if state["mode"] == "refused":
                return self.send_json(429, {"detail": "Request limit reached. Try again later."})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(frame("status", {"stage": "accepted", "state": "done", "text": "Question accepted."}))
                self.wfile.write(frame("status", {"stage": "planning", "state": "running", "text": "Planning which evidence to collect."}))
                self.wfile.write(frame("tool", {"phase": "started", "tool": "get_series", "args": {"source_id": "retrenched_employees"}}))
                self.wfile.flush()
                if state["mode"] == "hold":
                    state["release"].wait(15)
                if state["mode"] == "error":
                    self.wfile.write(frame("error", {"status": 503, "detail": "Synthetic mid-stream failure."}))
                    return
                self.wfile.write(b": keepalive\n\n")
                self.wfile.write(frame("tool", {"phase": "finished", "item": {"node": "execute_tool", "event": "ok", "detail": {"tool": "get_series", "seconds": 0.2, "new_items": ["O1"]}}}))
                self.wfile.write(frame("status", {"stage": "answering", "state": "running", "text": "Writing the answer from the evidence."}))
                self.wfile.write(frame("result", answered_fixture()))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass  # the browser stopped the run

    handler = functools.partial(Handler, directory=str(ROOT / "web"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    yield state
    state["release"].set()
    server.shutdown()
    worker.join()
    server.server_close()


def open_workbench(runtime, state):
    browser = runtime.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(state["url"] + "/workbench.html")
    return browser, page


def test_stream_shows_live_steps_before_the_answer_and_then_the_validated_answer(stream_server):
    playwright = pytest.importorskip("playwright.sync_api")
    stream_server["mode"] = "hold"
    with playwright.sync_playwright() as runtime:
        browser, page = open_workbench(runtime, stream_server)
        field = page.locator("#question-input")
        field.fill("How did retrenchments change?")
        field.press("Enter")
        status = page.locator(".run-status")
        status.filter(has_text="Planning which evidence to collect.").wait_for()
        assert status.get_attribute("role") == "status" and status.get_attribute("aria-live") == "polite"
        running = page.locator(".steps .step.active")
        running.wait_for()
        assert "get_series" in running.inner_text() and "running" in running.inner_text()
        assert page.locator(".answer-summary").count() == 0 and page.locator(".skeleton").count() > 0  # no answer text before validation finishes
        assert page.locator(".wb-stop").is_visible() and field.input_value() == ""
        stream_server["release"].set()
        page.locator(".answer-summary").wait_for()
        assert "retrenchments increased by 140 persons" in page.locator(".answer-summary").inner_text()
        assert stream_server["streams"] == 1 and stream_server["asks"] == 0
        assert page.locator(".wb-stop").is_hidden() and page.locator(".composer-form button[type=submit]").is_enabled()
        browser.close()


def test_stream_error_event_restores_the_question_and_shows_the_message(stream_server):
    playwright = pytest.importorskip("playwright.sync_api")
    stream_server["mode"] = "error"
    with playwright.sync_playwright() as runtime:
        browser, page = open_workbench(runtime, stream_server)
        field = page.locator("#question-input")
        field.fill("Restore this streamed question")
        field.press("Enter")
        page.locator(".answer-bezel.error").wait_for()
        assert "Synthetic mid-stream failure." in page.locator(".answer-bezel.error").inner_text()
        assert field.input_value() == "Restore this streamed question" and page.locator(".composer-form button[type=submit]").is_enabled()
        assert stream_server["asks"] == 0  # a failed run is not retried through the other endpoint
        browser.close()


def test_stop_aborts_the_stream(stream_server):
    playwright = pytest.importorskip("playwright.sync_api")
    stream_server["mode"] = "hold"
    with playwright.sync_playwright() as runtime:
        browser, page = open_workbench(runtime, stream_server)
        field = page.locator("#question-input")
        field.fill("Stop this streamed run")
        field.press("Enter")
        page.locator(".run-status").filter(has_text="Planning").wait_for()
        page.locator(".wb-stop").click()
        page.locator(".wb-stopped").wait_for()
        assert page.locator(".wb-stop").is_hidden() and field.is_enabled()
        stream_server["release"].set()
        field.fill("A later question")
        stream_server["mode"] = "ok"
        field.press("Enter")
        page.locator(".answer-summary").wait_for()
        browser.close()


def test_missing_stream_endpoint_falls_back_to_the_plain_one_but_a_refusal_does_not(stream_server):
    playwright = pytest.importorskip("playwright.sync_api")
    stream_server["mode"] = "missing"
    with playwright.sync_playwright() as runtime:
        browser, page = open_workbench(runtime, stream_server)
        field = page.locator("#question-input")
        field.fill("Use the plain endpoint")
        field.press("Enter")
        page.locator(".answer-summary").wait_for()
        assert stream_server["streams"] == 1 and stream_server["asks"] == 1
        stream_server["mode"] = "refused"
        field.fill("Rate limited")
        field.press("Enter")
        page.locator(".answer-bezel.error").wait_for()
        assert "Request limit reached" in page.locator(".answer-bezel.error").inner_text()
        assert stream_server["asks"] == 1 and field.input_value() == "Rate limited"  # no second attempt at a refused request
        browser.close()


@pytest.mark.parametrize("manual", [False, True])
def test_activity_while_running_then_data_unless_user_chose_a_tab(workbench_url, manual):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        pending = []

        def intercept(route):
            url = route.request.url
            if not url.startswith(workbench_url + "/"):
                route.abort()
            elif url.endswith("/api/status"):
                route.fulfill(json={"enabled": True, "authenticated": True})
            elif url.endswith("/api/ask"):
                pending.append(route)
            elif "/api/" in url:
                route.fulfill(json={})
            else:
                route.continue_()

        page.route("**/*", intercept)
        page.goto(workbench_url + "/workbench.html")
        assert page.locator('[data-tab="data"]').get_attribute("aria-selected") == "true"
        page.locator(".wb-example").first.click()
        page.locator("#question-input").press("Enter")
        page.wait_for_function("document.querySelector('[data-tab=activity]').getAttribute('aria-selected') === 'true'")
        if manual:
            page.locator('[data-tab="mcp"]').click()
        while not pending:
            page.wait_for_timeout(20)
        pending[0].fulfill(json=answered_fixture())
        page.locator(".answer-summary").wait_for()
        expected = "mcp" if manual else "data"
        assert page.locator(f'[data-tab="{expected}"]').get_attribute("aria-selected") == "true"
        assert page.locator(".wb-source-panel .source-group").count() == 4
        browser.close()


@pytest.mark.parametrize("width", [1440, 390])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_examples_menu_fills_without_submitting_and_closes(workbench_url, width, theme):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        asks = []

        def intercept(route):
            url = route.request.url
            if not url.startswith(workbench_url + "/"):
                route.abort()
            elif url.endswith("/api/status"):
                route.fulfill(json={"enabled": True, "authenticated": True})
            elif "/api/ask" in url:
                asks.append(url)
                route.fulfill(json=answered_fixture())
            elif "/api/" in url:
                route.fulfill(json={})
            else:
                route.continue_()

        page.route("**/*", intercept)
        page.add_init_script("localStorage.setItem('labourlens-theme', '" + theme + "')")
        page.goto(workbench_url + "/workbench.html")
        button = page.get_by_role("button", name="Examples", exact=True)
        popover = page.locator("#wb-examples-popover")
        field = page.locator("#question-input")
        page.wait_for_function("!document.querySelector('#question-input').disabled")
        assert button.get_attribute("aria-expanded") == "false" and popover.is_hidden()
        assert button.evaluate("n => n.nextElementSibling.textContent") == "Clear chat"
        button.click()
        assert button.get_attribute("aria-expanded") == "true" and popover.is_visible()
        items = popover.locator("button")
        assert items.count() == 9
        assert items.evaluate_all("nodes => nodes.every(n => n.type === 'button' && n.querySelector('.wb-example-label') && n.querySelector('.wb-example-question'))")
        box = popover.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= width
        out = Path("/tmp/labourlens-workbench-review"); out.mkdir(exist_ok=True)
        page.screenshot(path=str(out / f"examples-menu-{width}-{theme}.png"))
        page.keyboard.press("Escape")
        assert popover.is_hidden() and button.evaluate("n => n === document.activeElement")
        button.click()
        page.mouse.click(5, 5)
        assert popover.is_hidden()
        button.click()
        chosen = items.nth(8).locator(".wb-example-question").inner_text()
        items.nth(8).click()
        assert popover.is_hidden() and field.input_value() == chosen
        assert field.evaluate("n => n === document.activeElement") and not asks
        field.press("Enter")
        page.locator(".wb-message-user").wait_for()
        assert page.locator(".wb-start-examples").count() == 0
        page.wait_for_function("!document.querySelector('#question-input').disabled")
        button.click()
        assert popover.is_visible()
        items.nth(0).click()
        browser.close()


STREAM_INIT = """
window.__events = [];
const realFetch = window.fetch.bind(window);
window.fetch = (url, options) => {
  if (url !== '/api/ask/stream') return realFetch(url, options);
  const encoder = new TextEncoder();
  const stream = new ReadableStream({start(controller) { window.__push = (name, data) => controller.enqueue(encoder.encode(`event: ${name}\\ndata: ${JSON.stringify(data)}\\n\\n`)); window.__close = () => controller.close(); }});
  return Promise.resolve(new Response(stream, {status: 200, headers: {'Content-Type': 'text/event-stream'}}));
};
"""


@pytest.mark.parametrize("outcome", ["answer", "error"])
def test_activity_follows_streamed_steps_and_data_opens_at_the_end(workbench_url, outcome):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 700}, reduced_motion="reduce")

        def intercept(route):
            url = route.request.url
            if not url.startswith(workbench_url + "/"):
                route.abort()
            elif url.endswith("/api/status"):
                route.fulfill(json={"enabled": True, "authenticated": True})
            elif "/api/" in url:
                route.fulfill(json={})
            else:
                route.continue_()

        page.route("**/*", intercept)
        page.add_init_script(STREAM_INIT)
        page.goto(workbench_url + "/workbench.html")
        page.wait_for_function("!document.querySelector('#question-input').disabled")
        page.locator(".wb-example").first.click()
        page.locator("#question-input").press("Enter")
        page.wait_for_function("document.querySelector('[data-tab=activity]').getAttribute('aria-selected') === 'true' && !!window.__push")
        panel = page.locator(".wb-panel")

        def push_steps(start, stop):
            for n in range(start, stop):
                page.evaluate("([n]) => window.__push('tool', {item: {node: 'execute_tool', event: 'ok', detail: {tool: 'get_series', seconds: 0.1, args: {n}}}})", [n])

        push_steps(0, 40)
        page.wait_for_function("(() => { const p = document.querySelector('.wb-panel'); return p.scrollHeight > p.clientHeight + 100 && p.scrollHeight - p.scrollTop - p.clientHeight < 24; })()")
        # Scrolling up stops the following; new steps do not drag the reader down.
        panel.hover()
        page.mouse.wheel(0, -20000)
        page.wait_for_function("document.querySelector('.wb-panel').scrollTop === 0")
        push_steps(40, 50)
        page.wait_for_timeout(200)
        assert panel.evaluate("n => n.scrollTop") == 0
        # Returning to the bottom resumes following.
        panel.evaluate("n => { n.scrollTop = n.scrollHeight; }")
        page.wait_for_function("document.querySelector('.wb-panel').scrollHeight - document.querySelector('.wb-panel').scrollTop - document.querySelector('.wb-panel').clientHeight < 24")
        page.wait_for_timeout(150)  # let the scroll event re-enable following
        push_steps(50, 60)
        page.wait_for_function("(() => { const p = document.querySelector('.wb-panel'); return p.scrollHeight - p.scrollTop - p.clientHeight < 24; })()")
        if outcome == "answer":
            page.evaluate("([body]) => { window.__push('result', body); window.__close(); }", [answered_fixture()])
            page.locator(".answer-summary").wait_for()
        else:
            page.evaluate("() => { window.__push('error', {detail: 'Synthetic stream failure.'}); window.__close(); }")
            page.locator(".answer-bezel.error").wait_for()
        assert page.locator('[data-tab="data"]').get_attribute("aria-selected") == "true"
        browser.close()
