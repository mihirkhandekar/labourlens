"""An access code in a shared link (#code= or ?code=) fills the access field and is removed from the address bar; the deck link carries it.

Fake code only. Offline: API routes are intercepted and nothing leaves the local static server."""
import pytest
from test_workbench_controls import workbench_url  # noqa: F401  (fixture)

FAKE = "test-code-not-real"


def open_page(runtime, base, path, logins):
    browser = runtime.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    def intercept(route):
        url = route.request.url
        if not url.startswith(base + "/"):
            route.abort()
        elif url.endswith("/api/status"):
            route.fulfill(json={"enabled": True, "authenticated": False})
        elif url.endswith("/api/login"):
            logins.append(route.request.post_data)
            route.fulfill(status=401, json={"detail": "Invalid access code."})
        elif "/api/" in url:
            route.fulfill(json={})
        else:
            route.continue_()

    page.route("**/*", intercept)
    page.goto(base + path)
    return browser, page


@pytest.mark.parametrize("suffix, expected, remaining", [
    (f"#code={FAKE}", FAKE, ""),
    (f"?code={FAKE}", FAKE, ""),
    ("#code=a%20b%26c%3Dd", "a b&c=d", ""),                       # URL-encoded values decode
    (f"?question=hello&code={FAKE}#code=other", "other", ""),  # the fragment wins; the page then clears ?question as it always did
    (f"#section=1&code={FAKE}", FAKE, "#section=1"),
])
def test_workbench_takes_the_code_from_the_url_and_never_submits_it(workbench_url, suffix, expected, remaining):  # noqa: F811
    playwright = pytest.importorskip("playwright.sync_api")
    logins, logged = [], []
    with playwright.sync_playwright() as runtime:
        browser, page = open_page(runtime, workbench_url, "/workbench.html" + suffix, logins)
        page.on("console", lambda message: logged.append(message.text))
        field = page.locator("input[name=code]")
        field.wait_for()
        assert field.input_value() == expected and field.get_attribute("type") == "password"
        assert page.evaluate("location.search + location.hash") == remaining and FAKE not in page.url
        page.wait_for_timeout(400)
        assert logins == []  # explicit: the visitor presses Unlock
        assert not any(FAKE in text for text in logged)
        assert page.evaluate("localStorage.length + sessionStorage.length") == 0
        page.locator("button[type=submit]").first.click()
        page.locator("input[name=code]").wait_for()
        assert len(logins) == 1 and expected in logins[0].replace("\\u0026", "&")
        browser.close()


def test_no_code_in_the_url_leaves_the_field_empty_and_the_url_alone(workbench_url):  # noqa: F811
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser, page = open_page(runtime, workbench_url, "/workbench.html?x=1#y", [])
        assert page.locator("input[name=code]").input_value() == "" and page.evaluate("location.search + location.hash") == "?x=1#y"
        browser.close()


def test_deck_link_gets_the_code_only_when_the_deck_was_opened_with_one(workbench_url):  # noqa: F811
    playwright = pytest.importorskip("playwright.sync_api")
    probe = """async () => { const m = await import('/static/presentation/graphics.js'); const a = m.workbenchShot().querySelector('a');
                           return {href: a.href, where: location.search + location.hash, plain: m.workbenchHref('')}; }"""
    with playwright.sync_playwright() as runtime:
        browser, page = open_page(runtime, workbench_url, f"/deck.html?code={FAKE}&print-pdf=1", [])
        got = page.evaluate(probe)
        assert got["href"] == f"https://labourlens.navig.me/workbench#code={FAKE}" and got["plain"] == "https://labourlens.navig.me/workbench"
        assert got["where"] == "?print-pdf=1"  # cleaned, other parameters kept
        browser.close()
        browser, page = open_page(runtime, workbench_url, "/deck.html", [])
        assert page.evaluate(probe)["href"] == "https://labourlens.navig.me/workbench"
        browser.close()
