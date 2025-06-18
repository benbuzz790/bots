import unittest
from unittest.mock import MagicMock, patch

import bots.dev.cli as cli_module


class TestCLILoad(unittest.TestCase):
    """Test suite for CLI load functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.content = "Original response"
        self.mock_bot.conversation.replies = []
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot
        self.context.labeled_nodes = {"test": "node"}
        # Use StateHandler which contains the load function
        self.handler = cli_module.StateHandler()

    @patch("builtins.input")
    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_success_updates_context(self, mock_bot_load, mock_exists, mock_input):
        """Test that load function updates context.bot_instance."""
        # Setup mocks
        test_filename = "test_bot.bot"
        mock_input.return_value = test_filename
        mock_exists.return_value = True
        new_mock_bot = MagicMock()
        new_mock_bot.name = "LoadedBot"
        new_mock_bot.conversation = MagicMock()
        new_mock_bot.conversation.content = "Loaded response"
        new_mock_bot.conversation.replies = []
        mock_bot_load.return_value = new_mock_bot
        # Store original bot reference
        original_bot = self.context.bot_instance
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify the load was called
        mock_bot_load.assert_called_once_with(test_filename)
        # Verify context.bot_instance was updated (this should pass now)
        self.assertNotEqual(
            self.context.bot_instance,
            original_bot,
            "Context bot_instance should be updated after load",
        )
        self.assertEqual(
            self.context.bot_instance,
            new_mock_bot,
            "Context should reference the loaded bot",
        )
        self.assertIn("Bot loaded from test_bot.bot", result)

    @patch("builtins.input")
    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_clears_labeled_nodes(self, mock_bot_load, mock_exists, mock_input):
        """Test that load function clears labeled nodes."""
        # Setup mocks
        mock_input.return_value = "test_bot.bot"
        mock_exists.return_value = True
        new_bot = MagicMock()
        new_bot.conversation = MagicMock()
        new_bot.conversation.replies = []
        mock_bot_load.return_value = new_bot
        # Ensure labeled_nodes has content
        self.context.labeled_nodes = {"node1": "value1", "node2": "value2"}
        # Call load function
        self.handler.load(self.mock_bot, self.context, [])
        # Verify labeled_nodes was cleared
        self.assertEqual(
            self.context.labeled_nodes,
            {},
            "Labeled nodes should be cleared after load",
        )

    @patch("builtins.input")
    def test_load_cancelled_by_user(self, mock_input):
        """Test load function when user cancels by providing empty filename."""
        # User cancels by providing empty filename
        mock_input.return_value = ""
        original_bot = self.context.bot_instance
        original_nodes = self.context.labeled_nodes.copy()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify nothing changed
        self.assertEqual(self.context.bot_instance, original_bot)
        self.assertEqual(self.context.labeled_nodes, original_nodes)
        self.assertEqual(result, "Load cancelled - no filename provided")

    @patch("builtins.input")
    @patch("os.path.exists")
    def test_load_file_not_found(self, mock_exists, mock_input):
        """Test load function when file doesn't exist."""
        # Setup mocks
        mock_input.return_value = "nonexistent.bot"
        mock_exists.return_value = False
        original_bot = self.context.bot_instance
        original_nodes = self.context.labeled_nodes.copy()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify error handling
        self.assertIn("File not found", result)
        # Verify state wasn't corrupted (should remain unchanged on error)
        self.assertEqual(self.context.bot_instance, original_bot)
        self.assertEqual(self.context.labeled_nodes, original_nodes)

    @patch("builtins.input")
    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_file_error(self, mock_bot_load, mock_exists, mock_input):
        """Test load function handles file loading errors."""
        # Setup mocks
        mock_input.return_value = "corrupted.bot"
        mock_exists.return_value = True
        mock_bot_load.side_effect = FileNotFoundError("File corrupted")
        original_bot = self.context.bot_instance
        original_nodes = self.context.labeled_nodes.copy()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify error handling
        self.assertIn("Error loading bot", result)
        self.assertIn("File corrupted", result)
        # Verify state wasn't corrupted (should remain unchanged on error)
        self.assertEqual(self.context.bot_instance, original_bot)
        self.assertEqual(self.context.labeled_nodes, original_nodes)

    @patch("builtins.input")
    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_calls_rebuild_labels(self, mock_bot_load, mock_exists, mock_input):
        """Test that load function calls _rebuild_labels."""
        # Setup mocks
        mock_input.return_value = "test_bot.bot"
        mock_exists.return_value = True
        new_bot = MagicMock()
        new_bot.conversation = MagicMock()
        new_bot.conversation.replies = []
        mock_bot_load.return_value = new_bot
        # Mock the _rebuild_labels method
        self.handler._rebuild_labels = MagicMock()
        # Call load function
        self.handler.load(self.mock_bot, self.context, [])
        # Verify _rebuild_labels was called
        self.handler._rebuild_labels.assert_called_once_with(new_bot.conversation, self.context)

    @patch("builtins.input")
    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_navigates_to_conversation_end(self, mock_bot_load, mock_exists, mock_input):
        """Test that load function navigates to the end of the conversation."""
        # Setup mocks
        mock_input.return_value = "test_bot.bot"
        mock_exists.return_value = True
        # Create a mock conversation tree: root -> reply1 -> reply2
        root_node = MagicMock()
        reply1 = MagicMock()
        reply2 = MagicMock()
        root_node.replies = [reply1]
        reply1.replies = [reply2]
        reply2.replies = []  # End of conversation
        new_bot = MagicMock()
        new_bot.conversation = root_node
        mock_bot_load.return_value = new_bot
        # Mock _rebuild_labels to avoid issues
        self.handler._rebuild_labels = MagicMock()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify bot conversation was navigated to the end
        self.assertEqual(new_bot.conversation, reply2)
        self.assertIn("Conversation restored to most recent message", result)

    @patch("builtins.input")
    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_handles_extension_automatically(self, mock_bot_load, mock_exists, mock_input):
        """Test that load function automatically adds .bot extension."""
        # Setup mocks - user provides filename without extension
        mock_input.return_value = "test_bot"

        def mock_exists_side_effect(path):
            # First call: "test_bot" doesn't exist
            # Second call: "test_bot.bot" exists
            return path == "test_bot.bot"

        mock_exists.side_effect = mock_exists_side_effect
        new_bot = MagicMock()
        new_bot.conversation = MagicMock()
        new_bot.conversation.replies = []
        mock_bot_load.return_value = new_bot
        # Mock _rebuild_labels to avoid issues
        self.handler._rebuild_labels = MagicMock()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify the load was called with .bot extension added
        mock_bot_load.assert_called_once_with("test_bot.bot")
        self.assertIn("Bot loaded from test_bot.bot", result)

    def test_load_function_is_fixed(self):
        """Verify that the load function correctly updates context."""
        # This test demonstrates that the load function has been fixed
        # It should update context.bot_instance, not just create a local
        # variable
        # Create a mock scenario
        original_bot = self.context.bot_instance
        with (
            patch("builtins.input") as mock_input,
            patch("os.path.exists") as mock_exists,
            patch("bots.foundation.base.Bot.load") as mock_load,
        ):
            mock_input.return_value = "test.bot"
            mock_exists.return_value = True
            new_bot = MagicMock()
            new_bot.name = "NewBot"
            new_bot.conversation = MagicMock()
            new_bot.conversation.replies = []
            mock_load.return_value = new_bot
            # Mock _rebuild_labels to avoid AttributeError
            self.handler._rebuild_labels = MagicMock()
            # Call load
            result = self.handler.load(self.mock_bot, self.context, [])
            # Verify the fix works
            self.assertNotEqual(self.context.bot_instance, original_bot)
            self.assertEqual(self.context.bot_instance, new_bot)
            self.assertEqual(self.context.labeled_nodes, {})
            self.assertIn("Bot loaded from test.bot", result)


if __name__ == "__main__":
    unittest.main()
