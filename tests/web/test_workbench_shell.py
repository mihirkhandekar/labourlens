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
    for label in ("Lookup", "Comparison", "Cross-source", "Preliminary and final", "Causal limits", "Injection resistance"):
        assert label in SCRIPT
    assert "wb-start-examples" in SCRIPT
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


def test_shell_keeps_page_fixed_and_scrolls_only_thread_and_panels():
    assert "html:has(.workbench-root) { height: 100dvh; overflow: hidden; }" in CSS
    assert "grid-template-rows: minmax(0, 1fr)" in CSS
    assert ".wb-chat { display: flex; flex-direction: column; min-width: 0; min-height: 0; height: 100%; overflow: hidden;" in CSS
    assert ".wb-rail { display: flex; flex-direction: column; min-width: 0; min-height: 0; height: 100%; overflow: hidden;" in CSS
    assert ".wb-panel { flex: 2 1 0; min-height: 0; overflow-y: auto;" in CSS
    assert ".wb-messages { position: relative; display: flex; flex: 1 1 0;" in CSS
    assert ".wb-messages > * { flex: none; min-width: 0; }" in CSS
    # No scrollIntoView: it can scroll the fixed page ancestors and clip the top of an answer.
    assert "scrollIntoView({behavior" not in SCRIPT
    assert "function revealTop" in SCRIPT and "messages.scrollTo({top: Math.max(0, offset - 12)" in SCRIPT


def test_answer_stack_is_one_full_width_column_with_explanation_inside_the_card():
    assert "@media (min-width: 1280px)" not in CSS
    assert ".answer-stack > * { min-width: 0; max-width: 100%; }" in CSS
    assert "el('details', 'explanation')" in SCRIPT
    assert "c.append(explanation(response, events))" in SCRIPT
    assert "stack.append(explanation" not in SCRIPT
    assert "explanation-bezel" not in SCRIPT
    assert "box.open" not in SCRIPT  # collapsed by default
