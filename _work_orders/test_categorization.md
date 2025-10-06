# Test Suite Categorization Analysis

**Date**: 2025-01-07
**Work Order**: WO012_Test_Suite_Organization
**Total Files**: 90
**Total Tests**: 775

## Summary Statistics

| Category | File Count | Percentage |
|----------|------------|------------|
| Unit | 33 | 36.7% |
| Integration | 31 | 34.4% |
| E2E | 26 | 28.9% |
| **Total** | **90** | **100%** |

## Categorization Details

### Unit Tests (33 files)
Tests that are fast, isolated, and use mocks. No external API calls or file I/O.

| File | Tests | Description |
|------|-------|-------------|
| `test_add_tools_openai.py` | 13 | Unit tests |
| `test_cli\test_broadcast_to_leaves.py` | 2 | Unit tests |
| `test_cli\test_fp_callbacks.py` | 5 | Mocked unit tests |
| `test_cli\test_fp_wizard_complete.py` | 10 | Mocked unit tests |
| `test_cli\test_recombine_removal.py` | 2 | Mocked unit tests |
| `test_cli\test_save_auto_commands.py` | 6 | Mocked unit tests |
| `test_decorators.py` | 4 | Unit tests |
| `test_dynamic_execution.py` | 2 | Unit tests |
| `test_fp\test_fp_conditions.py` | 15 | Mocked unit tests |
| `test_fp\test_par_dispatch.py` | 3 | Mocked unit tests |
| `test_functions.py` | 0 | Helper/utility functions |
| `test_helpers.py` | 6 | Helper/utility functions |
| `test_insert.py` | 0 | Unit tests |
| `test_mock_bot.py` | 6 | Mocked unit tests |
| `test_nested.py` | 0 | Unit tests |
| `test_oaibot.py` | 3 | Unit tests |
| `test_observability\test_backward_compatibility.py` | 12 | Mocked unit tests |
| `test_observability\test_bot_tracing_unit.py` | 12 | Mocked unit tests |
| `test_observability\test_tracing_config.py` | 16 | Observability/tracing tests |
| `test_observability\test_tracing_setup.py` | 18 | Mocked unit tests |
| `test_patch_edit.py` | 42 | Unit tests |
| `test_pr_comment_parser.py` | 8 | Mocked unit tests |
| `test_python_edit\test_functions.py` | 0 | Helper/utility functions |
| `test_python_tools.py` | 56 | Unit tests |
| `test_replace_behavior.py` | 0 | Unit tests |
| `test_save_load_openai.py` | 13 | Unit tests |
| `test_self_tools.py` | 13 | Mocked unit tests |
| `test_tool_handler.py` | 11 | Tool handler logic |
| `test_tool_handler_comprehensive.py` | 10 | Tool handler logic |
| `test_toolify.py` | 22 | Tool conversion logic |
| `test_toolify_integration.py` | 11 | Tool conversion logic |
| `test_web_tool.py` | 10 | Mocked unit tests |
| `test_web_tool_integration.py` | 11 | Mocked unit tests |

### Integration Tests (31 files)
Tests with real API calls, file operations, or tool integrations.

| File | Tests | Description |
|------|-------|-------------|
| `test_add_tools.py` | 13 | Real API bot interactions |
| `test_basic.py` | 9 | Real API bot interactions |
| `test_bots.py` | 5 | Bot save/load operations |
| `test_cli\test_prompt_naming.py` | 2 | Real API bot interactions |
| `test_cli\test_prompt_naming_fixed.py` | 1 | Real API bot interactions |
| `test_code_tools.py` | 12 | Code tools tests |
| `test_comprehensive_helpers.py` | 1 | Bot save/load operations |
| `test_helper_preservation.py` | 1 | Bot save/load operations |
| `test_powershell_tool\test_terminal_timeout.py` | 14 | PowerShell tool tests |
| `test_powershell_tool\test_terminal_timeout_advanced.py` | 11 | PowerShell tool tests |
| `test_powershell_tool\test_terminal_tools_production_cases.py` | 11 | PowerShell tool tests |
| `test_python_edit\test_all_fixes.py` | 0 | Python edit tool tests |
| `test_python_edit\test_class_replace.py` | 1 | Python edit tool tests |
| `test_python_edit\test_comprehensive_failure_cases.py` | 1 | Python edit tool tests |
| `test_python_edit\test_empty_string_deletion.py` | 10 | Python edit tool tests |
| `test_python_edit\test_file_level.py` | 0 | Python edit tool tests |
| `test_python_edit\test_file_level_fixed.py` | 0 | Python edit tool tests |
| `test_python_edit\test_import_dedup_fixed.py` | 0 | Python edit tool tests |
| `test_python_edit\test_import_duplication.py` | 0 | Python edit tool tests |
| `test_python_edit\test_insert.py` | 0 | Python edit tool tests |
| `test_python_edit\test_insert_after.py` | 0 | Python edit tool tests |
| `test_python_edit\test_method_replacement_bugs.py` | 1 | Python edit tool tests |
| `test_python_edit\test_nested.py` | 0 | Python edit tool tests |
| `test_python_edit\test_python_edit.py` | 56 | Python edit tool tests |
| `test_python_edit\test_python_edit_edge_cases.py` | 0 | Python edit tool tests |
| `test_python_edit\test_python_view.py` | 35 | Python edit tool tests |
| `test_python_edit\test_replace_behavior.py` | 0 | Python edit tool tests |
| `test_save_load_anthropic.py` | 32 | Bot save/load operations |
| `test_save_load_debug.py` | 1 | Bot save/load operations |
| `test_save_load_gemini.py` | 12 | Bot save/load operations |
| `test_save_load_matrix.py` | 2 | Real API bot interactions |

### E2E Tests (26 files)
End-to-end workflow tests including CLI and functional prompts.

| File | Tests | Description |
|------|-------|-------------|
| `test_cli\test_auto_stache.py` | 15 | CLI/subprocess workflows |
| `test_cli\test_branch_self_integration.py` | 4 | CLI/subprocess workflows |
| `test_cli\test_broadcast_fp_cli.py` | 12 | CLI/subprocess workflows |
| `test_cli\test_broadcast_fp_comprehensive.py` | 10 | CLI/subprocess workflows |
| `test_cli\test_broadcast_fp_wizard_complete.py` | 10 | Functional prompt workflows |
| `test_cli\test_cli.py` | 33 | CLI/subprocess workflows |
| `test_cli\test_cli_and_while_functions.py` | 7 | CLI/subprocess workflows |
| `test_cli\test_cli_load.py` | 9 | CLI/subprocess workflows |
| `test_cli\test_cli_prompt_functionality.py` | 5 | CLI/subprocess workflows |
| `test_cli\test_cli_terminal_tool_integration.py` | 5 | CLI/subprocess workflows |
| `test_cli\test_combine_leaves.py` | 5 | CLI/subprocess workflows |
| `test_cli\test_keyboard_interrupt_handling.py` | 5 | CLI/subprocess workflows |
| `test_cli\test_leaf_command.py` | 8 | CLI/subprocess workflows |
| `test_cli\test_new_functionality.py` | 5 | CLI/subprocess workflows |
| `test_cli\test_prompt_management.py` | 25 | CLI/subprocess workflows |
| `test_cli\test_quiet_duplicate.py` | 4 | CLI/subprocess workflows |
| `test_cli\test_quiet_fix_verification.py` | 1 | CLI/subprocess workflows |
| `test_cli\test_wizard_debug.py` | 5 | CLI/subprocess workflows |
| `test_cli_tool_crash_bug.py` | 3 | CLI/subprocess workflows |
| `test_cli_tool_crash_bug_fix.py` | 2 | CLI/subprocess workflows |
| `test_fp\test_broadcast_fp.py` | 10 | Functional prompt workflows |
| `test_fp\test_cli_style_callback.py` | 1 | CLI/subprocess workflows |
| `test_fp\test_par_branch.py` | 5 | Functional prompt workflows |
| `test_fp\test_par_branch_while_callable_fix.py` | 3 | CLI/subprocess workflows |
| `test_powershell_tool\test_terminal_tools.py` | 43 | CLI/subprocess workflows |
| `test_specific_helper_bug.py` | 1 | CLI/subprocess workflows |

## Shared Fixture Opportunities

Based on analysis of test files, the following fixtures should be extracted to `tests/fixtures/`:

### 1. Bot Fixtures (`bot_fixtures.py`)
- **mock_bot_class**: Mock bot class for unit tests (used in 5+ files)
- **mock_anthropic_class**: Mock Anthropic bot (used in 2+ files)
- **real_anthropic_bot**: Real AnthropicBot instance for integration tests
- **real_openai_bot**: Real OpenAIBot instance for integration tests
- **real_gemini_bot**: Real GeminiBot instance for integration tests

### 2. File Fixtures (`file_fixtures.py`)
- **temp_test_file**: Create temporary test files (used extensively)
- **temp_test_dir**: Create temporary test directories
- **cleanup_temp_files**: Auto-cleanup fixture for temp files

### 3. Mock Fixtures (`mock_fixtures.py`)
- **mock_input**: Mock user input (used in 13+ files)
- **mock_print**: Mock print output (used in 3+ files)
- **mock_bot_load**: Mock bot loading (used in multiple files)

### 4. Tool Fixtures (`tool_fixtures.py`)
- **mock_tool_response**: Mock tool execution responses
- **test_tool_function**: Sample tool function for testing
- **tool_schema_validator**: Validate tool schemas

### 5. Environment Fixtures (`env_fixtures.py`)
- **clean_otel_env**: Clean OpenTelemetry environment (used in 3+ files)
- **mock_api_keys**: Mock API key environment variables

## Migration Notes

### Files Requiring Special Attention
1. **test_cli/** directory: Many CLI tests, need careful categorization
2. **test_python_edit/** directory: Large integration test suite
3. **test_fp/** directory: Functional prompt tests (mostly E2E)

### Import Path Updates Required
All moved tests will need import path updates:
- From: `from tests.conftest import ...`
- To: `from tests.fixtures.xxx_fixtures import ...`

### Marker Application
Each test file should have appropriate markers:
- Unit tests: `@pytest.mark.unit`
- Integration tests: `@pytest.mark.integration`
- E2E tests: `@pytest.mark.e2e`
- Slow tests: `@pytest.mark.slow`
- Flaky tests: `@pytest.mark.flaky(reruns=3)`

