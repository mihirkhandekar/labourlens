"""The site CSP is `script-src 'self'; style-src 'self'`. Keep the shipped page and scripts compatible.

Inline script or style in markup, HTML strings built in JavaScript, and style attributes set from a
string are all blocked or fragile under that policy. Setting a single CSS property through the
CSSOM (`node.style.setProperty(...)`) is allowed and is how the charts position tooltips.
"""
import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[2] / "web"
SCRIPTS = sorted((WEB / "static").rglob("*.js"))

FORBIDDEN_IN_JS = {
    "innerHTML": r"\.(?:inner|outer)HTML\b",
    "insertAdjacentHTML": r"insertAdjacentHTML",
    "document.write": r"document\.write",
    "style attribute from a string": r"setAttribute\(\s*['\"]style['\"]",
    "cssText": r"\.cssText\b",
    "style element": r"createElement\(\s*['\"]style['\"]",
    "script element": r"createElement\(\s*['\"]script['\"]",
    "inline style markup": r"\bstyle\s*=\s*[\"']",
    "eval": r"(?<![A-Za-z_$.])eval\(",
    "Function constructor": r"new\s+Function\(",
}


@pytest.mark.parametrize("page", ["index.html", "workbench.html"])
def test_html_has_no_inline_script_style_or_handlers(page):
    html = (WEB / page).read_text()
    assert not re.search(r"<style\b", html, re.I)
    assert not re.search(r"\sstyle\s*=", html, re.I)
    assert not re.search(r"\son[a-z]+\s*=", html, re.I)
    for tag in re.findall(r"<script\b[^>]*>", html, re.I):
        assert re.search(r"\bsrc\s*=", tag), f"inline script: {tag}"
    for body in re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.I | re.S):
        assert not body.strip(), "inline script body"
    for target in re.findall(r"\b(?:src|href)\s*=\s*['\"]([^'\"]+)", html, re.I):
        if target.startswith(("#", "https://", "mailto:")):
            continue
        if target in ("/", "/workbench", "/workbench.html"):
            continue
        assert not target.startswith("//"), f"{page}: external resource {target}"
        local = target.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        assert (WEB / local).is_file(), f"{page}: missing local resource {target}"


def test_static_scripts_exist():
    names = {p.name for p in SCRIPTS}
    assert {"charts.js", "evaluation.js", "app.js"} <= names


def test_static_scripts_never_inject_html_or_inline_style():
    found = []
    for path in SCRIPTS:
        text = path.read_text()
        for label, pattern in FORBIDDEN_IN_JS.items():
            if re.search(pattern, text):
                found.append(f"{path.relative_to(WEB)}: {label}")
    assert not found, found


def test_stylesheets_load_no_external_resources():
    for path in sorted((WEB / "static").rglob("*.css")):
        text = path.read_text()
        assert not re.search(r"@import\s+url\(\s*['\"]?https?:", text), path.name
        for target in re.findall(r"url\(\s*['\"]?([^)'\"]+)", text):
            assert not re.match(r"https?:|//", target), f"{path.name}: external url {target}"
