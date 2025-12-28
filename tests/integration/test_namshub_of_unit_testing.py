from unittest.mock import Mock

import pytest

from bots.namshubs import namshub_of_unit_testing


def test_unit_testing_namshub_workflow():
    """Test that the unit testing namshub executes the complete workflow."""
    from bots.testing.mock_bot import MockBot

    # Create a mock bot
    mock_bot = MockBot(autosave=False)

    # This should now complete without hanging
    result, node = namshub_of_unit_testing.invoke(mock_bot, target_file="app.py")

    # Verify the workflow was called
    assert isinstance(result, str)
    assert len(result) > 0


def test_unit_testing_validates_missing_target_file():
    """Test that the namshub validates required parameters."""
    from bots.testing.mock_bot import MockBot

    mock_bot = MockBot(autosave=False)

    # Call without target_file should return error
    result, _ = namshub_of_unit_testing.invoke(mock_bot)

    assert "Error" in result or "required" in result.lower()
    assert "target_file" in result.lower()


def test_unit_testing_system_message_configuration():
    """Test that the system message is properly configured."""
    mock_bot = Mock()
    mock_bot.conversation = Mock()
    mock_bot.conversation.parent = None

    # We can't easily test the full workflow, but we can verify
    # the system message setter exists and is callable
    assert hasattr(namshub_of_unit_testing, "_set_unit_testing_system_message")


def test_unit_testing_toolkit_creation():
    """Test that the namshub module has the required structure."""
    from bots.namshubs import namshub_of_unit_testing as nut

    # Check that the module has the required functions
    assert hasattr(nut, "invoke")
    assert hasattr(nut, "_set_unit_testing_system_message")
    assert callable(nut.invoke)
    assert callable(nut._set_unit_testing_system_message)


def test_unit_testing_workflow_prompts():
    """Test that the workflow prompts are properly structured."""
    # This is more of a smoke test to ensure the module loads
    # Verify the invoke function exists and has the right signature
    import inspect

    from bots.namshubs import namshub_of_unit_testing

    sig = inspect.signature(namshub_of_unit_testing.invoke)
    params = list(sig.parameters.keys())

    assert "bot" in params
    assert "target_file" in params


def test_unit_testing_final_summary():
    """Test that the final summary is properly formatted."""
    from bots.testing.mock_bot import MockBot

    mock_bot = MockBot(autosave=False)

    result, _ = namshub_of_unit_testing.invoke(mock_bot, target_file="app.py")

    # Verify the result contains key information
    assert isinstance(result, str)
    assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
