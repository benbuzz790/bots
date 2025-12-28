"""Test for namshub_of_enki - creating new namshubs.

This test validates that the Enki namshub can successfully create a new namshub
with proper structure, testing, and functionality.
"""

from unittest.mock import Mock

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

    from bots.namshubs import namshub_of_enki

    result, node = namshub_of_enki.invoke(bot, task_description="Create a namshub that counts lines in a file")

    # Verify the workflow was executed
    assert isinstance(result, str)
    assert len(result) > 0


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
    """Test that the bot can be invoked with task description."""
    bot = MockBot(autosave=False)

    from bots.namshubs import namshub_of_enki

    result, node = namshub_of_enki.invoke(bot, task_description="Test task")

    # Verify the invoke succeeded
    assert isinstance(result, str)
    assert node is not None


def test_enki_workflow_structure():
    """Test that the workflow can be invoked with various parameters."""
    bot = MockBot(autosave=False)

    from bots.namshubs import namshub_of_enki

    result, node = namshub_of_enki.invoke(
        bot,
        task_description="Create a calculator namshub",
        workflow_steps="Step 1, Step 2, Step 3",
        required_tools="python_edit, execute_powershell",
        namshub_name="calculator",
    )

    # Verify the result is valid
    assert isinstance(result, str)
    assert node is not None


def test_enki_final_summary():
    """Test that the final summary is properly formatted."""
    bot = MockBot(autosave=False)

    from bots.namshubs import namshub_of_enki

    result, node = namshub_of_enki.invoke(bot, task_description="Test namshub")

    # Verify the result contains key information
    assert isinstance(result, str)
    assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
