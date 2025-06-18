"""Unit tests for ChatGPT_Bot functionality.
This module tests core functionality of the ChatGPT_Bot class including:
- File operations using tools
- Tool execution and result preservation
- State persistence through save/load operations
- Tool call sequencing and history management
"""

import os
import shutil
import tempfile
import unittest

from bots import ChatGPT_Bot
from bots.foundation.base import Engines
from bots.tools.code_tools import view


class TestGPTBot(unittest.TestCase):
    """Test suite for ChatGPT_Bot functionality.
    Tests basic bot operations including:
    - File reading capabilities
    - Tool execution and result preservation
    - Save/load state preservation
    - Tool call sequencing
    """

    def setUp(self) -> None:
        """Set up test environment before each test.
        Creates a temporary directory and initializes a ChatGPT_Bot instance
        with standard test configuration. Creates a test file with known
        content for file operation tests.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.bot = ChatGPT_Bot(
            model_engine=Engines.GPT4TURBO,
            max_tokens=1000,
            temperature=0.7,
            name="TestBot",
        )
        self.bot.add_tools(view)
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        self.test_content = "This is a test file content."
        with open(self.test_file_path, "w") as f:
            f.write(self.test_content)

    def tearDown(self) -> None:
        """Clean up test environment after each test.
        Removes the temporary directory and all its contents.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_gptbot_read_file(self) -> None:
        """Test bot's ability to read and display file contents.
        Tests that the bot can:
        1. Successfully read a file using the view tool
        2. Include file contents in its response
        3. Save its state after the operation
        """
        response1 = self.bot.respond(f"Please display the contents of the file {self.test_file_path}")
        print(response1)
        self.bot.save(os.path.join(self.temp_dir, "gpttestresult.bot"))
        self.assertIn(self.test_content, response1)

    def test_tool_call_sequence_save_load(self) -> None:
        """Test tool calls maintain proper sequence through save/load.
        Verifies that:
        1. Tool results are preserved in conversation history
        2. Tool results survive save/load operations
        3. New tool calls after loading maintain correct sequencing
        """

        def simple_addition(x: str, y: str) -> str:
            """Returns x + y with appropriate type conversion.
            Parameters:
                x (str): First number as string
                y (str): Second number as string
            Returns:
                str: Sum of x and y as string
            """
            return str(int(x) + int(y))

        bot = ChatGPT_Bot(model_engine=Engines.GPT4TURBO, max_tokens=1000, temperature=0.7)
        bot.add_tools(simple_addition)
        bot.respond("What is 5 + 3?")
        save_path = os.path.join(self.temp_dir, "tool_test.bot")
        bot.save(save_path)
        loaded_bot = ChatGPT_Bot.load(save_path)
        loaded_bot.respond("What is 10 + 15?")
        self.assertTrue(
            any(("8" in str(v) for v in bot.conversation.parent.tool_results[0].values()))
            if bot.conversation.parent.tool_results
            else False
        )
        self.assertTrue(
            any(("25" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
            if loaded_bot.conversation.parent.tool_results
            else False
        )

    def test_tool_call_sequence_basic(self) -> None:
        """Test tool calls maintain proper sequence without save/load.
        Verifies that:
        1. Tool results are correctly stored in conversation history
        2. Multiple tool calls maintain proper sequencing
        3. Results are accessible through the conversation tree
        """

        def simple_addition(x: str, y: str) -> str:
            """Returns x + y with appropriate type conversion.
            Parameters:
                x (str): First number as string
                y (str): Second number as string
            Returns:
                str: Sum of x and y as string
            """
            return str(int(x) + int(y))

        bot = ChatGPT_Bot(model_engine=Engines.GPT4TURBO, max_tokens=1000, temperature=0.7)
        bot.add_tools(simple_addition)
        bot.respond("What is 5 + 3?")
        self.assertTrue(
            any(("8" in str(v) for v in bot.conversation.parent.tool_results[0].values()))
            if bot.conversation.parent.tool_results
            else False
        )
        bot.respond("What is 10 + 15?")
        self.assertTrue(
            any(("25" in str(v) for v in bot.conversation.parent.tool_results[0].values()))
            if bot.conversation.parent.tool_results
            else False
        )


def main() -> None:
    """Manual test runner for GPTBot tests.
    Executes a subset of tests in sequence for development and debugging
    purposes. Tests are run individually rather than through unittest
    framework to allow for precise control and observation of test execution.
    The following tests are executed in order:
    1. test_tool_call_sequence_basic - Tests basic tool sequencing
    2. test_tool_call_sequence_save_load - Tests persistence of tool calls
    Note:
        This function is primarily for development use. For running all tests,
        use unittest.main() instead.
    """
    t = TestGPTBot()
    t.setUp()
    t.test_tool_call_sequence_basic()
    t.tearDown()
    print("Test 2")
    u = TestGPTBot()
    u.setUp()
    u.test_tool_call_sequence_save_load()
    u.tearDown()


if __name__ == "__main__":
    unittest.main()
