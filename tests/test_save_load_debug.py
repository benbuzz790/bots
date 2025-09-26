#!/usr/bin/env python3
"""Debug test to trace helper function loss during save/load."""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath("."))

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines


class TestSaveLoadDebug(unittest.TestCase):
    """Debug test to trace helper function loss."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_debug_save_load_process(self):
        """Debug the save/load process step by step."""
        print("\nDEBUGGING SAVE/LOAD PROCESS...")

        # Create bot and add view_dir tool
        bot = AnthropicBot(name="DebugBot", model_engine=Engines.CLAUDE35_SONNET_20240620, max_tokens=1000)

        from bots.tools.code_tools import view_dir

        print(f"Original view_dir function: {view_dir}")
        print(f"Original view_dir module: {view_dir.__module__}")
        print(f"Original view_dir globals keys: {list(view_dir.__globals__.keys())[:10]}...")  # First 10 keys

        bot.add_tools(view_dir)

        # Check what got stored in the tool handler
        print("\nAfter adding tools:")
        print(f"Tool handler modules: {list(bot.tool_handler.modules.keys())}")
        print(f"Function map: {list(bot.tool_handler.function_map.keys())}")

        # Get the function from the tool handler
        stored_func = bot.tool_handler.function_map["view_dir"]
        print(f"Stored function: {stored_func}")
        print(f"Stored function module: {stored_func.__module__}")
        print(f"Stored function has __module_context__: {hasattr(stored_func, '__module_context__')}")

        if hasattr(stored_func, "__module_context__"):
            context = stored_func.__module_context__
            print(f"Module context: {context}")
            print(f"Module context namespace keys: {list(context.namespace.__dict__.keys())[:10]}...")

        # Check globals
        if hasattr(stored_func, "__globals__"):
            globals_keys = list(stored_func.__globals__.keys())
            helper_funcs = [k for k in globals_keys if k.startswith("_") and callable(stored_func.__globals__.get(k))]
            print(f"Stored function globals helper functions: {helper_funcs}")

        # Now save the bot
        print("\nSAVING BOT...")
        save_path = os.path.join(self.temp_dir, "debug_bot")
        bot.save(save_path)

        # Look at the saved data
        with open(save_path + ".bot", "r") as f:
            saved_data = json.load(f)

        print(f"Saved data keys: {list(saved_data.keys())}")
        if "tool_handler" in saved_data:
            th_data = saved_data["tool_handler"]
            print(f"Tool handler data keys: {list(th_data.keys())}")
            if "modules" in th_data:
                print(f"Modules in saved data: {list(th_data['modules'].keys())}")
                for module_path, module_data in th_data["modules"].items():
                    print(f"  Module {module_path}:")
                    print(f"    Keys: {list(module_data.keys())}")
                    if "globals" in module_data:
                        globals_keys = list(module_data["globals"].keys())
                        helper_globals = [k for k in globals_keys if k.startswith("_")]
                        print(f"    Globals helper functions: {helper_globals}")
                    if "source" in module_data:
                        source_lines = module_data["source"].split("\n")
                        helper_defs = [line for line in source_lines if line.strip().startswith("def _")]
                        print(f"    Helper function definitions in source: {len(helper_defs)}")

        # Now load the bot
        print("\nLOADING BOT...")
        loaded_bot = Bot.load(save_path + ".bot")

        # Check what we got back
        print(f"Loaded bot tool handler modules: {list(loaded_bot.tool_handler.modules.keys())}")
        print(f"Loaded bot function map: {list(loaded_bot.tool_handler.function_map.keys())}")

        loaded_func = loaded_bot.tool_handler.function_map["view_dir"]
        print(f"Loaded function: {loaded_func}")
        print(f"Loaded function module: {loaded_func.__module__}")
        print(f"Loaded function has __module_context__: {hasattr(loaded_func, '__module_context__')}")

        if hasattr(loaded_func, "__module_context__"):
            context = loaded_func.__module_context__
            print(f"Loaded module context: {context}")
            print(f"Loaded module context namespace keys: {list(context.namespace.__dict__.keys())[:10]}...")

        # Check globals
        if hasattr(loaded_func, "__globals__"):
            globals_keys = list(loaded_func.__globals__.keys())
            helper_funcs = [k for k in globals_keys if k.startswith("_") and callable(loaded_func.__globals__.get(k))]
            print(f"Loaded function globals helper functions: {helper_funcs}")

        print("\nDEBUG COMPLETE")
        return True


if __name__ == "__main__":
    unittest.main(verbosity=2)
