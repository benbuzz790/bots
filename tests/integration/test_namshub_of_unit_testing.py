from unittest.mock import Mock, patch

import pytest

from bots.namshubs import namshub_of_unit_testing


def test_unit_testing_namshub_workflow():
    """Test that the unit testing namshub executes the complete workflow."""
    # Create a mock bot
    mock_bot = Mock()
    mock_bot.conversation = Mock()
    mock_bot.conversation.parent = None
    mock_bot.conversation._add_reply = Mock(return_value=mock_bot.conversation)

    # Mock the chain_workflow to avoid actual execution
    with patch("bots.namshubs.namshub_of_unit_testing.chain_workflow") as mock_chain:
        mock_chain.return_value = (
            ["Context gathered", "Plan complete", "Tests generated", "Verification complete", "Summary"],
            [mock_bot.conversation] * 5,
        )

        # This should now complete without hanging
        result, node = namshub_of_unit_testing.invoke(mock_bot, target_file="app.py")

        # Verify the workflow was called
        assert mock_chain.called
        assert "app.py" in result or "Unit Testing" in result


def test_unit_testing_validates_missing_target_file():
    """Test that the namshub validates required parameters."""
    mock_bot = Mock()
    mock_bot.conversation = Mock()

    # Call without target_file should return error
    result, _ = namshub_of_unit_testing.invoke(mock_bot)

    assert "Missing required parameter" in result or "target_file" in result


def test_unit_testing_system_message_configuration():
    """Test that the system message is properly configured."""
    mock_bot = Mock()
    mock_bot.conversation = Mock()
    mock_bot.conversation.parent = None

    # We can't easily test the full workflow, but we can verify
    # the system message setter exists and is callable
    assert hasattr(namshub_of_unit_testing, "_set_unit_testing_system_message")


def test_unit_testing_toolkit_creation():
    """Test that the toolkit is properly created with required tools."""
    mock_bot = Mock()
    mock_bot.conversation = Mock()

    # Verify the namshub imports the required tools
    from bots.namshubs import namshub_of_unit_testing as nut

    # Check that the module has access to the tools it needs
    assert hasattr(nut, "execute_powershell")
    assert hasattr(nut, "execute_python")
    assert hasattr(nut, "view")
    assert hasattr(nut, "view_dir")
    assert hasattr(nut, "python_view")
    assert hasattr(nut, "python_edit")


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
    mock_bot = Mock()
    mock_bot.conversation = Mock()
    mock_bot.conversation.parent = None
    mock_bot.conversation._add_reply = Mock(return_value=mock_bot.conversation)

    # Mock chain_workflow to avoid hanging
    with patch("bots.namshubs.namshub_of_unit_testing.chain_workflow") as mock_chain:
        mock_chain.return_value = (["Summary of work"], [mock_bot.conversation])

        result, _ = namshub_of_unit_testing.invoke(mock_bot, target_file="app.py")

        # Verify the result contains key information
        assert "app.py" in result or "Unit Testing" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
