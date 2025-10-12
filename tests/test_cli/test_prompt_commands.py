"""
Tests for CLI /s (save prompt) and /p (load prompt) commands.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from bots.dev.cli import CLI, PromptHandler, PromptManager


@pytest.fixture
def temp_prompts_file():
    """Create a temporary prompts file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
        # Initialize with empty structure
        json.dump({"recents": [], "prompts": {}}, f)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def prompt_manager(temp_prompts_file):
    """Create a PromptManager with a temporary file."""
    return PromptManager(prompts_file=temp_prompts_file)


@pytest.fixture
def prompt_handler(temp_prompts_file):
    """Create a PromptHandler with a temporary file."""
    handler = PromptHandler()
    handler.prompt_manager = PromptManager(prompts_file=temp_prompts_file)
    return handler


@pytest.fixture
def cli_with_temp_prompts(temp_prompts_file):
    """Create a CLI instance with a temporary prompts file."""
    cli = CLI()
    cli.prompts.prompt_manager = PromptManager(prompts_file=temp_prompts_file)
    return cli


class TestPromptManager:
    """Tests for the PromptManager class."""

    def test_save_prompt_with_name(self, prompt_manager):
        """Test saving a prompt with a specific name."""
        prompt_text = "This is a test prompt"
        name = prompt_manager.save_prompt(prompt_text, name="test_prompt")

        assert name == "test_prompt"
        assert "test_prompt" in prompt_manager.prompts_data["prompts"]
        assert prompt_manager.prompts_data["prompts"]["test_prompt"] == prompt_text

    def test_save_prompt_without_name(self, prompt_manager):
        """Test saving a prompt without a name (auto-generated)."""
        with patch.object(prompt_manager, "_generate_prompt_name", return_value="auto_generated"):
            prompt_text = "This is a test prompt"
            name = prompt_manager.save_prompt(prompt_text)

            assert name == "auto_generated"
            assert "auto_generated" in prompt_manager.prompts_data["prompts"]

    def test_save_prompt_duplicate_name(self, prompt_manager):
        """Test saving prompts with duplicate names (should append counter)."""
        prompt_text1 = "First prompt"
        prompt_text2 = "Second prompt"

        name1 = prompt_manager.save_prompt(prompt_text1, name="duplicate")
        name2 = prompt_manager.save_prompt(prompt_text2, name="duplicate")

        assert name1 == "duplicate"
        assert name2 == "duplicate_1"
        assert prompt_manager.prompts_data["prompts"]["duplicate"] == prompt_text1
        assert prompt_manager.prompts_data["prompts"]["duplicate_1"] == prompt_text2

    def test_load_prompt(self, prompt_manager):
        """Test loading a saved prompt."""
        prompt_text = "Test prompt to load"
        prompt_manager.save_prompt(prompt_text, name="loadable")

        loaded = prompt_manager.load_prompt("loadable")
        assert loaded == prompt_text

    def test_load_nonexistent_prompt(self, prompt_manager):
        """Test loading a prompt that doesn't exist."""
        with pytest.raises(KeyError):
            prompt_manager.load_prompt("nonexistent")

    def test_search_prompts_by_name(self, prompt_manager):
        """Test searching prompts by name."""
        prompt_manager.save_prompt("Content 1", name="test_search_1")
        prompt_manager.save_prompt("Content 2", name="test_search_2")
        prompt_manager.save_prompt("Content 3", name="other_name")

        results = prompt_manager.search_prompts("test_search")
        assert len(results) == 2
        assert all("test_search" in name for name, _ in results)

    def test_search_prompts_by_content(self, prompt_manager):
        """Test searching prompts by content."""
        prompt_manager.save_prompt("Find this content", name="prompt1")
        prompt_manager.save_prompt("Other content", name="prompt2")

        results = prompt_manager.search_prompts("Find this")
        assert len(results) == 1
        assert results[0][0] == "prompt1"

    def test_search_prompts_empty_query_returns_recents(self, prompt_manager):
        """Test that empty search query returns recent prompts."""
        prompt_manager.save_prompt("Recent 1", name="recent1")
        prompt_manager.save_prompt("Recent 2", name="recent2")

        results = prompt_manager.search_prompts("")
        assert len(results) == 2
        # Most recent should be first
        assert results[0][0] == "recent2"

    def test_update_recents(self, prompt_manager):
        """Test that recents list is updated correctly."""
        prompt_manager.save_prompt("Prompt 1", name="p1")
        prompt_manager.save_prompt("Prompt 2", name="p2")
        prompt_manager.save_prompt("Prompt 3", name="p3")

        # Load p1 again to move it to front
        prompt_manager.load_prompt("p1")

        assert prompt_manager.prompts_data["recents"][0] == "p1"

    def test_recents_limited_to_five(self, prompt_manager):
        """Test that recents list is limited to 5 items."""
        for i in range(10):
            prompt_manager.save_prompt(f"Prompt {i}", name=f"p{i}")

        assert len(prompt_manager.prompts_data["recents"]) == 5


class TestPromptHandler:
    """Tests for the PromptHandler class."""

    def test_save_prompt_with_args(self, prompt_handler):
        """Test /s command with arguments."""
        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["This", "is", "a", "test"]

        with patch.object(prompt_handler.prompt_manager, "save_prompt", return_value="test_name") as mock_save:
            result = prompt_handler.save_prompt(mock_bot, mock_context, args, last_user_message=None)

            mock_save.assert_called_once_with("This is a test")
            assert "Saved prompt as: test_name" in result

    def test_save_prompt_with_last_message(self, prompt_handler):
        """Test /s command without args but with last user message."""
        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = []
        last_message = "Save this message"

        with patch.object(prompt_handler.prompt_manager, "save_prompt", return_value="saved_msg") as mock_save:
            result = prompt_handler.save_prompt(mock_bot, mock_context, args, last_user_message=last_message)

            mock_save.assert_called_once_with("Save this message")
            assert "Saved prompt as: saved_msg" in result

    def test_save_prompt_no_content(self, prompt_handler):
        """Test /s command with no args and no last message."""
        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = []

        result = prompt_handler.save_prompt(mock_bot, mock_context, args, last_user_message=None)

        assert "No prompt to save" in result

    def test_save_prompt_empty_string(self, prompt_handler):
        """Test /s command with empty string."""
        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["   "]

        result = prompt_handler.save_prompt(mock_bot, mock_context, args, last_user_message=None)

        assert "Cannot save empty prompt" in result

    def test_load_prompt_single_match(self, prompt_handler):
        """Test /p command with single match."""
        # Save a prompt first
        prompt_handler.prompt_manager.save_prompt("Test content", name="unique_prompt")

        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["unique"]

        message, prefill = prompt_handler.load_prompt(mock_bot, mock_context, args)

        assert "Loaded prompt: unique_prompt" in message
        assert prefill == "Test content"

    def test_load_prompt_no_matches(self, prompt_handler):
        """Test /p command with no matches."""
        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["nonexistent"]

        message, prefill = prompt_handler.load_prompt(mock_bot, mock_context, args)

        assert "No prompts found" in message
        assert prefill is None

    def test_load_prompt_multiple_matches(self, prompt_handler):
        """Test /p command with multiple matches requiring selection."""
        # Save multiple prompts
        prompt_handler.prompt_manager.save_prompt("Content 1", name="test_1")
        prompt_handler.prompt_manager.save_prompt("Content 2", name="test_2")

        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["test"]

        with patch("builtins.input", return_value="1"):
            message, prefill = prompt_handler.load_prompt(mock_bot, mock_context, args)

            assert "Loaded prompt:" in message
            assert prefill in ["Content 1", "Content 2"]

    def test_load_prompt_invalid_selection(self, prompt_handler):
        """Test /p command with invalid selection number."""
        # Save multiple prompts
        prompt_handler.prompt_manager.save_prompt("Content 1", name="test_1")
        prompt_handler.prompt_manager.save_prompt("Content 2", name="test_2")

        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["test"]

        with patch("builtins.input", return_value="99"):
            message, prefill = prompt_handler.load_prompt(mock_bot, mock_context, args)

            assert "Invalid selection" in message
            assert prefill is None

    def test_load_prompt_cancelled_selection(self, prompt_handler):
        """Test /p command with cancelled selection."""
        # Save multiple prompts
        prompt_handler.prompt_manager.save_prompt("Content 1", name="test_1")
        prompt_handler.prompt_manager.save_prompt("Content 2", name="test_2")

        mock_bot = MagicMock()
        mock_context = MagicMock()
        args = ["test"]

        with patch("builtins.input", return_value=""):
            message, prefill = prompt_handler.load_prompt(mock_bot, mock_context, args)

            assert "Selection cancelled" in message
            assert prefill is None


class TestCLIIntegration:
    """Integration tests for /s and /p commands in CLI."""

    def test_cli_save_command_with_args(self, cli_with_temp_prompts):
        """Test CLI /s command with arguments."""
        cli = cli_with_temp_prompts
        mock_bot = MagicMock()

        with patch.object(cli.prompts.prompt_manager, "_generate_prompt_name", return_value="test_save"):
            result = cli.commands["/s"](mock_bot, cli.context, ["Save", "this", "text"])

            assert "Saved prompt as:" in result
            assert "test_save" in cli.prompts.prompt_manager.prompts_data["prompts"]

    def test_cli_save_command_after_message(self, cli_with_temp_prompts):
        """Test CLI /s command after sending a message."""
        cli = cli_with_temp_prompts
        cli.last_user_message = "This was my last message"
        mock_bot = MagicMock()

        with patch.object(cli.prompts.prompt_manager, "_generate_prompt_name", return_value="last_msg"):
            result = cli.commands["/s"](mock_bot, cli.context, [])

            assert "Saved prompt as:" in result
            assert cli.prompts.prompt_manager.prompts_data["prompts"]["last_msg"] == "This was my last message"

    def test_cli_load_command(self, cli_with_temp_prompts):
        """Test CLI /p command."""
        cli = cli_with_temp_prompts

        # Save a prompt first
        cli.prompts.prompt_manager.save_prompt("Loaded content", name="loadable")

        mock_bot = MagicMock()

        # Call without assignment to avoid unused variable
        cli.commands["/p"](mock_bot, cli.context, ["loadable"])

        # Should set pending_prefill
        assert cli.pending_prefill == "Loaded content"

    def test_cli_handle_chat_tracks_last_message(self, cli_with_temp_prompts):
        """Test that _handle_chat tracks the last user message."""
        cli = cli_with_temp_prompts
        mock_bot = MagicMock()
        mock_bot.conversation = MagicMock()

        with patch("bots.flows.functional_prompts.chain", return_value=(["response"], [MagicMock()])):
            cli._handle_chat(mock_bot, "Test user input")

            assert cli.last_user_message == "Test user input"

    def test_cli_commands_registered(self, cli_with_temp_prompts):
        """Test that /s and /p commands are properly registered."""
        cli = cli_with_temp_prompts

        assert "/s" in cli.commands
        assert "/p" in cli.commands
        assert cli.commands["/s"] == cli._handle_save_prompt
        assert cli.commands["/p"] == cli._handle_load_prompt


class TestEndToEnd:
    """End-to-end tests for the prompt workflow."""

    def test_save_and_load_workflow(self, cli_with_temp_prompts):
        """Test complete workflow: save a prompt, then load it."""
        cli = cli_with_temp_prompts
        mock_bot = MagicMock()

        # Step 1: Save a prompt
        with patch.object(cli.prompts.prompt_manager, "_generate_prompt_name", return_value="workflow_test"):
            save_result = cli.commands["/s"](mock_bot, cli.context, ["Workflow", "test", "prompt"])
            assert "Saved prompt as: workflow_test" in save_result

        # Step 2: Load the prompt
        cli.commands["/p"](mock_bot, cli.context, ["workflow"])
        assert cli.pending_prefill == "Workflow test prompt"

    def test_save_after_chat_then_load(self, cli_with_temp_prompts):
        """Test saving after a chat message, then loading it."""
        cli = cli_with_temp_prompts
        mock_bot = MagicMock()
        mock_bot.conversation = MagicMock()

        # Step 1: Simulate a chat message
        with patch("bots.flows.functional_prompts.chain", return_value=(["response"], [MagicMock()])):
            cli._handle_chat(mock_bot, "Important message to save")

        # Step 2: Save the last message
        with patch.object(cli.prompts.prompt_manager, "_generate_prompt_name", return_value="important_msg"):
            save_result = cli.commands["/s"](mock_bot, cli.context, [])
            assert "Saved prompt as: important_msg" in save_result

        # Step 3: Load it back
        cli.commands["/p"](mock_bot, cli.context, ["important"])
        assert cli.pending_prefill == "Important message to save"

    def test_multiple_saves_and_search(self, cli_with_temp_prompts):
        """Test saving multiple prompts and searching through them."""
        cli = cli_with_temp_prompts
        # Save multiple prompts
        prompts = [
            ("coding_task", "Write a function to sort a list"),
            ("coding_review", "Review this code for bugs"),
            ("documentation", "Write documentation for this module"),
        ]

        for name, content in prompts:
            cli.prompts.prompt_manager.save_prompt(content, name=name)

        # Search for "coding" should return 2 results
        results = cli.prompts.prompt_manager.search_prompts("coding")
        assert len(results) == 2

        # Search for "documentation" should return 1 result
        results = cli.prompts.prompt_manager.search_prompts("documentation")
        assert len(results) == 1
