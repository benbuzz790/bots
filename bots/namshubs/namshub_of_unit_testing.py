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


def invoke(bot: Bot, target_file: str | None = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the unit testing workflow to create comprehensive tests.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        target_file (str): The file to create tests for
        **kwargs: Additional keyword arguments

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    if target_file is None:
        return "Error: target_file is required", bot.conversation

    # Execute the workflow
    response = bot.respond(f"Create comprehensive unit tests for {target_file}")

    return response, bot.conversation
