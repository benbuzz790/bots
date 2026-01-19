#!/usr/bin/env python3
"""Test dill serialization behavior for tool functions.

This test verifies:
1. Dill serialization succeeds for same-runtime functions (positive case)
2. Dill serialization fails silently for dynamic modules (expected negative case)
3. Source code fallback works when dill fails
4. Functions work correctly after deserialization regardless of dill success/failure
"""

import os
import shutil
import sys
import tempfile
import unittest
from types import ModuleType

import pytest

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines

sys.path.insert(0, os.path.abspath("."))


class TestDillSerialization(unittest.TestCase):
    """Test dill serialization behavior with positive and negative cases."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.flaky(reruns=3)
    def test_dill_succeeds_for_same_runtime_functions(self):
        """Test that dill successfully serializes/deserializes same-runtime functions."""
        import os

        # Create a bot and add a tool from a real module (not dynamic)
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        from bots.tools.code_tools import view

        bot.add_tools(view)

        # Save and load
        save_path = os.path.join(self.temp_dir, "test_bot.bot")
        bot.save(save_path)
        loaded_bot = AnthropicBot.load(save_path)

        # Verify the tool was loaded correctly
        self.assertIn("view", loaded_bot.tool_handler.function_map, "view function should be in function_map after loading")

        # Verify the function works
        result = loaded_bot.tool_handler.function_map["view"](file_path="README.md", start_line="1", end_line="5")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_dill_fails_gracefully_for_dynamic_modules(self):
        """Test that dill serialization fails gracefully for dynamic modules and falls back to source code."""
        # Create a dynamic module at runtime
        dynamic_module = ModuleType("dynamic_test_module")
        dynamic_code = '''
def dynamic_function(x: int) -> int:
    """A dynamically created function."""
    return x * 2
'''
        exec(dynamic_code, dynamic_module.__dict__)

        # Create a bot and add the dynamic function
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)
        bot.add_tools(dynamic_module.dynamic_function)

        # Save and load
        save_path = os.path.join(self.temp_dir, "test_bot_dynamic.bot")
        bot.save(save_path)
        loaded_bot = AnthropicBot.load(save_path)

        # Verify the tool was loaded correctly (via source code fallback)
        self.assertIn(
            "dynamic_function",
            loaded_bot.tool_handler.function_map,
            "dynamic_function should be in function_map after loading",
        )

        # Verify the function works correctly
        result = loaded_bot.tool_handler.function_map["dynamic_function"](x=5)
        self.assertEqual(result, 10, "Function should work correctly after deserialization")

    def test_source_code_fallback_preserves_functionality(self):
        """Test that source code fallback preserves function functionality."""

        # Create a simple function
        def test_function(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Create a bot and add the function
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)
        bot.add_tools(test_function)

        # Save and load
        save_path = os.path.join(self.temp_dir, "test_bot_fallback.bot")
        bot.save(save_path)
        loaded_bot = AnthropicBot.load(save_path)

        # Verify the function works
        result = loaded_bot.tool_handler.function_map["test_function"](a=3, b=4)
        self.assertEqual(result, 7, "Function should work correctly after deserialization")


if __name__ == "__main__":
    unittest.main()
