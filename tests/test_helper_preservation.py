#!/usr/bin/env python3
"""Test helper function preservation in save/load cycles."""
import os
import sys
import tempfile
import unittest
from typing import Any, Dict

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines

sys.path.insert(0, os.path.abspath("."))


class TestHelperPreservation(unittest.TestCase):
    """Test that helper functions are preserved across save/load cycles."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_tool_with_helpers(self) -> str:
        """Create a test file with tools that depend on helper functions."""
        content = '''# Helper functions
def _internal_helper(data: str) -> str:
    """Internal helper function"""
    return f"HELPER_PROCESSED: {data.upper()}"
def _another_helper(value: int) -> str:
    """Another helper function"""
    return f"NUMERIC_HELPER: {value * 2}"
# Main tool that uses helper functions
def tool_with_helpers(input_text: str, multiplier: int = 1) -> str:
    """Tool that depends on helper functions"""
    processed = _internal_helper(input_text)
    numeric_result = _another_helper(multiplier)
    return f"COMBINED: {processed} + {numeric_result}"
'''
        test_file_path = os.path.join(self.temp_dir, "helper_tools.py")
        with open(test_file_path, "w") as f:
            f.write(content)
        return test_file_path

    def check_helper_availability(self, bot: AnthropicBot, tool_name: str) -> Dict[str, Any]:
        """Check if helper functions are available."""
        result = {"tool_exists": False, "helper_functions_available": False, "helper_function_names": [], "error_details": []}
        try:
            if tool_name in bot.tool_handler.function_map:
                result["tool_exists"] = True
                func = bot.tool_handler.function_map[tool_name]
                if hasattr(func, "__globals__"):
                    globals_dict = func.__globals__
                    helper_funcs = [
                        name for name in globals_dict.keys() if name.startswith("_") and callable(globals_dict.get(name))
                    ]
                    result["helper_functions_available"] = len(helper_funcs) > 0
                    result["helper_function_names"] = helper_funcs
        except Exception as e:
            result["error_details"].append(f"Helper check error: {str(e)}")
        return result

    def test_helper_preservation_basic(self):
        """Test basic helper function preservation."""
        print("\nTesting helper function preservation...")
        # Create bot with helper-dependent tools
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE35_SONNET_20240620, max_tokens=1000)
        tool_file = self.create_tool_with_helpers()
        bot.add_tools(tool_file)
        # Check helpers before save/load
        before = self.check_helper_availability(bot, "tool_with_helpers")
        print(f"Before save/load - Helper functions available: {before['helper_functions_available']}")
        print(f"Helper function names: {before['helper_function_names']}")
        # Save and load
        save_path = os.path.join(self.temp_dir, "test_bot")
        bot.save(save_path)
        loaded_bot = Bot.load(save_path + ".bot")
        # Check helpers after save/load
        after = self.check_helper_availability(loaded_bot, "tool_with_helpers")
        print(f"After save/load - Helper functions available: {after['helper_functions_available']}")
        print(f"Helper function names: {after['helper_function_names']}")
        # Test if the tool still works
        try:
            # This should work if helpers are preserved
            func = loaded_bot.tool_handler.function_map["tool_with_helpers"]
            result = func("test", 2)
            print(f"Tool execution result: {result}")
            tool_works = "HELPER_PROCESSED: TEST" in result and "NUMERIC_HELPER: 4" in result
        except Exception as e:
            print(f"Tool execution failed: {e}")
            tool_works = False
        print(f"Tool works after save/load: {tool_works}")
        print(f"Helper preservation: {before['helper_functions_available'] == after['helper_functions_available']}")
        return {
            "before": before,
            "after": after,
            "tool_works": tool_works,
            "helper_preservation": before["helper_functions_available"] == after["helper_functions_available"],
        }


if __name__ == "__main__":
    unittest.main(verbosity=2)
