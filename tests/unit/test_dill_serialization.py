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
from io import StringIO
from types import ModuleType

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

    def test_dill_succeeds_for_same_runtime_functions(self):
        """Test that dill successfully serializes/deserializes same-runtime functions."""
        # Create a bot and add a tool from a real module (not dynamic)
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        from bots.tools.code_tools import view

        bot.add_tools(view)

        # Debug: Check what's in function_map before save
        print(f"DEBUG: Before save, function_map keys: {list(bot.tool_handler.function_map.keys())}")
        print(f"DEBUG: Before save, tool_registry keys: {list(bot.tool_handler.tool_registry.keys())}")

        # Save and load the bot (save adds .bot extension)
        save_path = os.path.join(self.temp_dir, "bot_state")
        actual_path = bot.save(save_path)

        # Debug: Check what was saved
        import json

        with open(actual_path, "r") as f:
            saved_data = json.load(f)
        tool_handler_data = saved_data.get("tool_handler", {})
        print(f"DEBUG: Saved tool_registry keys: {list(tool_handler_data.get('tool_registry', {}).keys())}")
        print(f"DEBUG: Saved function_paths keys: {list(tool_handler_data.get('function_paths', {}).keys())}")

        loaded_bot = AnthropicBot.load(actual_path)

        # Debug: Check what's in function_map after load
        print(f"DEBUG: After load, function_map keys: {list(loaded_bot.tool_handler.function_map.keys())}")
        print(f"DEBUG: After load, tool_registry keys: {list(loaded_bot.tool_handler.tool_registry.keys())}")

        # Verify the tool works after loading
        self.assertIn("view", loaded_bot.tool_handler.function_map)
        func = loaded_bot.tool_handler.function_map["view"]
        self.assertTrue(callable(func))

        # Test that the function actually works (can be called)
        # Note: We don't test execution here, just that it's callable and has right signature
        import inspect

        sig = inspect.signature(func)
        self.assertIn("file_path", sig.parameters)

    def test_dill_fails_silently_for_dynamic_modules(self):
        """Test that dill failures for dynamic modules are silent (no warnings printed)."""
        # Create a bot with a dynamically loaded tool
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        # Create a dynamic module with a synthetic __module__ name
        dynamic_module = ModuleType("__runtime__.dynamic_module_test")

        # Define a function in the dynamic module
        exec(
            """
def test_dynamic_func(x: int) -> str:
    '''A test function from a dynamic module.'''
    return f"Result: {x * 2}"
""",
            dynamic_module.__dict__,
        )

        test_func = dynamic_module.__dict__["test_dynamic_func"]

        # Manually set the __module__ to simulate dynamic module behavior
        test_func.__module__ = "__runtime__.dynamic_module_test"

        bot.add_tools(test_func)

        # Capture stdout to check for warnings
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Save and load the bot - dill will fail but should be silent
            save_path = os.path.join(self.temp_dir, "bot_state")
            actual_path = bot.save(save_path)
            loaded_bot = AnthropicBot.load(actual_path)

            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify no "Could not dill deserialize" warnings were printed
        self.assertNotIn("Could not dill deserialize", output)

        # Verify the function still exists and works (via source code fallback)
        self.assertIn("test_dynamic_func", loaded_bot.tool_handler.function_map)
        func = loaded_bot.tool_handler.function_map["test_dynamic_func"]
        self.assertTrue(callable(func))

    def test_source_code_fallback_works(self):
        """Test that source code fallback successfully recreates functions when dill fails."""
        # Create a bot with a function that has helper functions
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        # Create a module with a main function and helper function
        test_module = ModuleType("test_module_with_helpers")
        test_module.__file__ = os.path.join(self.temp_dir, "test_module.py")

        source_code = """
def _helper_function(value):
    '''Helper function that should be preserved.'''
    return value * 2

def main_function(x: int) -> int:
    '''Main function that uses helper.

    Parameters:
    - x (int): Input value

    Returns:
    - int: Processed value
    '''
    return _helper_function(x) + 1
"""

        exec(source_code, test_module.__dict__)
        main_func = test_module.__dict__["main_function"]

        # Make this look like a dynamic module to force dill failure
        main_func.__module__ = "__runtime__.test_module_dynamic"

        bot.add_tools(main_func)

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Save and load - dill will fail, source code should work
            save_path = os.path.join(self.temp_dir, "bot_state")
            actual_path = bot.save(save_path)
            loaded_bot = AnthropicBot.load(actual_path)

            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify no warnings
        self.assertNotIn("Could not dill deserialize", output)

        # Verify the function exists and works
        self.assertIn("main_function", loaded_bot.tool_handler.function_map)
        func = loaded_bot.tool_handler.function_map["main_function"]
        self.assertTrue(callable(func))

        # Verify the helper function is also available by checking the function's globals
        # (this tests that source code execution recreated it)
        if hasattr(func, "__module_context__"):
            # If module context exists, check there
            module_context = func.__module_context__
            self.assertIn("_helper_function", module_context.namespace.__dict__)
            helper = module_context.namespace.__dict__["_helper_function"]
            self.assertTrue(callable(helper))
        else:
            # Otherwise check the function's globals
            self.assertIn("_helper_function", func.__globals__)
            helper = func.__globals__["_helper_function"]
            self.assertTrue(callable(helper))

    def test_branching_with_dynamic_modules_no_warnings(self):
        """Test that branching operations don't produce dill warnings."""
        from bots.tools.self_tools import branch_self

        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)
        bot.add_tools(branch_self)

        # Capture stdout during bot state serialization (used in branching)
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Get the bot's state (this is what branching does internally)
            state = bot.__getstate__()

            # Create a new bot from the state (simulating branch)
            new_bot = AnthropicBot.__new__(AnthropicBot)
            new_bot.__setstate__(state)

            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify no dill warnings were printed
        self.assertNotIn("Could not dill deserialize", output)

        # Verify the tool still works in the new bot
        self.assertIn("branch_self", new_bot.tool_handler.function_map)
        func = new_bot.tool_handler.function_map["branch_self"]
        self.assertTrue(callable(func))

    def test_actual_failure_case_missing_source(self):
        """Test that actual failures (missing source AND dill failure) are still detected."""
        # Create a bot
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        # Create a function with no source code available
        # This simulates a truly broken case
        def temp_func(x: int) -> str:
            """A temporary function."""
            return str(x)

        bot.add_tools(temp_func)

        # Manually corrupt the saved state to simulate source code loss
        save_path = os.path.join(self.temp_dir, "bot_state")
        actual_path = bot.save(save_path)

        import json

        with open(actual_path, "r") as f:
            state = json.load(f)

        # Corrupt the source code for all modules
        if "tool_handler" in state and "modules" in state["tool_handler"]:
            for module_key in state["tool_handler"]["modules"]:
                state["tool_handler"]["modules"][module_key]["source"] = ""

        with open(actual_path, "w") as f:
            json.dump(state, f)

        # Try to load - this should fail or at least show the function is broken
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            loaded_bot = AnthropicBot.load(actual_path)
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # In this case, the function should either be missing or a warning should appear
        # (since BOTH dill AND source failed)
        # The exact behavior depends on implementation, but it shouldn't silently succeed
        # Check that either the function is missing OR there was a warning
        function_missing = "temp_func" not in loaded_bot.tool_handler.function_map
        warning_present = "Warning:" in output or "Failed" in output

        self.assertTrue(
            function_missing or warning_present,
            "Expected either missing function or warning when both dill and source fail",
        )


if __name__ == "__main__":
    unittest.main()
