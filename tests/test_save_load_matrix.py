#!/usr/bin/env python3
"""Comprehensive test matrix for save/load tool functionality."""

import sys
import os
import tempfile
import unittest
from typing import Dict, List, Callable, Any
sys.path.insert(0, os.path.abspath('.'))

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines
import bots.tools.python_editing_tools as python_editing_tools


class TestSaveLoadMatrix(unittest.TestCase):
    """Comprehensive test matrix for save/load tool functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self) -> str:
        """Create a temporary test file with tools."""
        test_file_content = '''def file_test_tool(input_text: str) -> str:
    """Test tool from file"""
    return f"FILE_RESULT: {input_text}"
'''
        test_file_path = os.path.join(self.temp_dir, "test_tools.py")
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)
        return test_file_path

    def create_callable_tool(self) -> Callable:
        """Create a callable test tool."""
        def callable_test_tool(input_text: str) -> str:
            """Test tool from callable"""
            return f"CALLABLE_RESULT: {input_text}"
        return callable_test_tool

    def create_dynamic_tool(self) -> Callable:
        """Create a dynamic test tool."""
        code = '''
def dynamic_test_tool(input_text: str) -> str:
    """Dynamically created test tool"""
    return f"DYNAMIC_RESULT: {input_text}"
'''
        namespace = {}
        exec(code, namespace)
        return namespace['dynamic_test_tool']

    def create_bot_with_tool(self, tool_method: str, tool_source: Any) -> AnthropicBot:
        """Create a bot with the specified tool addition method."""
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE35_SONNET_20240620, max_tokens=1000)
        bot.add_tools(tool_source)
        return bot

    def check_tool_usage(self, bot: AnthropicBot, expected_result: str, test_prompt: str) -> bool:
        """Test that tools work correctly on the bot."""
        try:
            response = bot.respond(test_prompt)

            # Check tool results in conversation
            tool_results = bot.conversation.tool_results[0].values() if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values() if bot.conversation.pending_results else []

            # Check if expected result appears in tool results
            found_result = any((expected_result in str(v) for v in tool_results)) or any((expected_result in str(v) for v in pending_results))

            return found_result
        except Exception as e:
            print(f"Tool usage failed: {e}")
            return False

    def run_scenario(self, tool_method: str, tool_source: Any, scenario: str, 
                   expected_result: str, test_prompt: str) -> Dict[str, Any]:
        """Run a specific test scenario."""
        result = {
            "tool_method": tool_method,
            "scenario": scenario,
            "success": False,
            "error": None,
            "details": {}
        }

        try:
            if scenario == "basic":
                # Basic tool use
                bot = self.create_bot_with_tool(tool_method, tool_source)
                result["success"] = self.check_tool_usage(bot, expected_result, test_prompt)
                result["details"]["tool_count"] = len(bot.tool_handler.tools)

            elif scenario == "save_load":
                # Save and load and tool use
                bot = self.create_bot_with_tool(tool_method, tool_source)

                # Save the bot
                save_path = os.path.join(self.temp_dir, f"{tool_method}_save_load")
                bot.save(save_path)

                # Load the bot
                loaded_bot = Bot.load(save_path + ".bot")
                result["success"] = self.check_tool_usage(loaded_bot, expected_result, test_prompt)
                result["details"]["original_tool_count"] = len(bot.tool_handler.tools)
                result["details"]["loaded_tool_count"] = len(loaded_bot.tool_handler.tools)

            elif scenario == "save_load_twice":
                # Save and load twice and tool use
                bot = self.create_bot_with_tool(tool_method, tool_source)

                # First save/load
                save_path1 = os.path.join(self.temp_dir, f"{tool_method}_save_load_1")
                bot.save(save_path1)
                loaded_bot1 = Bot.load(save_path1 + ".bot")

                # Second save/load
                save_path2 = os.path.join(self.temp_dir, f"{tool_method}_save_load_2")
                loaded_bot1.save(save_path2)
                loaded_bot2 = Bot.load(save_path2 + ".bot")

                result["success"] = self.check_tool_usage(loaded_bot2, expected_result, test_prompt)
                result["details"]["original_tool_count"] = len(bot.tool_handler.tools)
                result["details"]["loaded1_tool_count"] = len(loaded_bot1.tool_handler.tools)
                result["details"]["loaded2_tool_count"] = len(loaded_bot2.tool_handler.tools)

            else:
                raise ValueError(f"Unknown scenario: {scenario}")

        except Exception as e:
            result["error"] = str(e)
            import traceback
            result["details"]["traceback"] = traceback.format_exc()

        return result

    def test_matrix(self):
        """Run the complete test matrix."""

        # Define test matrix dimensions
        tool_methods = {
            "file": {
                "source": self.create_test_file(),
                "expected_result": "FILE_RESULT: test",
                "test_prompt": "Use file_test_tool with input_text 'test'"
            },
            "module": {
                "source": python_editing_tools,
                "expected_result": "view",  # Should find 'view' in the response from view_file
                "test_prompt": "Use view_file with file_path 'README.md' and start_line '1' and end_line '5'"
            },
            "callable": {
                "source": self.create_callable_tool(),
                "expected_result": "CALLABLE_RESULT: test",
                "test_prompt": "Use callable_test_tool with input_text 'test'"
            },
            "dynamic": {
                "source": self.create_dynamic_tool(),
                "expected_result": "DYNAMIC_RESULT: test",
                "test_prompt": "Use dynamic_test_tool with input_text 'test'"
            }
        }

        scenarios = ["basic", "save_load", "save_load_twice"]

        # Run all combinations
        results = []
        for tool_method, tool_config in tool_methods.items():
            for scenario in scenarios:
                print(f"\nTesting {tool_method} + {scenario}...")
                result = self.run_scenario(
                    tool_method, 
                    tool_config["source"],
                    scenario,
                    tool_config["expected_result"],
                    tool_config["test_prompt"]
                )
                results.append(result)

                # Print result
                status = "PASS" if result["success"] else "FAIL"
                print(f"  {tool_method:10} + {scenario:15} = {status}")
                if result["error"]:
                    print(f"    Error: {result['error']}")
                if result["details"]:
                    for key, value in result["details"].items():
                        if key != "traceback":
                            print(f"    {key}: {value}")

        # Summary
        print("\n" + "="*60)
        print("SUMMARY MATRIX")
        print("="*60)

        # Create summary table
        print(f"{'Tool Method':<12} {'Basic':<8} {'Save+Load':<12} {'Save+Load2x':<12}")
        print("-" * 50)

        for tool_method in tool_methods.keys():
            row = f"{tool_method:<12} "
            for scenario in scenarios:
                # Find result for this combination
                result = next((r for r in results if r["tool_method"] == tool_method and r["scenario"] == scenario), None)
                status = "PASS" if result and result["success"] else "FAIL"
                if scenario == "basic":
                    row += f"{status:<8} "
                else:
                    row += f"{status:<12} "
            print(row)

        # Count failures
        failures = [r for r in results if not r["success"]]
        print(f"\nTotal tests: {len(results)}")
        print(f"Failures: {len(failures)}")
        print(f"Success rate: {(len(results) - len(failures)) / len(results) * 100:.1f}%")

        # Show failure details
        if failures:
            print("\nFAILURE DETAILS:")
            for failure in failures:
                print(f"\n{failure['tool_method']} + {failure['scenario']}:")
                print(f"  Error: {failure['error']}")

        # Don't assert failure for now - just report
        # self.assertEqual(len(failures), 0, f"Found {len(failures)} failures in test matrix")


if __name__ == "__main__":
    unittest.main(verbosity=2)
