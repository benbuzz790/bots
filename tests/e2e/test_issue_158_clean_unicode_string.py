"""
Test for Issue #158: python_view/python_edit tools fail with 'clean_unicode_string' not defined after bot load
"""

import os
import tempfile

import pytest

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines
from bots.tools.python_edit import python_edit, python_view


def test_python_tools_after_bot_load():
    """Test that python_view and python_edit work after saving and loading a bot."""

    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        bot_file = os.path.join(tmpdir, "test_bot.bot")
        test_py_file = os.path.join(tmpdir, "test_file.py")

        # Create a simple Python file to view/edit
        with open(test_py_file, "w", encoding="utf-8") as f:
            f.write(
                """def hello():
    return "Hello, World!"
"""
            )

        # Step 1: Create a bot and add python tools
        bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=1000, temperature=0.0)

        # Add the python tools
        bot.add_tools(python_view, python_edit)

        # Verify tools are added
        assert "python_view" in bot.tool_handler.function_map
        assert "python_edit" in bot.tool_handler.function_map

        # Step 2: Save the bot
        bot.save(bot_file)
        assert os.path.exists(bot_file)

        # Step 3: Load the bot
        loaded_bot = Bot.load(bot_file)

        # Verify tools are still present
        assert "python_view" in loaded_bot.tool_handler.function_map
        assert "python_edit" in loaded_bot.tool_handler.function_map

        # Step 4: Try to use python_view - this should trigger the error if bug exists
        try:
            result = loaded_bot.tool_handler.function_map["python_view"](test_py_file)
            print("✓ python_view succeeded after load")
            print(f"Result preview: {result[:100]}...")

            # If we got here, the bug is fixed!
            assert "def hello():" in result

        except NameError as e:
            if "clean_unicode_string" in str(e):
                print(f"✗ BUG REPRODUCED: {e}")
                pytest.fail(f"Issue #158 reproduced: {e}")
            else:
                raise

        # Step 5: Try to use python_edit
        try:
            edit_result = loaded_bot.tool_handler.function_map["python_edit"](
                test_py_file,
                """def goodbye():
    return "Goodbye!"
""",
                coscope_with="__FILE_END__",
            )
            print("✓ python_edit succeeded after load")
            print(f"Edit result: {edit_result}")

        except NameError as e:
            if "clean_unicode_string" in str(e):
                print(f"✗ BUG REPRODUCED in python_edit: {e}")
                pytest.fail(f"Issue #158 reproduced in python_edit: {e}")
            else:
                raise

        print("\n✓✓✓ Issue #158 appears to be FIXED - both tools work after bot load!")


if __name__ == "__main__":
    test_python_tools_after_bot_load()
