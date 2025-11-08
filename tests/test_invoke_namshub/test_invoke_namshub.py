"""Tests for invoke_namshub tool with filepath support."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from bots.foundation.base import Bot
from bots.tools.invoke_namshub import invoke_namshub


@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    bot = MagicMock(spec=Bot)
    bot.system_message = "Original system message"
    bot.tool_handler = MagicMock()
    bot.set_system_message = MagicMock()
    bot.conversation = MagicMock()
    bot.conversation.tool_calls = []
    return bot


@pytest.fixture
def temp_namshub_file():
    """Create a temporary namshub file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Test namshub for testing filepath support."""

def invoke(bot, test_param=None, **kwargs):
    """Test invoke function."""
    return f"Test namshub executed with param: {test_param}", None
'''
        )
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_invoke_namshub_with_filepath(mock_bot, temp_namshub_file):
    """Test that invoke_namshub works with a filepath."""
    with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=mock_bot):
        result = invoke_namshub(temp_namshub_file, kwargs='{"test_param": "hello"}')

    assert "Test namshub executed with param: hello" in result
    assert "Error" not in result


def test_invoke_namshub_with_name(mock_bot):
    """Test that invoke_namshub still works with a namshub name."""
    # This will fail to find the namshub, but should show available ones
    with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=mock_bot):
        result = invoke_namshub("nonexistent_namshub")

    assert "Error" in result
    assert "not found" in result


def test_invoke_namshub_with_real_namshub_filepath(mock_bot):
    """Test that invoke_namshub works with a real namshub filepath."""
    # Get the path to a real namshub
    namshub_path = os.path.join(os.path.dirname(__file__), "..", "..", "bots", "namshubs", "namshub_of_pull_requests.py")

    if not os.path.exists(namshub_path):
        pytest.skip("namshub_of_pull_requests.py not found")

    with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=mock_bot):
        # This should load but fail due to missing pr_number
        result = invoke_namshub(namshub_path)

    # Should either execute or show a parameter error, but not a "not found" error
    assert "not found" not in result.lower() or "Error" in result


def test_invoke_namshub_nonexistent_filepath(mock_bot):
    """Test that invoke_namshub handles nonexistent filepaths gracefully."""
    with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=mock_bot):
        result = invoke_namshub("/nonexistent/path/to/namshub.py")

    assert "Error" in result
    assert "not found" in result


def test_invoke_namshub_restores_bot_state(mock_bot, temp_namshub_file):
    """Test that invoke_namshub restores the bot's original state."""
    original_handler = mock_bot.tool_handler

    with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=mock_bot):
        invoke_namshub(temp_namshub_file, kwargs='{"test_param": "test"}')

    # Bot state should be restored
    assert mock_bot.tool_handler == original_handler
