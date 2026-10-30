"""Keep local-corpus integration tests selectable without loading data at collection."""
import pytest


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


def pytest_collection_modifyitems(items):
    for item in items:
        path = item.path.as_posix()
        if (path.endswith(("mcp/test_mcp.py", "mcp/test_tools.py", "mcp/test_http.py"))
                and item.originalname not in INDEPENDENT_MCP) or "rec" in item.fixturenames:
            item.add_marker(pytest.mark.corpus)
