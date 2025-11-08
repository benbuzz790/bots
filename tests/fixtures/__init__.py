"""Shared test fixtures for the bots test suite.

This package contains reusable fixtures organized by category:
- bot_fixtures: Bot creation and mocking
- file_fixtures: Temporary file/directory handling
- mock_fixtures: Common mocks (input, print, etc.)
- tool_fixtures: Tool-related fixtures
- env_fixtures: Environment setup/cleanup

Test namshubs for testing namshub invocation:
- namshub_of_no_op: Does nothing (simplest case)
- namshub_of_echo: Echoes back a parameter
- namshub_of_state_change: Modifies bot state
- namshub_of_tool_use: Uses tools
- namshub_of_simple_workflow: Executes a workflow
- namshub_of_error: Raises errors for testing

Note: Test namshubs are NOT auto-imported to avoid issues with pytest collection.
Import them explicitly in your tests:
    from tests.fixtures import namshub_of_no_op
"""
