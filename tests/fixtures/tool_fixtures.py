"""Tool-related fixtures for testing.

Provides fixtures for testing tool functionality and schemas.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_tool_response():
    """Mock tool execution response.

    Returns a mock that simulates tool execution results.

    Usage:
        def test_something(mock_tool_response):
            mock_tool_response.return_value = "Tool executed successfully"
            # Use in tests that need tool responses
    """
    return Mock(return_value="Mock tool response")


@pytest.fixture
def test_tool_function():
    """Sample tool function for testing.

    Returns a simple tool function that can be used in tests.

    Usage:
        def test_something(test_tool_function):
            result = test_tool_function("input")
            assert result == "Processed: input"
    """

    def sample_tool(input_str: str) -> str:
        """Sample tool for testing.

        Parameters:
        - input_str (str): Input string to process

        Returns:
        str: Processed result
        """
        return f"Processed: {input_str}"

    return sample_tool


@pytest.fixture
def tool_schema_validator():
    """Validator for tool schemas.

    Returns a function that validates tool schema structure.

    Usage:
        def test_something(tool_schema_validator):
            schema = {...}
            is_valid = tool_schema_validator(schema)
            assert is_valid
    """

    def validate_schema(schema):
        """Validate that a schema has required fields."""
        required_fields = ["name", "description"]
        return all(field in schema for field in required_fields)

    return validate_schema


@pytest.fixture
def mock_tool_execution():
    """Mock tool execution context.

    Returns a mock that simulates the tool execution environment.
    """
    mock_exec = Mock()
    mock_exec.execute = Mock(return_value="Execution result")
    mock_exec.validate = Mock(return_value=True)
    return mock_exec
