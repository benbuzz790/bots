"""Fixtures for CLI tests."""

import pytest


@pytest.fixture
def temp_prompts_file(tmp_path):
    """Create a temporary prompts file for testing."""
    prompts_file = tmp_path / "test_prompts.json"
    return prompts_file
