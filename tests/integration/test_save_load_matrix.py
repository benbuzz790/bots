#!/usr/bin/env python3
"""Comprehensive test matrix for save/load tool functionality.

Refactored to use MockBot for deterministic, fast testing focused on
tool save/load functionality rather than actual bot behavior.
"""

import os
import sys
import tempfile
import unittest
from types import ModuleType
from typing import Any, Callable, Dict

from bots.foundation.base import Bot, Engines
from bots.testing.mock_bot import MockBot

sys.path.insert(0, os.path.abspath("."))


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
        with open(test_file_path, "w") as f:
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
        return namespace["dynamic_test_tool"]

    def create_test_module(self) -> ModuleType:
        """Create a simple test module with tools."""
        import types

        # Create module content
        module_content = '''def module_test_tool(input_text: str) -> str:
    """Test tool from module"""
    return f"MODULE_RESULT: {input_text}"

def another_module_tool(data: str) -> str:
    """Another test tool from module"""
    return f"ANOTHER_MODULE_RESULT: {data}"
'''

        # Create the module
        module = types.ModuleType("test_module")
        # Don't set __file__ so it falls back to __source__
        module.__source__ = module_content

        # Execute the module content in the module's namespace
        exec(module_content, module.__dict__)

        return module

    def create_mock_bot(self, name: str = "TestBot") -> MockBot:
        """Create a mock bot for testing."""
        bot = MockBot(name=name, model_engine=Engines.CLAUDE35_HAIKU, max_tokens=1000, temperature=1)
        # Set a response pattern that indicates tool usage
        bot.set_response_pattern("Tool executed successfully with result: {user_input}")
        return bot

    def create_bot_with_tool(self, tool_method: str, tool_source: Any) -> MockBot:
        """Create a mock bot with the specified tool addition method."""
        bot = self.create_mock_bot("TestBot")
        bot.add_tools(tool_source)
        return bot

    def check_tool_preservation(self, bot: Bot, expected_tool_names: list) -> bool:
        """Check that tools are preserved correctly in the bot.

        Args:
            bot: Bot instance to check
            expected_tool_names: List of tool names that should be present

        Returns:
            True if all expected tools are present and functional
        """
        # Check tool count
        if len(bot.tool_handler.tools) != len(expected_tool_names):
            print(f"Tool count mismatch: expected {len(expected_tool_names)}, got {len(bot.tool_handler.tools)}")
            return False

        # Check each tool exists in function_map
        for tool_name in expected_tool_names:
            if tool_name not in bot.tool_handler.function_map:
                print(f"Tool {tool_name} not found in function_map")
                return False

            # Try to call the tool to verify it's functional
            try:
                func = bot.tool_handler.function_map[tool_name]
                result = func("test")
                if not isinstance(result, str):
                    print(f"Tool {tool_name} returned non-string result: {type(result)}")
                    return False
            except Exception as e:
                print(f"Tool {tool_name} failed to execute: {e}")
                return False

        return True

    def run_scenario(
        self,
        tool_method: str,
        tool_source: Any,
        scenario: str,
        expected_tool_names: list,
    ) -> Dict[str, Any]:
        """Run a specific test scenario.

        Args:
            tool_method: Method used to add tools (file, module, callable, dynamic)
            tool_source: The tool source (file path, module, function, etc.)
            scenario: Test scenario (basic, save_load, save_load_twice)
            expected_tool_names: List of tool names that should be present

        Returns:
            Dictionary with test results
        """
        result = {
            "tool_method": tool_method,
            "scenario": scenario,
            "success": False,
            "error": None,
            "details": {},
        }

        try:
            if scenario == "basic":
                # Basic tool preservation
                bot = self.create_bot_with_tool(tool_method, tool_source)
                result["success"] = self.check_tool_preservation(bot, expected_tool_names)
                result["details"]["tool_count"] = len(bot.tool_handler.tools)

            elif scenario == "save_load":
                # Save and load and check tool preservation
                bot = self.create_bot_with_tool(tool_method, tool_source)

                # Save the bot
                save_path = os.path.join(self.temp_dir, f"mock_{tool_method}_save_load")
                bot.save(save_path)

                # Load the bot
                loaded_bot = Bot.load(save_path + ".bot")
                result["success"] = self.check_tool_preservation(loaded_bot, expected_tool_names)
                result["details"]["original_tool_count"] = len(bot.tool_handler.tools)
                result["details"]["loaded_tool_count"] = len(loaded_bot.tool_handler.tools)

            elif scenario == "save_load_twice":
                # Save and load twice and check tool preservation
                bot = self.create_bot_with_tool(tool_method, tool_source)

                # First save/load
                save_path1 = os.path.join(self.temp_dir, f"mock_{tool_method}_save_load_1")
                bot.save(save_path1)
                loaded_bot1 = Bot.load(save_path1 + ".bot")

                # Second save/load
                save_path2 = os.path.join(self.temp_dir, f"mock_{tool_method}_save_load_2")
                loaded_bot1.save(save_path2)
                loaded_bot2 = Bot.load(save_path2 + ".bot")

                result["success"] = self.check_tool_preservation(loaded_bot2, expected_tool_names)
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

    def create_tool_with_helper_functions(self) -> str:
        """Create a test file with tools that depend on helper functions."""
        test_file_content = """# Helper function that should be preserved
def _internal_helper(data: str) -> str:
    return f"HELPER_PROCESSED: {data.upper()}"

def _another_helper(value: str) -> str:
    try:
        num_value = int(value)
        result = num_value * 2
        return f"NUMERIC_HELPER: {result}"
    except ValueError:
        return f"NUMERIC_HELPER: INVALID_INPUT"

# Main tool that uses helper functions
def tool_with_helpers(input_text: str, multiplier: str = "1") -> str:
    processed = _internal_helper(input_text)
    numeric_result = _another_helper(multiplier)
    return f"COMBINED: {processed} + {numeric_result}"
"""
        test_file_path = os.path.join(self.temp_dir, "helper_tools.py")
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
        return test_file_path

    def create_module_with_complex_dependencies(self) -> ModuleType:
        """Create a module with complex helper function dependencies."""
        import types

        module_content = """import os
import json
from typing import Dict, Any

# Helper functions
def _validate_input(data: str) -> bool:
    return len(data) > 0 and data.strip() != ""

def _format_output(result: Dict[str, Any]) -> str:
    return json.dumps(result, indent=2)

# Main tools that depend on helpers
def complex_tool(input_data: str) -> str:
    if not _validate_input(input_data):
        return "ERROR: Invalid input"

    result = {
        "processed_data": input_data.upper(),
        "status": "success"
    }

    return _format_output(result)
"""

        module = types.ModuleType("complex_module")
        module.__source__ = module_content
        exec(module_content, module.__dict__)
        return module

    def check_helper_function_availability(self, bot: Bot, tool_name: str) -> Dict[str, Any]:
        """Check if helper functions are available after save/load."""
        result = {
            "tool_exists": False,
            "helper_functions_available": False,
            "function_map_complete": False,
            "module_context_preserved": False,
            "error_details": [],
        }

        try:
            # Check if tool exists in function map
            if tool_name in bot.tool_handler.function_map:
                result["tool_exists"] = True
                func = bot.tool_handler.function_map[tool_name]

                # Try to inspect the function's module/globals for helper functions
                if hasattr(func, "__globals__"):
                    globals_dict = func.__globals__
                    # Look for helper functions (typically start with _)
                    helper_funcs = [
                        name for name in globals_dict.keys() if name.startswith("_") and callable(globals_dict.get(name))
                    ]
                    result["helper_functions_available"] = len(helper_funcs) > 0
                    result["helper_function_names"] = helper_funcs

                # Check if function has module context
                if hasattr(func, "__module_context__"):
                    result["module_context_preserved"] = True

                result["function_map_complete"] = True

        except Exception as e:
            result["error_details"].append(f"Helper check error: {str(e)}")

        return result

    def test_import_duplication_bug(self):
        """Test that imports are not duplicated on repeated save/load cycles.

        This test specifically checks for the bug where _add_imports_to_source
        keeps adding imports to source that already has imports, causing them
        to accumulate on each save/load cycle.
        """
        print("\n" + "=" * 80)
        print("TESTING IMPORT DUPLICATION BUG")
        print("=" * 80)

        # Create a module with imports
        import types

        module_content = """import os
import json
from typing import Dict, Any

def test_tool(input_data: str) -> str:
    result = {"data": input_data}
    return json.dumps(result)
"""

        module = types.ModuleType("import_test_module")
        module.__source__ = module_content
        exec(module_content, module.__dict__)

        # Create bot and add the module
        bot = self.create_mock_bot("ImportTestBot")
        bot.add_tools(module)

        # Track source line counts through save/load cycles
        source_line_counts = []
        import_line_counts = []

        # Get initial source
        module_context = list(bot.tool_handler.modules.values())[0]
        initial_source = module_context.source
        source_line_counts.append(len(initial_source.split("\n")))
        import_line_counts.append(initial_source.count("import"))

        print(f"\nInitial source ({source_line_counts[0]} lines, {import_line_counts[0]} import statements):")
        for i, line in enumerate(initial_source.split("\n")[:10], 1):
            print(f"  {i:2d}: {line}")

        # Perform multiple save/load cycles
        num_cycles = 3
        current_bot = bot

        for cycle in range(1, num_cycles + 1):
            print(f"\n--- Save/Load Cycle {cycle} ---")

            # Save
            save_path = os.path.join(self.temp_dir, f"import_test_cycle_{cycle}")
            current_bot.save(save_path)

            # Load
            loaded_bot = Bot.load(save_path + ".bot")

            # Get source from loaded bot
            module_context = list(loaded_bot.tool_handler.modules.values())[0]
            loaded_source = module_context.source
            line_count = len(loaded_source.split("\n"))
            import_count = loaded_source.count("import")

            source_line_counts.append(line_count)
            import_line_counts.append(import_count)

            print(f"After cycle {cycle}: {line_count} lines, {import_count} import statements")
            print("First 15 lines:")
            for i, line in enumerate(loaded_source.split("\n")[:15], 1):
                print(f"  {i:2d}: {line}")

            # Check if tool still works
            try:
                func = loaded_bot.tool_handler.function_map["test_tool"]
                result = func("test")
                tool_works = "test" in result
                print(f"Tool works: {tool_works}")
            except Exception as e:
                print(f"Tool FAILED: {e}")
                tool_works = False

            current_bot = loaded_bot

        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        print(f"Source line count progression: {source_line_counts}")
        print(f"Import statement count progression: {import_line_counts}")

        # Check for duplication
        line_count_stable = len(set(source_line_counts)) == 1
        import_count_stable = len(set(import_line_counts)) == 1

        print(f"\nLine count stable: {line_count_stable}")
        print(f"Import count stable: {import_count_stable}")

        if not line_count_stable:
            print(f"WARNING: Line count increased from {source_line_counts[0]} to {source_line_counts[-1]}")
            growth_per_cycle = [(source_line_counts[i] - source_line_counts[i - 1]) for i in range(1, len(source_line_counts))]
            print(f"  Growth per cycle: {growth_per_cycle}")

        if not import_count_stable:
            print(f"WARNING: Import count increased from {import_line_counts[0]} to {import_line_counts[-1]}")
            growth_per_cycle = [(import_line_counts[i] - import_line_counts[i - 1]) for i in range(1, len(import_line_counts))]
            print(f"  Growth per cycle: {growth_per_cycle}")

        # Test should fail if imports are duplicating
        self.assertTrue(
            line_count_stable and import_count_stable,
            f"Import duplication detected! Line counts: {source_line_counts}, " f"Import counts: {import_line_counts}",
        )

    def test_helper_function_preservation(self):
        """Test that helper functions are preserved across save/load cycles."""
        print("\n" + "=" * 60)
        print("TESTING HELPER FUNCTION PRESERVATION")
        print("=" * 60)

        test_cases = [
            {
                "name": "file_with_helpers",
                "source": self.create_tool_with_helper_functions(),
                "tool_name": "tool_with_helpers",
            },
            {
                "name": "module_with_complex_deps",
                "source": self.create_module_with_complex_dependencies(),
                "tool_name": "complex_tool",
            },
        ]

        scenarios = ["basic", "save_load", "save_load_twice"]
        results = []

        for test_case in test_cases:
            for scenario in scenarios:
                print(f"\nTesting {test_case['name']} + {scenario}...")

                try:
                    # Create bot and add tools
                    bot = self.create_mock_bot("HelperTestBot")
                    bot.add_tools(test_case["source"])

                    # Check helper functions before save/load
                    before_helpers = self.check_helper_function_availability(bot, test_case["tool_name"])

                    if scenario == "basic":
                        # Just test basic functionality
                        after_helpers = before_helpers
                        # Test that the tool actually works
                        func = bot.tool_handler.function_map[test_case["tool_name"]]
                        try:
                            result = func("test")
                            success = isinstance(result, str) and len(result) > 0
                        except Exception as e:
                            print(f"  Tool execution failed: {e}")
                            success = False

                    elif scenario == "save_load":
                        # Save and load once
                        save_path = os.path.join(self.temp_dir, f"{test_case['name']}_save_load")
                        bot.save(save_path)
                        loaded_bot = Bot.load(save_path + ".bot")

                        # Check helper functions after save/load
                        after_helpers = self.check_helper_function_availability(loaded_bot, test_case["tool_name"])
                        # Test that the tool actually works
                        func = loaded_bot.tool_handler.function_map[test_case["tool_name"]]
                        try:
                            result = func("test")
                            success = isinstance(result, str) and len(result) > 0
                        except Exception as e:
                            print(f"  Tool execution failed: {e}")
                            success = False

                    elif scenario == "save_load_twice":
                        # Save and load twice
                        save_path1 = os.path.join(self.temp_dir, f"{test_case['name']}_save_load_1")
                        bot.save(save_path1)
                        loaded_bot1 = Bot.load(save_path1 + ".bot")

                        save_path2 = os.path.join(self.temp_dir, f"{test_case['name']}_save_load_2")
                        loaded_bot1.save(save_path2)
                        loaded_bot2 = Bot.load(save_path2 + ".bot")

                        # Check helper functions after double save/load
                        after_helpers = self.check_helper_function_availability(loaded_bot2, test_case["tool_name"])
                        # Test that the tool actually works
                        func = loaded_bot2.tool_handler.function_map[test_case["tool_name"]]
                        try:
                            result = func("test")
                            success = isinstance(result, str) and len(result) > 0
                        except Exception as e:
                            print(f"  Tool execution failed: {e}")
                            success = False

                    # Record results
                    result = {
                        "test_case": test_case["name"],
                        "scenario": scenario,
                        "tool_works": success,
                        "helpers_before": before_helpers,
                        "helpers_after": after_helpers,
                        "helper_preservation": (
                            before_helpers["helper_functions_available"] == after_helpers["helper_functions_available"]
                            and before_helpers["module_context_preserved"] == after_helpers["module_context_preserved"]
                        ),
                    }
                    results.append(result)

                    # Print status
                    status = "PASS" if success and result["helper_preservation"] else "FAIL"
                    print(f"  Tool Function: {'WORKS' if success else 'BROKEN'}")
                    print(f"  Helper Preservation: {'PRESERVED' if result['helper_preservation'] else 'LOST'}")
                    print(f"  Overall: {status}")

                    if not result["helper_preservation"]:
                        print(f"    Before helpers: {before_helpers['helper_functions_available']}")
                        print(f"    After helpers: {after_helpers['helper_functions_available']}")
                        if after_helpers.get("error_details"):
                            print(f"    Errors: {after_helpers['error_details']}")

                except Exception as e:
                    print(f"  ERROR: {str(e)}")
                    results.append(
                        {
                            "test_case": test_case["name"],
                            "scenario": scenario,
                            "tool_works": False,
                            "helper_preservation": False,
                            "error": str(e),
                        }
                    )

        # Summary
        print("\n" + "=" * 60)
        print("HELPER FUNCTION PRESERVATION SUMMARY")
        print("=" * 60)

        print(f"{'Test Case':<25} {'Basic':<8} {'Save+Load':<12} {'Save+Load2x':<12}")
        print("-" * 65)

        for test_case in test_cases:
            row = f"{test_case['name']:<25} "
            for scenario in scenarios:
                result = next(
                    (r for r in results if r["test_case"] == test_case["name"] and r["scenario"] == scenario),
                    None,
                )
                if result:
                    if result.get("tool_works") and result.get("helper_preservation"):
                        status = "PASS"
                    elif result.get("tool_works"):
                        status = "PARTIAL"  # Tool works but helpers lost
                    else:
                        status = "FAIL"
                else:
                    status = "ERROR"

                if scenario == "basic":
                    row += f"{status:<8} "
                else:
                    row += f"{status:<12} "
            print(row)

        # Detailed failure analysis
        failures = [r for r in results if not (r.get("tool_works", False) and r.get("helper_preservation", False))]
        if failures:
            print(f"\nFAILURES DETECTED: {len(failures)}")
            print("\nDETAILED FAILURE ANALYSIS:")
            for failure in failures:
                print(f"\n{failure['test_case']} + {failure['scenario']}:")
                if failure.get("error"):
                    print(f"  Error: {failure['error']}")
                else:
                    print(f"  Tool Works: {failure.get('tool_works', False)}")
                    print(f"  Helpers Preserved: {failure.get('helper_preservation', False)}")
                    if failure.get("helpers_before") and failure.get("helpers_after"):
                        before = failure["helpers_before"]
                        after = failure["helpers_after"]
                        print(f"  Helper Functions Before: {before.get('helper_functions_available', False)}")
                        print(f"  Helper Functions After: {after.get('helper_functions_available', False)}")
                        if before.get("helper_function_names"):
                            print(f"  Helper Names Before: {before['helper_function_names']}")
                        if after.get("helper_function_names"):
                            print(f"  Helper Names After: {after['helper_function_names']}")

        return results

    def test_matrix(self):
        """Run the complete test matrix using MockBot."""

        # Define test matrix dimensions
        tool_methods = {
            "file": {
                "source": self.create_test_file(),
                "expected_tools": ["file_test_tool"],
            },
            "module": {
                "source": self.create_test_module(),
                "expected_tools": ["module_test_tool", "another_module_tool"],
            },
            "callable": {
                "source": self.create_callable_tool(),
                "expected_tools": ["callable_test_tool"],
            },
            "dynamic": {
                "source": self.create_dynamic_tool(),
                "expected_tools": ["dynamic_test_tool"],
            },
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
                    tool_config["expected_tools"],
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
        print("\n" + "=" * 80)
        print("SUMMARY MATRIX")
        print("=" * 80)

        print(f"{'Tool Method':<12} {'Basic':<8} {'Save+Load':<12} {'Save+Load2x':<12}")
        print("-" * 50)

        for tool_method in tool_methods.keys():
            row = f"{tool_method:<12} "
            for scenario in scenarios:
                # Find result for this combination
                result = next(
                    (r for r in results if r["tool_method"] == tool_method and r["scenario"] == scenario),
                    None,
                )
                status = "PASS" if result and result["success"] else "FAIL"
                if scenario == "basic":
                    row += f"{status:<8} "
                else:
                    row += f"{status:<12} "
            print(row)

        # Overall summary
        failures = [r for r in results if not r["success"]]
        print("\nOVERALL SUMMARY:")
        print(f"Total tests: {len(results)}")
        print(f"Failures: {len(failures)}")
        print(f"Success rate: {(len(results) - len(failures)) / len(results) * 100:.1f}%")

        # Show failure details
        if failures:
            print("\nFAILURE DETAILS:")
            for failure in failures:
                print(f"  {failure['tool_method']} + {failure['scenario']}: {failure['error']}")

        # All tests should pass with MockBot (deterministic behavior)
        self.assertEqual(
            len(failures),
            0,
            f"Found {len(failures)} failures in test matrix. "
            f"Success rate: {(len(results) - len(failures)) / len(results) * 100:.1f}%",
        )

    def test_cli_save_load(self):
        """Test that CLI can be saved and loaded, preserving its state and configuration."""
        print("\n" + "=" * 60)
        print("TESTING CLI SAVE/LOAD")
        print("=" * 60)

        from bots.dev.cli import CLI

        # Create a CLI instance with custom configuration
        cli = CLI()

        # Customize the CLI state
        cli.last_user_message = "Test message for CLI"
        cli.pending_prefill = "Test prefill content"
        cli.context.config.verbose = True
        cli.context.config.auto_stash = True

        # Add a labeled node to the context
        bot = self.create_mock_bot("CLITestBot")
        bot.add_tools(self.create_test_file())
        cli.context.bot_instance = bot

        # Create a conversation with labeled nodes
        bot.respond("Hello")
        cli.context.labeled_nodes["test_label"] = bot.conversation

        # Test tool operation before save
        print("\nTesting tool before save...")
        tool_func_before = bot.tool_handler.function_map["file_test_tool"]
        result_before = tool_func_before("test_input")
        print(f"Tool result before save: {result_before}")
        tool_works_before = "FILE_RESULT: test_input" in result_before

        # Save the bot (which contains the CLI state indirectly through conversation)
        save_path = os.path.join(self.temp_dir, "cli_test_bot")
        bot.save(save_path)

        # Load the bot back
        loaded_bot = Bot.load(save_path + ".bot")

        # Create a new CLI and restore state
        new_cli = CLI()
        new_cli.context.bot_instance = loaded_bot

        # Verify the bot was loaded correctly
        print(f"\nOriginal bot tools: {len(bot.tool_handler.tools)}")
        print(f"Loaded bot tools: {len(loaded_bot.tool_handler.tools)}")

        # Check that tools are preserved
        tools_preserved = self.check_tool_preservation(loaded_bot, ["file_test_tool"])

        # Test tool operation after load
        print("\nTesting tool after load...")
        tool_func_after = loaded_bot.tool_handler.function_map["file_test_tool"]
        result_after = tool_func_after("test_input")
        print(f"Tool result after load: {result_after}")
        tool_works_after = "FILE_RESULT: test_input" in result_after

        # Check that conversation is preserved
        conversation_preserved = loaded_bot.conversation is not None

        print(f"\nTools preserved: {tools_preserved}")
        print(f"Tool works before save: {tool_works_before}")
        print(f"Tool works after load: {tool_works_after}")
        print(f"Conversation preserved: {conversation_preserved}")

        # Overall test result - all conditions must pass
        test_passed = tools_preserved and tool_works_before and tool_works_after and conversation_preserved

        print(f"\nCLI Save/Load Test: {'PASS' if test_passed else 'FAIL'}")

        self.assertTrue(test_passed, "CLI save/load test failed")

        return test_passed


if __name__ == "__main__":
    unittest.main(verbosity=2)
