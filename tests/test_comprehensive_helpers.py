#!/usr/bin/env python3
"""Comprehensive test for helper function preservation in save/load cycles."""
import os
import sys
import tempfile
import unittest
from types import ModuleType
from typing import Any, Dict

sys.path.insert(0, os.path.abspath("."))
from bots.foundation.anthropic_bots import AnthropicBot  # noqa: E402
from bots.foundation.base import Engines  # noqa: E402


class TestHelperPreservationComprehensive(unittest.TestCase):
    """Comprehensive test for helper function preservation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_file_with_nested_helpers(self) -> str:
        """Create a file with nested helper dependencies."""
        content = '''# Deep helper chain
def _level3_helper(x):
    return f"LEVEL3: {x}"
def _level2_helper(x):
    return _level3_helper(f"LEVEL2: {x}")
def _level1_helper(x):
    return _level2_helper(f"LEVEL1: {x}")
def nested_tool(input_text: str) -> str:
    """Tool with nested helper dependencies"""
    return _level1_helper(input_text)
'''
        path = os.path.join(self.temp_dir, "nested_helpers.py")
        with open(path, "w") as f:
            f.write(content)
        return path

    def create_module_with_helpers(self) -> ModuleType:
        """Create a module with helper functions."""
        import types

        module_content = '''
def _module_helper(data):
    return f"MODULE_HELPER: {data.upper()}"
def _another_module_helper(value):
    return f"ANOTHER: {value * 3}"
def module_tool(input_text: str, multiplier: int = 2) -> str:
    """Module tool with helpers"""
    result1 = _module_helper(input_text)
    result2 = _another_module_helper(multiplier)
    return f"{result1} + {result2}"
'''
        module = types.ModuleType("helper_module")
        module.__source__ = module_content
        exec(module_content, module.__dict__)
        return module

    def check_helper_availability(self, bot: AnthropicBot, tool_name: str) -> Dict[str, Any]:
        """Check if helper functions are available."""
        result = {
            "tool_exists": False,
            "helper_functions_available": False,
            "helper_function_names": [],
            "module_context_preserved": False,
            "error_details": [],
        }
        try:
            if tool_name in bot.tool_handler.function_map:
                result["tool_exists"] = True
                func = bot.tool_handler.function_map[tool_name]
                # Check for helper functions in globals
                if hasattr(func, "__globals__"):
                    globals_dict = func.__globals__
                    helper_funcs = [
                        name for name in globals_dict.keys() if name.startswith("_") and callable(globals_dict.get(name))
                    ]
                    result["helper_functions_available"] = len(helper_funcs) > 0
                    result["helper_function_names"] = helper_funcs
                # Check for module context
                if hasattr(func, "__module_context__"):
                    result["module_context_preserved"] = True
        except Exception as e:
            result["error_details"].append(f"Helper check error: {str(e)}")
        return result

    def test_all_scenarios(self):
        """Test helper preservation across all scenarios."""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE HELPER FUNCTION PRESERVATION TEST")
        print("=" * 60)
        test_cases = [
            {
                "name": "nested_helpers",
                "source": self.create_file_with_nested_helpers(),
                "tool_name": "nested_tool",
                "expected_result": "LEVEL3: LEVEL2: LEVEL1: test",
            },
            {
                "name": "module_helpers",
                "source": self.create_module_with_helpers(),
                "tool_name": "module_tool",
                "expected_result": "MODULE_HELPER: TEST + ANOTHER: 6",
            },
        ]
        scenarios = ["basic", "save_load", "save_load_twice"]
        results = []
        for test_case in test_cases:
            print(f"\nTesting {test_case['name']}...")
            for scenario in scenarios:
                print(f"  Scenario: {scenario}")
                try:
                    # Create bot and add tool
                    bot = AnthropicBot(engine=Engines.CLAUDE_3_5_SONNET)
                    if isinstance(test_case["source"], str):
                        bot.add_tool_from_file(test_case["source"])
                    else:
                        bot.add_tool_from_module(test_case["source"])
                    # Check helpers before
                    before = self.check_helper_availability(bot, test_case["tool_name"])
                    # Apply scenario
                    if scenario == "save_load":
                        temp_file = os.path.join(self.temp_dir, f"bot_{test_case['name']}.json")
                        bot.save(temp_file)
                        bot = AnthropicBot.load(temp_file)
                    elif scenario == "save_load_twice":
                        temp_file1 = os.path.join(self.temp_dir, f"bot_{test_case['name']}_1.json")
                        temp_file2 = os.path.join(self.temp_dir, f"bot_{test_case['name']}_2.json")
                        bot.save(temp_file1)
                        bot = AnthropicBot.load(temp_file1)
                        bot.save(temp_file2)
                        bot = AnthropicBot.load(temp_file2)
                    # Check helpers after
                    after = self.check_helper_availability(bot, test_case["tool_name"])
                    # Test tool functionality
                    tool_works = False
                    try:
                        if test_case["tool_name"] == "nested_tool":
                            result = bot.tool_handler.function_map[test_case["tool_name"]]("test")
                        else:
                            result = bot.tool_handler.function_map[test_case["tool_name"]]("test", 2)
                        tool_works = result == test_case["expected_result"]
                    except Exception as e:
                        print(f"    Tool execution error: {e}")
                    # Record results
                    test_result = {
                        "test_case": test_case["name"],
                        "scenario": scenario,
                        "tool_works": tool_works,
                        "helpers_before": before,
                        "helpers_after": after,
                        "helper_preservation": before["helper_functions_available"] == after["helper_functions_available"],
                    }
                    results.append(test_result)
                    # Print status
                    status = "PASS" if tool_works and test_result["helper_preservation"] else "FAIL"
                    print(f"    Helper preservation: {test_result['helper_preservation']}")
                    print(f"    Tool works: {tool_works}")
                    print(f"    Status: {status}")
                except Exception as e:
                    print(f"    ERROR: {e}")
                    results.append(
                        {
                            "test_case": test_case["name"],
                            "scenario": scenario,
                            "tool_works": False,
                            "helper_preservation": False,
                            "error": str(e),
                        }
                    )
        # Summary table
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"{'Test Case':<20} {'Basic':<8} {'Save+Load':<12} {'Save+Load2x':<12}")
        print("-" * 60)
        for test_case in test_cases:
            row = f"{test_case['name']:<20} "
            for scenario in scenarios:
                matching_results = [r for r in results if r["test_case"] == test_case["name"] and r["scenario"] == scenario]
                if matching_results:
                    result = matching_results[0]
                    if "error" in result:
                        status = "ERROR"
                    elif result["tool_works"] and result["helper_preservation"]:
                        status = "PASS"
                    else:
                        status = "FAIL"
                else:
                    status = "N/A"
                if scenario == "basic":
                    row += f"{status:<8} "
                elif scenario == "save_load":
                    row += f"{status:<12} "
                else:
                    row += f"{status:<12}"
            print(row)
        # Detailed failure analysis
        failures = [r for r in results if not (r.get("tool_works", False) and r.get("helper_preservation", False))]
        if failures:
            print(f"\nFAILURE ANALYSIS ({len(failures)} failures):")
            print("-" * 60)
            for failure in failures:
                print(f"Test: {failure['test_case']} | Scenario: {failure['scenario']}")
                if "error" in failure:
                    print(f"  Error: {failure['error']}")
                else:
                    print(f"  Tool works: {failure['tool_works']}")
                    print(f"  Helper preservation: {failure['helper_preservation']}")
                    if "helpers_before" in failure and "helpers_after" in failure:
                        before = failure["helpers_before"]
                        after = failure["helpers_after"]
                        print(f"  Helpers before: {before.get('helper_function_names', [])}")
                        print(f"  Helpers after: {after.get('helper_function_names', [])}")
        return results


if __name__ == "__main__":
    unittest.main(verbosity=2)
