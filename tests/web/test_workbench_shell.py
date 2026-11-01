from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (ROOT / "web/static/js/workbench.js").read_text()
PAGE = (ROOT / "web/static/js/workbench-page.js").read_text()
CSS = (ROOT / "web/static/css/workbench.css").read_text()


def test_workbench_has_focused_access_gate_and_session_status_messages():
    assert "access-screen" in SCRIPT
    assert "name = 'code'" in SCRIPT
    assert "autocomplete = 'current-password'" in SCRIPT
    assert "credentials: 'same-origin'" in SCRIPT
    assert "Login temporarily locked. Try again later." not in SCRIPT  # messages are rendered verbatim from the endpoint
    assert "rootStatus.textContent = error.message" in SCRIPT
    assert "access.hidden = enabled && authenticated" in SCRIPT


def test_full_viewport_conversation_and_context_tabs_exist():
    for selector in ("wb-grid", "wb-messages", "wb-panel", "wb-tabs", "wb-source-panel", "wb-data-panel"):
        assert selector in SCRIPT
    assert "100dvh" in CSS
    assert "overflow: hidden" in CSS
    assert "overflow-y: auto" in CSS
    assert "Jump to latest" in SCRIPT
    assert "Clear chat" in SCRIPT and "Clear this chat?" in SCRIPT
    assert "Sources" in SCRIPT and "Activity" in SCRIPT and "Data" in SCRIPT


def test_examples_cover_requested_question_types_and_enter_behavior():
    for label in ("Factual lookup", "Comparison", "Cross-source", "Revision conflict", "Ambiguity", "Adversarial and safety"):
        assert label in SCRIPT
    assert "examplesToggle" in SCRIPT
    assert "event.key === 'Enter' && !event.shiftKey" in SCRIPT
    assert "event.key === 'Enter' && (event.ctrlKey || event.metaKey)" not in SCRIPT
    assert "Clear chat" in SCRIPT


def test_right_panel_is_responsive_and_source_citations_focus_evidence():
    assert "@media (max-width: 760px)" in CSS
    assert "wb-rail.is-open" in CSS
    assert "Focuses this item in Sources and context." in SCRIPT
    assert "data-evidence-label" in SCRIPT
    assert "The server stops the run after 80 seconds if it has not finished." in SCRIPT
    assert "closePanel" in SCRIPT
    assert "setTimeout(() => controller.abort(), 95000)" in SCRIPT


def test_workbench_has_no_unapproved_internal_copy_or_html_injection():
    for forbidden in ("innerHTML", "insertAdjacentHTML", "chain of thought", "A3", "R3"):
        assert forbidden not in SCRIPT
    assert "openai.com" not in SCRIPT
    assert "mountWorkbench" in PAGE and "Presentation" in SCRIPT
