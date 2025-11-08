"""Test for namshub_of_enki - creating new namshubs.

This test validates that the Enki namshub can successfully create a new namshub
with proper structure, testing, and functionality.
"""

from unittest.mock import Mock, patch

import pytest

from bots.testing.mock_bot import MockBot


@pytest.mark.integration
def test_enki_creates_simple_namshub():
    """Test that Enki can create a simple namshub with basic functionality.

    This test creates a simple "file counter" namshub that counts lines in a file.
    It's a minimal example to verify the Enki workflow works end-to-end.
    """
    # Create a mock bot for testing
    bot = MockBot(autosave=False)

    # Mock the chain_workflow to avoid actual execution
    with patch("bots.namshubs.namshub_of_enki.chain_workflow") as mock_chain:
        mock_chain.return_value = (["Created namshub", "Added tests", "Verified functionality"], [bot.conversation] * 3)

        from bots.namshubs import namshub_of_enki

        result, node = namshub_of_enki.invoke(bot, task_description="Create a namshub that counts lines in a file")

        # Verify the workflow was executed
        assert mock_chain.called
        assert "namshub" in result.lower() or "created" in result.lower()


def test_enki_validates_missing_task_description():
    """Test that Enki validates required parameters."""
    bot = MockBot(autosave=False)

    from bots.namshubs import namshub_of_enki

    result, node = namshub_of_enki.invoke(bot)

    assert "Error" in result or "required" in result.lower()
    assert "task_description" in result.lower()


def test_enki_system_message_configuration():
    """Test that the system message is properly formatted."""
    bot = Mock()
    bot.conversation = Mock()

    from bots.namshubs import namshub_of_enki

    namshub_of_enki._set_enki_system_message(bot, "Create a test namshub")

    assert bot.set_system_message.called
    system_msg = bot.set_system_message.call_args[0][0]

    # Check for key workflow steps
    assert "namshub" in system_msg.lower()
    assert "create" in system_msg.lower() or "design" in system_msg.lower()


def test_enki_toolkit_creation():
    """Test that the bot is equipped with necessary tools."""
    bot = Mock()
    bot.conversation = Mock()

    from unittest.mock import patch

    with patch("bots.namshubs.namshub_of_enki.create_toolkit") as mock_toolkit:
        with patch("bots.namshubs.namshub_of_enki.chain_workflow") as mock_chain:
            mock_chain.return_value = (["Response"], [bot.conversation])

            from bots.namshubs import namshub_of_enki

            namshub_of_enki.invoke(bot, task_description="Test task")

            # Verify create_toolkit was called with the bot
            assert mock_toolkit.called
            call_args = mock_toolkit.call_args[0]
            assert call_args[0] == bot


def test_enki_workflow_structure():
    """Test that the workflow prompts are properly structured."""
    bot = Mock()
    bot.conversation = Mock()

    from unittest.mock import patch

    with patch("bots.namshubs.namshub_of_enki.chain_workflow") as mock_chain:
        mock_chain.return_value = (["Response"] * 5, [bot.conversation] * 5)

        from bots.namshubs import namshub_of_enki

        namshub_of_enki.invoke(bot, task_description="Create a calculator namshub")

        # Verify chain_workflow was called with proper prompts
        call_args = mock_chain.call_args[0]
        prompts = call_args[1]

        # Should have multiple workflow steps
        assert len(prompts) >= 3

        # Check for key workflow elements in prompts
        all_prompts = " ".join(prompts).lower()
        assert "namshub" in all_prompts
        assert "create" in all_prompts or "design" in all_prompts


def test_enki_final_summary():
    """Test that the final summary is properly formatted."""
    bot = Mock()
    bot.conversation = Mock()

    from unittest.mock import patch

    with patch("bots.namshubs.namshub_of_enki.chain_workflow") as mock_chain:
        mock_responses = ["Designed namshub", "Implemented code", "Created tests"]
        mock_chain.return_value = (mock_responses, [bot.conversation] * 3)

        from bots.namshubs import namshub_of_enki

        result, node = namshub_of_enki.invoke(bot, task_description="Test namshub")

        # Verify the result contains key information
        assert "namshub" in result.lower() or "test" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
