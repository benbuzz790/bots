"""Bot-related fixtures for testing.

Provides both mock and real bot instances for different test scenarios.
"""
import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_bot_class():
    """Mock bot class for unit tests.

    Returns a mock bot with common methods (respond, add_tools, save, load).
    Used extensively in unit tests to avoid real API calls.
    """
    mock_bot = Mock()
    mock_bot.respond = Mock(return_value="Mock response")
    mock_bot.add_tools = Mock()
    mock_bot.save = Mock()
    mock_bot.load = Mock()
    mock_bot.conversation = Mock()
    mock_bot.tools = []
    return mock_bot


@pytest.fixture
def mock_anthropic_class():
    """Mock AnthropicBot class for unit tests.

    Returns a mock of the AnthropicBot class itself (not an instance).
    Useful for testing code that instantiates bots.
    """
    mock_class = MagicMock()
    mock_instance = Mock()
    mock_instance.respond = Mock(return_value="Mock Anthropic response")
    mock_instance.conversation = Mock()
    mock_class.return_value = mock_instance
    return mock_class


@pytest.fixture
def real_anthropic_bot():
    """Real AnthropicBot instance for integration tests.

    Creates an actual bot instance that makes real API calls.
    Use sparingly and only in integration tests.
    """
    from bots import AnthropicBot
    return AnthropicBot()


@pytest.fixture
def real_openai_bot():
    """Real OpenAIBot instance for integration tests.

    Creates an actual bot instance that makes real API calls.
    Use sparingly and only in integration tests.
    """
    from bots import OpenAIBot
    return OpenAIBot()


@pytest.fixture
def real_gemini_bot():
    """Real GeminiBot instance for integration tests.

    Creates an actual bot instance that makes real API calls.
    Use sparingly and only in integration tests.
    """
    from bots import GeminiBot
    return GeminiBot()
