"""Unit testing namshub - creates comprehensive unit tests for bots framework code.

This namshub transforms the bot into a test generation specialist that:
1. Analyzes target file to understand what needs testing
2. Checks existing tests and runs coverage analysis to identify gaps
3. Plans test files and fixtures needed
4. Generates tests in parallel (one branch per file)
5. Verifies tests collect and run properly

The bot is equipped with code viewing, Python editing, and terminal tools
to analyze code, create tests, and verify they work.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import (
    chain_workflow,
    create_toolkit,
    format_final_summary,
    validate_required_params,
)
from bots.tools.code_tools import view, view_dir
from bots.tools.python_edit import python_edit, python_view
from bots.tools.python_execution_tool import execute_python
from bots.tools.terminal_tools import execute_powershell


def _set_unit_testing_system_message(bot: Bot, target_file: str) -> None:
    """Set specialized system message for unit test generation workflow.

    Parameters:
        bot (Bot): The bot to configure
        target_file (str): The file to create tests for
    """
    system_message = f"""You are a unit test generation specialist for the bots framework.

TARGET FILE: {target_file}

TESTING PRINCIPLES:

1. COVERAGE TARGET: 95%
   - Aim for comprehensive coverage of all code paths
   - Both happy path (works when it should) and sad path (breaks when it should)

2. TEST ORGANIZATION:
   - Tests go in tests/unit/ with subfolder structure mirroring source
   - Example: bots/flows/functional_prompts.py → tests/unit/flows/test_functional_prompts.py
   - Use pytest-style functions: def test_something():
   - NOT unittest.TestCase classes

3. MOCKING STRATEGY:
   - Use existing fixtures from tests/fixtures/ when available
   - Create new fixtures when needed
   - Mock all external dependencies (API calls, file I/O, etc.)
   - Common fixtures:
     * mock_bot_class - Mock bot for unit tests
     * mock_anthropic_class - Mock AnthropicBot class
     * real_anthropic_bot - Real bot for integration tests (DON'T USE in unit tests)

4. TEST STRUCTURE:
   - Test both happy paths and error cases
   - Use descriptive test names: test_function_name_does_what_when_condition
   - Include docstrings explaining what each test validates
   - Use arrange-act-assert pattern
   - Clean up resources in fixtures or with context managers

5. PYTEST CONVENTIONS:
   - Use @pytest.fixture for test fixtures
   - Use @pytest.mark.parametrize for multiple test cases
   - Use pytest.raises for exception testing
   - Import fixtures from tests.fixtures modules

WORKFLOW COMMANDS:

To view target file:
python_view("{target_file}")

To check existing test file:
view("tests/unit/path/to/test_file.py")

To run coverage on target file:
execute_powershell("pytest tests/unit/path/to/test_file.py --cov={target_file} --cov-report=term-missing -v")

To create/edit test file:
python_edit("tests/unit/path/to/test_file.py", code)

To verify tests collect:
execute_powershell("pytest tests/unit/path/to/test_file.py --collect-only")

To run tests:
execute_powershell("pytest tests/unit/path/to/test_file.py -v")

IMPORTANT NOTES:
- Tests must collect and run (failures are OK, collection errors are NOT)
- One branch per file to avoid file corruption
- Use branch_self to parallelize test generation across multiple files
- Report findings clearly before generating tests
"""
    bot.set_system_message(system_message.strip())


def invoke(
    bot: Bot,
    target_file: str = None,
    **kwargs
) -> Tuple[str, ConversationNode]:
    """Execute the unit testing workflow to create comprehensive tests.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        target_file (str, optional): The file to create tests for (e.g., "bots/flows/functional_prompts.py")
        **kwargs: Additional parameters (unused, for compatibility)

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # Validate required parameters
    valid, error = validate_required_params(target_file=target_file)
    if not valid:
        return (
            error + "\nUsage: invoke_namshub('namshub_of_unit_testing', target_file='bots/module/file.py')",
            bot.conversation
        )

    # BRANCH FIRST to preserve calling context
    original_conversation = bot.conversation
    bot.conversation = original_conversation._add_reply(
        content=f"Starting unit testing workflow for: {target_file}",
        role="assistant"
    )

    # Configure the bot for test generation
    create_toolkit(bot, view, view_dir, python_view, python_edit, execute_powershell, execute_python)
    _set_unit_testing_system_message(bot, target_file)

    # Define the unit testing workflow (without INSTRUCTION prefix - chain_workflow adds it)
    workflow_prompts = [
        f"""Analyze the target file and gather context.

Use branch_self to create a context-gathering branch that will:
1. View the target file: python_view("{target_file}")
2. Understand what the code does (classes, functions, dependencies)
3. Determine the test file path (mirror structure in tests/unit/)
4. Check if test file already exists
5. If exists, identify what's already tested and what's missing
6. Run coverage analysis: pytest <test_file> --cov={target_file} --cov-report=term-missing -v
7. Report back: What needs testing? What's the coverage gap? What fixtures are needed?

The branch should report findings in a clear summary format.

When the branch reports back, say CONTEXT_GATHERED.""",

        """Plan the test files and fixtures to create/modify.

Based on the context gathered, create a plan:
1. List all test files that need to be created or modified
2. List any fixture files that need to be created or modified
3. For each file, specify what will be added/changed
4. Ensure one file per branch (no parallel edits to same file)

Format your plan as a clear list:
- File: tests/unit/path/test_something.py (CREATE/MODIFY)
  Purpose: Test functions X, Y, Z
  Fixtures needed: mock_a, mock_b

When plan is complete, say PLAN_COMPLETE.""",

        """Generate tests in parallel.

Use branch_self to create tests in parallel, one branch per file from your plan.

For each branch:
- Task: Create/modify the specific test file
- Definition of done: File created with tests that collect properly
- Reporting: Report the file path and number of tests created

Example branch prompt:
"Create tests/unit/flows/test_functional_prompts.py with comprehensive tests for chain(), branch(), and prompt_while().
Include happy path and error cases. Use existing mock fixtures. Verify tests collect.
Report: file path and test count."

After all branches complete, say TESTS_GENERATED.""",

        f"""Verify all tests collect and run.

For each test file that was created/modified:
1. Verify tests collect: pytest <test_file> --collect-only
2. Run the tests: pytest <test_file> -v
3. Check coverage: pytest <test_file> --cov={target_file} --cov-report=term-missing -v

Collection errors are NOT acceptable - fix them.
Test failures are acceptable - just note them.

Report:
- Which tests collect successfully
- Which tests run (pass or fail)
- Current coverage percentage
- Any collection errors that need fixing

When verification is complete, say VERIFICATION_COMPLETE.""",

        f"""Final summary and coverage report.

Provide a comprehensive summary:
1. Target file: {target_file}
2. Test files created/modified (with paths)
3. Total number of tests created
4. Coverage achieved (vs 95% target)
5. Tests passing vs failing (failures are OK)
6. Any remaining gaps or recommendations

Format as a clear report.

Say TESTING_COMPLETE when done."""
    ]

    # Execute the workflow using chain_workflow with INSTRUCTION pattern
    responses, nodes = chain_workflow(bot, workflow_prompts)

    # Return the final response
    final_summary = format_final_summary(
        f"Unit Testing: {target_file}",
        len(responses),
        responses[-1]
    )

    return final_summary, nodes[-1]
