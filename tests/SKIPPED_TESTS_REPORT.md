# Skipped Tests Report

**Generated:** 2025-12-22 12:37:15
**Total Skipped Tests:** 36

## Executive Summary

This repository has 36 skipped tests across various test suites. The skipped tests fall into the following categories:

- **Dependencies Missing (9 tests):** Tests requiring OpenTelemetry that are conditionally skipped
- **API Keys Required (7 tests):** Tests requiring external API keys (Anthropic, Google/Gemini)
- **Flaky/Unstable (6 tests):** Tests with race conditions, LLM non-determinism, or hanging issues
- **Other (12 tests):** Various reasons including API-dependent tests and compatibility issues
- **Known Bugs/Issues (1 test):** Test exposing an infinite loop bug in dill serialization
- **Manual/Interactive (1 test):** Test requiring user input that's difficult to mock

---

## 1. Dependencies Missing (9 tests)

These tests are skipped when OpenTelemetry is not installed. This is appropriate for optional dependencies.

### Files Affected:
- `tests/integration/test_observability_integration.py` (1 test)
- `tests/unit/test_observability/test_callbacks.py` (8 tests)

### Tests:

1. **tests/integration/test_observability_integration.py:38** - `Unknown`
   - Reason: OpenTelemetry not available

2. **tests/unit/test_observability/test_callbacks.py:76** - `test_on_respond_start_adds_event`
   - Reason: OpenTelemetry not available

3. **tests/unit/test_observability/test_callbacks.py:92** - `test_on_respond_complete_adds_event`
   - Reason: OpenTelemetry not available

4. **tests/unit/test_observability/test_callbacks.py:107** - `test_on_respond_error_records_exception`
   - Reason: OpenTelemetry not available

5. **tests/unit/test_observability/test_callbacks.py:121** - `test_on_api_call_complete_sets_attributes`
   - Reason: OpenTelemetry not available

6. **tests/unit/test_observability/test_callbacks.py:136** - `test_on_tool_start_adds_event`
   - Reason: OpenTelemetry not available

7. **tests/unit/test_observability/test_callbacks.py:151** - `test_graceful_degradation_no_span`
   - Reason: OpenTelemetry not available

8. **tests/unit/test_observability/test_callbacks.py:162** - `test_graceful_degradation_span_not_recording`
   - Reason: OpenTelemetry not available

9. **tests/unit/test_observability/test_callbacks.py:273** - `test_otel_callbacks_handle_missing_metadata_keys`
   - Reason: OpenTelemetry not available

### Recommendation:
✅ **No action needed.** These are properly conditionally skipped for optional dependencies.

---

## 2. API Keys Required (7 tests)

Tests requiring external API keys that may not be available in all environments.

### Files Affected:
- `tests/e2e/test_namshub_of_unit_testing_real.py` (2 tests)
- `tests/integration/test_save_load_gemini.py` (4 tests)
- `tests/unit/test_web_tool_integration.py` (1 test)

### Tests:

1. **tests/e2e/test_namshub_of_unit_testing_real.py:15** - `test_unit_testing_namshub_completes_workflow`
   - Reason: Requires ANTHROPIC_API_KEY environment variable

2. **tests/e2e/test_namshub_of_unit_testing_real.py:59** - `test_unit_testing_namshub_handles_complex_code`
   - Reason: Requires ANTHROPIC_API_KEY environment variable

3. **tests/integration/test_save_load_gemini.py:248** - `test_real_conversation_and_save_load`
   - Reason: Conditional: not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY")

4. **tests/integration/test_save_load_gemini.py:276** - `test_real_tool_usage_and_persistence`
   - Reason: Conditional: not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY")

5. **tests/integration/test_save_load_gemini.py:319** - `test_real_error_handling`
   - Reason: Conditional: not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY")

6. **tests/integration/test_save_load_gemini.py:334** - `test_multiple_conversation_turns`
   - Reason: Conditional: not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY")

7. **tests/unit/test_web_tool_integration.py:194** - `test_manual_web_search_inspection`
   - Reason: Manual inspection test - run separately with real API key

### Recommendation:
✅ **Acceptable for CI.** Consider running these in a separate nightly test suite with API keys available.

---

## 3. Flaky/Unstable (6 tests)

Tests that fail intermittently due to race conditions, LLM non-determinism, or other stability issues.

### Files Affected:
- `tests/integration/test_observability_integration.py` (1 test)
- `tests/integration/test_save_load_anthropic.py` (1 test)
- `tests/integration/test_powershell_tool/test_terminal_timeout.py` (1 test)
- `tests/integration/test_powershell_tool/test_terminal_timeout_advanced.py` (1 test)
- `tests/integration/test_python_edit/test_empty_string_deletion.py` (1 test)
- `tests/unit/test_save_load_openai.py` (1 test)

### Tests:

1. **tests/integration/test_observability_integration.py:197** - `test_callbacks_integration`
   - Issue: Test hangs - needs investigation
   - ⚠️ **Priority: HIGH** - Hanging tests are problematic

2. **tests/integration/test_save_load_anthropic.py:1012** - `test_branch_self_tool_execution_vs_response_integration`
   - Issue: Test is flaky - LLM doesn
   - 💡 **Suggestion:** Use mock LLM or more deterministic prompts

3. **tests/integration/test_powershell_tool/test_terminal_timeout.py:442** - `test_process_communication_health`
   - Issue: Flaky test - race condition in process initialization in CI
   - 💡 **Suggestion:** Add retry logic or increase timeouts

4. **tests/integration/test_powershell_tool/test_terminal_timeout_advanced.py:96** - `test_error_recovery`
   - Issue: Flaky test - PowerShell session cleanup issues in CI
   - 💡 **Suggestion:** Improve cleanup with explicit teardown

5. **tests/integration/test_python_edit/test_empty_string_deletion.py:265** - `test_empty_string_preserves_file_structure`
   - Issue: Flaky in CI due to temp directory race conditions - see issue #XXX
   - 💡 **Suggestion:** Add retry logic or increase timeouts

6. **tests/unit/test_save_load_openai.py:400** - `test_mixed_tool_sources`
   - Issue: Test is flaky - LLM doesn
   - 💡 **Suggestion:** Use mock LLM or more deterministic prompts

### Recommendation:
⚠️ **Action needed.** These tests should be fixed or refactored to be more stable.

---

## 4. Known Bugs/Issues (1 test)

Tests that expose actual bugs in the codebase.

### Files Affected:
- `tests/e2e/test_bot_picklability.py` (1 test)

### Tests:

1. **tests/e2e/test_bot_picklability.py:189** - `test_deepcopy_functionality`
   - Issue: Test crashes due to infinite loop in dill serialization during bot.respond() quicksave
   - 🐛 **Priority: HIGH** - This indicates a real bug that should be fixed

### Recommendation:
🔴 **Critical.** This test exposes a real bug that should be investigated and fixed.

---

## 5. Manual/Interactive (1 test)

Tests requiring user interaction that are difficult to automate.

### Files Affected:
- `tests/unit/test_system_handler.py` (1 test)

### Tests:

1. **tests/unit/test_system_handler.py:136** - `test_add_tool_no_args_returns_string`
   - Issue: add_tool() uses interactive input() which is difficult to mock in this context
   - 💡 **Refactor:** Mock the input() function or refactor the code to accept input as a parameter

### Recommendation:
💡 **Refactor.** Mock the input() function or refactor the code to accept input as a parameter.

---

## 6. Other (12 tests)

Various other reasons for skipping tests.

### Files Affected:
- `tests/e2e/test_auto_stache.py` (1 test)
- `tests/e2e/test_branch_self_recursive.py` (1 test)
- `tests/integration/test_save_load_anthropic.py` (2 tests)
- `tests/integration/test_save_load_gemini.py` (2 tests)
- `tests/integration/test_python_edit/test_python_edit.py` (1 test)
- `tests/test_invoke_namshub/test_invoke_namshub.py` (1 test)
- `tests/unit/test_python_tools.py` (1 test)
- `tests/unit/test_web_tool_integration.py` (1 test)
- `tests/unit/test_cli/test_fp_wizard_complete.py` (2 tests)

### Tests:

1. **tests/e2e/test_auto_stache.py:141** - `Unknown`
   - Reason: No reason provided

2. **tests/e2e/test_branch_self_recursive.py:163** - `test_branch_positioning_after_recursive_load`
   - Reason: Test requires real API calls after save/load which can fail with OpenAI validation errors

3. **tests/integration/test_save_load_anthropic.py:913** - `Unknown`
   - Reason: No reason provided

4. **tests/integration/test_save_load_anthropic.py:967** - `Unknown`
   - Reason: No reason provided

5. **tests/integration/test_save_load_gemini.py:219** - `Unknown`
   - Reason: No reason provided

6. **tests/integration/test_save_load_gemini.py:229** - `Unknown`
   - Reason: No reason provided

7. **tests/integration/test_python_edit/test_python_edit.py:519** - `Unknown`
   - Reason: No reason provided

8. **tests/test_invoke_namshub/test_invoke_namshub.py:71** - `test_invoke_namshub_nonexistent_filepath`
   - Reason: No reason provided

9. **tests/unit/test_python_tools.py:901** - `test_execute_python_code_basic`
   - Reason: Using private implementation

10. **tests/unit/test_web_tool_integration.py:200** - `Unknown`
   - Reason: No reason provided

11. **tests/unit/test_cli/test_fp_wizard_complete.py:212** - `test_fp_par_branch_wizard`
   - Reason: par_branch uses parallel execution with Bot.save/load

12. **tests/unit/test_cli/test_fp_wizard_complete.py:247** - `test_fp_par_branch_while_wizard`
   - Reason: par_branch_while uses parallel execution with Bot.save/load

### Recommendation:
🔍 **Review individually.** Some may need refactoring, others may be legitimately skipped.

---

## Priority Actions

### 🔴 High Priority
1. **Fix hanging test:** `test_callbacks_integration` (test_observability_integration.py:197)
2. **Fix infinite loop bug:** `test_deepcopy_functionality` (test_bot_picklability.py:189)

### 🟡 Medium Priority
3. **Stabilize flaky tests:** 4 tests with race conditions or LLM non-determinism
4. **Mock interactive input:** `test_add_tool_no_args_returns_string` (test_system_handler.py:136)

### 🟢 Low Priority
5. **Review "Other" category:** 12 tests with various skip reasons

---

## Statistics by Test Type

| Test Directory | Skipped Tests |
|----------------|---------------|
| tests/e2e/ | 5 |
| tests/integration/ (other) | 7 |
| tests/integration/test_powershell_tool/ | 2 |
| tests/integration/test_python_edit/ | 1 |
| tests/test_invoke_namshub/ | 1 |
| tests/unit/ (other) | 2 |
| tests/unit/test_cli/ | 2 |
| tests/unit/test_observability/ | 9 |
| tests/unit/test_web_tool_integration/ | 1 |

---

## Recommendations Summary

1. **Keep conditionally skipped tests** for optional dependencies (OpenTelemetry, API keys)
2. **Fix or stabilize** the 6 flaky tests to improve CI reliability
3. **Investigate and fix** the infinite loop bug in dill serialization
4. **Investigate and fix** the hanging test in observability integration
5. **Refactor interactive tests** to be mockable
6. **Consider a nightly test suite** for API-dependent tests with credentials

---

## Changes

### 2025-12-22
- **Removed 3 "Not Implemented" tests** from `tests/integration/test_bots.py`:
  - `TestBaseBot::test_batch_respond`
  - `TestGPTBot::test_batch_respond`
  - `TestAnthropicBot::test_parallel_respond`
- **Reason:** Plans changed, batch/parallel features not planned for implementation
- **New total:** 36 skipped tests (down from 39)
