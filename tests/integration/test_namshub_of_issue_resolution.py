"""Test for namshub_of_issue_resolution - resolving GitHub issues.

This test validates that the issue resolution namshub can successfully:
1. Read and analyze an issue
2. Create a feature branch
3. Implement a solution
4. Create tests
5. Create a PR
6. Invoke the PR namshub
"""

from unittest.mock import Mock, patch

import pytest

from bots import AnthropicBot
from bots.foundation.base import Bot
from bots.namshubs import namshub_of_issue_resolution
from bots.testing.mock_bot import MockBot


@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    bot = Mock(spec=Bot)
    bot.conversation = Mock()
    bot.conversation.parent = None
    return bot


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository structure for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Create some sample files
    (repo_dir / "main.py").write_text("def main():\n    pass\n")
    (repo_dir / "README.md").write_text("# Test Project\n")

    return repo_dir


def test_invoke_without_issue_number(mock_bot):
    """Test that invoke fails gracefully without an issue number."""
    result, node = namshub_of_issue_resolution.invoke(mock_bot)

    assert "Error" in result or "required" in result.lower()
    assert "issue_number" in result.lower()


def test_invoke_with_issue_number(mock_bot):
    """Test that invoke accepts an issue number."""
    # Mock the chain_workflow to avoid actual execution
    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_chain.return_value = (["response"], [mock_bot.conversation])

        result, node = namshub_of_issue_resolution.invoke(mock_bot, issue_number="123")

        # Should not contain error message
        assert "Error" not in result or "required" not in result.lower()


def test_system_message_configuration(mock_bot):
    """Test that the system message is properly configured."""
    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_chain.return_value = (["response"], [mock_bot.conversation])

        namshub_of_issue_resolution.invoke(mock_bot, issue_number="456")

        # Verify set_system_message was called
        mock_bot.set_system_message.assert_called_once()
        system_msg = mock_bot.set_system_message.call_args[0][0]

        # Check that the system message contains key workflow elements
        assert "issue #456" in system_msg.lower()
        assert "gh issue view" in system_msg.lower()


def test_toolkit_creation(mock_bot):
    """Test that the bot is equipped with necessary tools."""
    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        with patch("bots.namshubs.namshub_of_issue_resolution.create_toolkit") as mock_toolkit:
            mock_chain.return_value = (["response"], [mock_bot.conversation])

            namshub_of_issue_resolution.invoke(mock_bot, issue_number="789")

            # Verify create_toolkit was called with the bot and expected tools
            mock_toolkit.assert_called_once()
            call_args = mock_toolkit.call_args[0]
            assert call_args[0] == mock_bot
            # Should include branch_self, execute_powershell, execute_python, view, view_dir, python_view, python_edit
            assert len(call_args) > 1


def test_workflow_execution(mock_bot):
    """Test that the workflow is executed with proper prompts."""
    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_chain.return_value = (["Step 1 done", "Step 2 done"], [mock_bot.conversation, mock_bot.conversation])

        result, node = namshub_of_issue_resolution.invoke(mock_bot, issue_number="101")

        # Verify chain_workflow was called
        mock_chain.assert_called_once()
        call_args = mock_chain.call_args[0]

        # First arg should be the bot
        assert call_args[0] == mock_bot

        # Second arg should be a list of workflow prompts
        workflow_prompts = call_args[1]
        assert isinstance(workflow_prompts, list)
        assert len(workflow_prompts) > 0


def test_issue_number_extraction_from_context(mock_bot):
    """Test that issue number can be extracted from conversation context."""
    # Set up parent content with issue reference
    mock_bot.conversation.parent = Mock()
    mock_bot.conversation.parent.content = "Please work on issue #999"

    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_chain.return_value = (["response"], [mock_bot.conversation])

        result, node = namshub_of_issue_resolution.invoke(mock_bot)

        # Should extract issue number from context
        mock_bot.set_system_message.assert_called_once()
        system_msg = mock_bot.set_system_message.call_args[0][0]
        assert "issue #999" in system_msg.lower()


def test_final_summary_format(mock_bot):
    """Test that the final summary is properly formatted."""
    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_responses = ["Step 1 complete", "Step 2 complete", "All done!"]
        mock_chain.return_value = (mock_responses, [mock_bot.conversation] * 3)

        result, node = namshub_of_issue_resolution.invoke(mock_bot, issue_number="202")

        # Result should be a string
        assert isinstance(result, str)
        # Should reference the issue number
        assert "202" in result or "issue" in result.lower()


@pytest.mark.integration
def test_real_workflow_with_mock_bot():
    """Integration test with a real MockBot instance."""
    bot = MockBot()

    # This should not crash, even though it won't execute real commands
    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_chain.return_value = (["Workflow complete"], [bot.conversation])

        result, node = namshub_of_issue_resolution.invoke(bot, issue_number="303")

        assert isinstance(result, str)
        assert node is not None


@pytest.mark.skip(reason="Requires real GitHub access and API credentials")
def test_real_github_integration():
    """
    Real integration test that would work with actual GitHub.
    Skipped by default as it requires:
    - GitHub CLI (gh) installed and authenticated
    - A real repository with issues
    - API credentials
    """
    bot = AnthropicBot()

    # This would execute the real workflow
    result, node = namshub_of_issue_resolution.invoke(bot, issue_number="1")

    assert "Error" not in result
    assert node is not None


def test_workflow_prompts_content():
    """Test that workflow prompts contain expected commands and instructions."""
    bot = MockBot()

    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        mock_chain.return_value = (["response"], [bot.conversation])

        namshub_of_issue_resolution.invoke(bot, issue_number="404")

        # Get the workflow prompts that were passed
        workflow_prompts = mock_chain.call_args[0][1]

        # Convert all prompts to a single string for easier checking
        all_prompts = " ".join(workflow_prompts).lower()

        # Check for key workflow elements
        assert "gh issue view" in all_prompts
        assert "branch" in all_prompts
        assert "test" in all_prompts or "pytest" in all_prompts
        assert "pr" in all_prompts or "pull request" in all_prompts


def test_error_handling_in_workflow():
    """Test that errors during workflow execution are handled gracefully."""
    bot = MockBot()

    with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
        # Simulate an error in the workflow
        mock_chain.side_effect = Exception("Workflow error")

        try:
            result, node = namshub_of_issue_resolution.invoke(bot, issue_number="505")
            # If no exception is raised, check that error is in result
            assert "error" in result.lower() or "exception" in result.lower()
        except Exception as e:
            # It's acceptable for the exception to propagate
            assert "Workflow error" in str(e)


def test_multiple_issue_patterns():
    """Test extraction of issue numbers from various formats."""
    bot = MockBot()

    test_cases = [
        ("Work on #123", "123"),
        ("Fix PR #456", "456"),
        ("Resolve issue #789", "789"),
        ("Handle pull request #101", "101"),
    ]

    for content, expected_number in test_cases:
        bot.conversation.parent = Mock()
        bot.conversation.parent.content = content

        with patch("bots.namshubs.namshub_of_issue_resolution.chain_workflow") as mock_chain:
            mock_chain.return_value = (["response"], [bot.conversation])

            namshub_of_issue_resolution.invoke(bot)

            system_msg = bot.set_system_message.call_args[0][0]
            assert f"#{expected_number}" in system_msg or expected_number in system_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
