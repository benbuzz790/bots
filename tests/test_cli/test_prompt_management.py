import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bots.dev.cli import CLI, PromptHandler, PromptManager
from bots.foundation.base import Engines


class TestPromptManager(unittest.TestCase):
    """Test the PromptManager class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_prompts_file = Path(self.temp_dir) / "test_prompts.json"
        self.prompt_manager = PromptManager(str(self.test_prompts_file))

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_prompts_initialization(self):
        """Test that PromptManager initializes with empty structure when no file exists."""
        self.assertEqual(self.prompt_manager.prompts_data["recents"], [])
        self.assertEqual(self.prompt_manager.prompts_data["prompts"], {})

    def test_save_and_load_prompts_file(self):
        """Test saving and loading prompts from file."""
        # Add some test data
        self.prompt_manager.prompts_data = {
            "recents": ["test1", "test2"],
            "prompts": {"test1": "This is test prompt 1", "test2": "This is test prompt 2"},
        }
        self.prompt_manager._save_prompts()

        # Create new manager to test loading
        new_manager = PromptManager(str(self.test_prompts_file))
        self.assertEqual(new_manager.prompts_data["recents"], ["test1", "test2"])
        self.assertEqual(new_manager.prompts_data["prompts"]["test1"], "This is test prompt 1")

    def test_update_recents(self):
        """Test recency list management."""
        # Add prompts
        self.prompt_manager.prompts_data["prompts"] = {"prompt1": "content1", "prompt2": "content2", "prompt3": "content3"}

        # Test adding to empty recents
        self.prompt_manager._update_recents("prompt1")
        self.assertEqual(self.prompt_manager.prompts_data["recents"], ["prompt1"])

        # Test adding new item
        self.prompt_manager._update_recents("prompt2")
        self.assertEqual(self.prompt_manager.prompts_data["recents"], ["prompt2", "prompt1"])

        # Test moving existing item to front
        self.prompt_manager._update_recents("prompt1")
        self.assertEqual(self.prompt_manager.prompts_data["recents"], ["prompt1", "prompt2"])

        # Test limit of 5 items
        for i in range(3, 8):
            self.prompt_manager._update_recents(f"prompt{i}")

        self.assertEqual(len(self.prompt_manager.prompts_data["recents"]), 5)
        self.assertEqual(self.prompt_manager.prompts_data["recents"][0], "prompt7")

    @patch("bots.foundation.anthropic_bots.AnthropicBot")
    def test_generate_prompt_name(self, mock_bot_class):
        """Test prompt name generation using Haiku bot."""
        # Mock the bot response
        mock_bot = MagicMock()
        mock_bot.respond.return_value = "test_prompt_name"
        mock_bot_class.return_value = mock_bot

        name = self.prompt_manager._generate_prompt_name("This is a test prompt")

        self.assertEqual(name, "test_prompt_name")
        mock_bot_class.assert_called_once_with(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
        mock_bot.respond.assert_called_once()

    @patch("bots.foundation.anthropic_bots.AnthropicBot")
    def test_generate_prompt_name_fallback(self, mock_bot_class):
        """Test prompt name generation fallback when bot fails."""
        # Mock the bot to raise an exception
        mock_bot_class.side_effect = Exception("Bot creation failed")

        with patch("time.time", return_value=1234567890):
            name = self.prompt_manager._generate_prompt_name("This is a test prompt")
            self.assertEqual(name, "prompt_1234567890")

    def test_search_prompts_empty_query(self):
        """Test search with empty query returns recents."""
        self.prompt_manager.prompts_data = {
            "recents": ["recent1", "recent2"],
            "prompts": {"recent1": "Recent prompt 1", "recent2": "Recent prompt 2", "other": "Other prompt"},
        }

        results = self.prompt_manager.search_prompts("")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], ("recent1", "Recent prompt 1"))
        self.assertEqual(results[1], ("recent2", "Recent prompt 2"))

    def test_search_prompts_by_name(self):
        """Test search by prompt name."""
        self.prompt_manager.prompts_data = {
            "recents": [],
            "prompts": {
                "neural_network": "Design a neural network",
                "database_query": "Write a SQL query",
                "neural_optimization": "Optimize neural networks",
            },
        }

        results = self.prompt_manager.search_prompts("neural")
        self.assertEqual(len(results), 2)
        names = [r[0] for r in results]
        self.assertIn("neural_network", names)
        self.assertIn("neural_optimization", names)

    def test_search_prompts_by_content(self):
        """Test search by prompt content."""
        self.prompt_manager.prompts_data = {
            "recents": [],
            "prompts": {
                "prompt1": "Design a neural network architecture",
                "prompt2": "Write a database schema",
                "prompt3": "Create a neural network model",
            },
        }

        results = self.prompt_manager.search_prompts("neural network")
        self.assertEqual(len(results), 2)
        names = [r[0] for r in results]
        self.assertIn("prompt1", names)
        self.assertIn("prompt3", names)

    @patch("bots.foundation.anthropic_bots.AnthropicBot")
    def test_save_prompt_with_auto_name(self, mock_bot_class):
        """Test saving prompt with auto-generated name."""
        mock_bot = MagicMock()
        mock_bot.respond.return_value = "auto_generated_name"
        mock_bot_class.return_value = mock_bot

        name = self.prompt_manager.save_prompt("This is a test prompt")

        self.assertEqual(name, "auto_generated_name")
        self.assertIn("auto_generated_name", self.prompt_manager.prompts_data["prompts"])
        self.assertEqual(self.prompt_manager.prompts_data["prompts"]["auto_generated_name"], "This is a test prompt")
        self.assertEqual(self.prompt_manager.prompts_data["recents"][0], "auto_generated_name")

    def test_save_prompt_unique_names(self):
        """Test that duplicate names get unique suffixes."""
        with patch.object(self.prompt_manager, "_generate_prompt_name", return_value="test_name"):
            # Save first prompt
            name1 = self.prompt_manager.save_prompt("First prompt")
            self.assertEqual(name1, "test_name")

            # Save second prompt with same generated name
            name2 = self.prompt_manager.save_prompt("Second prompt")
            self.assertEqual(name2, "test_name_1")

            # Save third prompt
            name3 = self.prompt_manager.save_prompt("Third prompt")
            self.assertEqual(name3, "test_name_2")

    def test_load_prompt(self):
        """Test loading a prompt and updating recency."""
        self.prompt_manager.prompts_data = {
            "recents": ["other"],
            "prompts": {"test_prompt": "This is a test prompt", "other": "Other prompt"},
        }

        content = self.prompt_manager.load_prompt("test_prompt")

        self.assertEqual(content, "This is a test prompt")
        self.assertEqual(self.prompt_manager.prompts_data["recents"][0], "test_prompt")

    def test_load_nonexistent_prompt(self):
        """Test loading a prompt that doesn't exist."""
        with self.assertRaises(KeyError):
            self.prompt_manager.load_prompt("nonexistent")


class TestPromptHandler(unittest.TestCase):
    """Test the PromptHandler class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_prompts_file = Path(self.temp_dir) / "test_prompts.json"

        # Create handler with custom prompts file
        self.handler = PromptHandler()
        self.handler.prompt_manager = PromptManager(str(self.test_prompts_file))

        # Mock bot and context
        self.mock_bot = MagicMock()
        self.mock_context = MagicMock()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("builtins.input")
    def test_load_prompt_no_matches(self, mock_input):
        """Test loading prompt when no matches found."""
        mock_input.return_value = "nonexistent"

        message, prefill = self.handler.load_prompt(self.mock_bot, self.mock_context, [])

        self.assertEqual(message, "No prompts found matching your search.")
        self.assertIsNone(prefill)

    @patch("builtins.input")
    def test_load_prompt_single_match(self, mock_input):
        """Test loading prompt with single match."""
        # Setup test data
        self.handler.prompt_manager.prompts_data = {"recents": [], "prompts": {"test_prompt": "This is a test prompt"}}

        mock_input.return_value = "test"

        message, prefill = self.handler.load_prompt(self.mock_bot, self.mock_context, [])

        self.assertEqual(message, "Loaded prompt: test_prompt")
        self.assertEqual(prefill, "This is a test prompt")

    @patch("builtins.input")
    @patch("builtins.print")
    def test_load_prompt_multiple_matches(self, mock_print, mock_input):
        """Test loading prompt with multiple matches."""
        # Setup test data
        self.handler.prompt_manager.prompts_data = {
            "recents": [],
            "prompts": {"test1": "First test prompt", "test2": "Second test prompt"},
        }

        mock_input.side_effect = ["test", "1"]  # Search then select first

        message, prefill = self.handler.load_prompt(self.mock_bot, self.mock_context, [])

        self.assertEqual(message, "Loaded prompt: test1")
        self.assertEqual(prefill, "First test prompt")

    @patch("builtins.input")
    @patch("builtins.print")
    def test_load_prompt_invalid_selection(self, mock_print, mock_input):
        """Test loading prompt with invalid selection."""
        # Setup test data with multiple matches to trigger selection
        self.handler.prompt_manager.prompts_data = {
            "recents": [],
            "prompts": {"test1": "First test prompt", "test2": "Second test prompt"},
        }

        mock_input.side_effect = ["test", "5"]  # Search then invalid selection

        message, prefill = self.handler.load_prompt(self.mock_bot, self.mock_context, [])

        self.assertTrue("Invalid selection" in message)
        self.assertIsNone(prefill)

    def test_load_prompt_with_args(self):
        """Test loading prompt with search args provided."""
        # Setup test data
        self.handler.prompt_manager.prompts_data = {"recents": [], "prompts": {"neural_network": "Design a neural network"}}

        message, prefill = self.handler.load_prompt(self.mock_bot, self.mock_context, ["neural"])

        self.assertEqual(message, "Loaded prompt: neural_network")
        self.assertEqual(prefill, "Design a neural network")

    @patch("bots.foundation.anthropic_bots.AnthropicBot")
    def test_save_prompt_with_args(self, mock_bot_class):
        """Test saving prompt with provided text."""
        mock_bot = MagicMock()
        mock_bot.respond.return_value = "generated_name"
        mock_bot_class.return_value = mock_bot

        result = self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt", "text"], None)

        self.assertEqual(result, "Saved prompt as: generated_name")
        self.assertEqual(self.handler.prompt_manager.prompts_data["prompts"]["generated_name"], "test prompt text")

    @patch("bots.foundation.anthropic_bots.AnthropicBot")
    def test_save_prompt_last_message(self, mock_bot_class):
        """Test saving prompt from last user message."""
        mock_bot = MagicMock()
        mock_bot.respond.return_value = "generated_name"
        mock_bot_class.return_value = mock_bot

        result = self.handler.save_prompt(self.mock_bot, self.mock_context, [], "last user message")

        self.assertEqual(result, "Saved prompt as: generated_name")
        self.assertEqual(self.handler.prompt_manager.prompts_data["prompts"]["generated_name"], "last user message")

    def test_save_prompt_no_content(self):
        """Test saving prompt with no content."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, [], None)

        self.assertTrue(result.startswith("No prompt to save"))

    def test_save_prompt_empty_content(self):
        """Test saving prompt with empty content."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, ["   "], None)

        self.assertEqual(result, "Cannot save empty prompt.")


class TestCLIPromptIntegration(unittest.TestCase):
    """Test CLI integration with prompt management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_prompts_file = Path(self.temp_dir) / "test_prompts.json"

        # Create CLI with mocked components
        with patch("bots.dev.cli.AnthropicBot"):
            self.cli = CLI()
            self.cli.prompts.prompt_manager = PromptManager(str(self.test_prompts_file))

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_handle_load_prompt(self):
        """Test CLI handling of /p command."""
        # Setup test data
        self.cli.prompts.prompt_manager.prompts_data = {"recents": [], "prompts": {"test_prompt": "This is a test prompt"}}

        result = self.cli._handle_load_prompt(None, None, ["test"])

        self.assertEqual(result, "Loaded prompt: test_prompt")
        self.assertEqual(self.cli.pending_prefill, "This is a test prompt")

    @patch("bots.foundation.anthropic_bots.AnthropicBot")
    def test_handle_save_prompt(self, mock_bot_class):
        """Test CLI handling of /s command."""
        mock_bot = MagicMock()
        mock_bot.respond.return_value = "generated_name"
        mock_bot_class.return_value = mock_bot

        self.cli.last_user_message = "test message"
        result = self.cli._handle_save_prompt(None, None, [])

        self.assertEqual(result, "Saved prompt as: generated_name")

    @patch("builtins.input")
    def test_get_user_input_with_prefill(self, mock_input):
        """Test getting user input with prefill fallback when readline not available."""
        # Test the fallback behavior when readline is not available
        with patch("bots.dev.cli.HAS_READLINE", False):
            mock_input.return_value = "edited prompt text"
            self.cli.pending_prefill = "original prompt text"

            result = self.cli._get_user_input(">>> ")

            self.assertEqual(result, "edited prompt text")
            self.assertIsNone(self.cli.pending_prefill)  # Should be cleared

    @patch("builtins.input")
    def test_get_user_input_without_prefill(self, mock_input):
        """Test getting user input without prefill."""
        mock_input.return_value = "normal input"

        result = self.cli._get_user_input(">>> ")

        self.assertEqual(result, "normal input")


def run_with_timeout(test_func, timeout_seconds=5):
    """Run a test function with timeout to prevent hanging."""
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = test_func()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        raise TimeoutError(f"Test timed out after {timeout_seconds} seconds")

    if exception[0]:
        raise exception[0]

    return result[0]


if __name__ == "__main__":
    unittest.main()
