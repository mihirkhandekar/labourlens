"""Keep local-corpus integration tests selectable without loading data at collection.

Corpus-marked tests also skip cleanly when the local corpus is absent (a fresh clone has the committed manifest, snapshots and
processed tables, but not the gitignored passages, raw PDFs, indexes or run logs).
"""
import pytest

from labourlens import paths


def _corpus_present() -> bool:
    return paths.PASSAGES.is_dir() and any(paths.PASSAGES.glob("*.jsonl"))


@pytest.fixture(autouse=True)
def no_paid_calls_from_tests(monkeypatch):
    """The web runner makes a scope-triage model call (D-051) that fails open without a key; a developer's real key must never turn a test into a paid call."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# These modules mix protocol integration and corpus-free boundary tests.
INDEPENDENT_MCP = {
    "test_dimension_values_cap_applies_to_the_model_contract",
    "test_screen_result_quarantines_list_items_and_refuses_instructions_elsewhere",
    "test_unlisted_server_and_missing_binary_are_refused",
    "test_hostile_list_datasets_item_is_quarantined",
    "test_hostile_instruction_in_a_scalar_field_refuses_the_whole_result",
    "test_client_allow_list_blocks_unlisted_tools_and_validates_per_tool_arguments",
    "test_server_refuses_to_start_without_a_long_enough_token",
    "test_server_refuses_a_non_loopback_host_at_start",
    "test_allow_nonloopback_flag_warns_instead_of_refusing",
    "test_client_refuses_non_loopback_or_odd_urls",
    "test_missing_and_wrong_token_get_a_bare_401",
    "test_wrong_token_fails_the_client_closed",
    "test_client_requires_the_token_in_its_environment",
    "test_bad_host_and_origin_are_rejected_even_with_a_valid_token",
    "test_no_cors_headers_and_preflight_is_not_answered",
    "test_oversized_request_body_is_rejected",
}


# Tests that build the real retrieval world (BM25 over data/passages) before reaching the code under test.
CORPUS_TESTS = {"test_agent_exp_refuses_existing_run_without_force"}


def pytest_collection_modifyitems(items):
    for item in items:
        path = item.path.as_posix()
        if (path.endswith(("mcp/test_mcp.py", "mcp/test_tools.py", "mcp/test_http.py"))
                and item.originalname not in INDEPENDENT_MCP) or "rec" in item.fixturenames or item.originalname in CORPUS_TESTS:
            item.add_marker(pytest.mark.corpus)
    if not _corpus_present():
        skip = pytest.mark.skip(reason="local corpus not present (data/passages is empty); run `labourlens fetch` and `build`")
        for item in items:
            if item.get_closest_marker("corpus"):
                item.add_marker(skip)
