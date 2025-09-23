#!/usr/bin/env python3
"""Test to reproduce the specific _convert_tool_inputs helper function loss bug."""
import sys
import os
import tempfile
import unittest
from typing import Dict, Any
sys.path.insert(0, os.path.abspath('.'))
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines
class TestSpecificHelperBug(unittest.TestCase):
    """Test to reproduce the specific helper function loss bug from CLI."""
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    def test_view_dir_tool_after_save_load(self):
        """Test view_dir tool specifically after save/load to reproduce the bug."""
        print("\nTesting view_dir tool after save/load (reproducing CLI bug)...")
        # Create bot and add view_dir tool (this should include _convert_tool_inputs helper)
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE35_SONNET_20240620, max_tokens=1000)
        # Import and add the view_dir tool
        from bots.tools.code_tools import view_dir
        bot.add_tools(view_dir)
        print(f"Original bot has {len(bot.tool_handler.tools)} tools")
        # Check if view_dir works before save/load
        try:
            result_before = view_dir(".", target_extensions="['py']", max_lines=10)
            print("view_dir works BEFORE save/load")
            before_works = True
        except Exception as e:
            print(f"view_dir FAILED before save/load: {e}")
            before_works = False
        # Check helper functions before save/load
        view_dir_func = bot.tool_handler.function_map.get("view_dir")
        if view_dir_func and hasattr(view_dir_func, '__globals__'):
            helpers_before = [name for name in view_dir_func.__globals__.keys() 
                            if name.startswith('_') and callable(view_dir_func.__globals__.get(name))]
            print(f"Helper functions before save/load: {helpers_before}")
            has_convert_tool_inputs_before = '_convert_tool_inputs' in view_dir_func.__globals__
            print(f"_convert_tool_inputs available before: {has_convert_tool_inputs_before}")
        else:
            helpers_before = []
            has_convert_tool_inputs_before = False
        # Save and load the bot
        save_path = os.path.join(self.temp_dir, "bug_reproduction_bot")
        bot.save(save_path)
        loaded_bot = Bot.load(save_path + ".bot")
        print(f"Loaded bot has {len(loaded_bot.tool_handler.tools)} tools")
        # Check helper functions after save/load
        loaded_view_dir_func = loaded_bot.tool_handler.function_map.get("view_dir")
        if loaded_view_dir_func and hasattr(loaded_view_dir_func, '__globals__'):
            helpers_after = [name for name in loaded_view_dir_func.__globals__.keys() 
                           if name.startswith('_') and callable(loaded_view_dir_func.__globals__.get(name))]
            print(f"Helper functions after save/load: {helpers_after}")
            has_convert_tool_inputs_after = '_convert_tool_inputs' in loaded_view_dir_func.__globals__
            print(f"_convert_tool_inputs available after: {has_convert_tool_inputs_after}")
        else:
            helpers_after = []
            has_convert_tool_inputs_after = False
        # Try to use view_dir after save/load (this should reproduce the bug)
        try:
            result_after = loaded_bot.tool_handler.function_map["view_dir"](".", target_extensions="['py']", max_lines=10)
            print("view_dir works AFTER save/load")
            after_works = True
        except Exception as e:
            print(f"view_dir FAILED after save/load: {e}")
            print(f"Error type: {type(e).__name__}")
            if "_convert_tool_inputs" in str(e):
                print("*** BUG REPRODUCED: _convert_tool_inputs helper function is missing! ***")
            after_works = False
        # Summary
        print(f"\nSUMMARY:")
        print(f"Before save/load: works={before_works}, _convert_tool_inputs={has_convert_tool_inputs_before}")
        print(f"After save/load:  works={after_works}, _convert_tool_inputs={has_convert_tool_inputs_after}")
        print(f"Helper functions lost: {set(helpers_before) - set(helpers_after)}")
        print(f"Bug reproduced: {before_works and not after_works}")
        return {
            "before_works": before_works,
            "after_works": after_works,
            "helpers_before": helpers_before,
            "helpers_after": helpers_after,
            "bug_reproduced": before_works and not after_works,
            "convert_tool_inputs_lost": has_convert_tool_inputs_before and not has_convert_tool_inputs_after
        }
if __name__ == "__main__":
    unittest.main(verbosity=2)
