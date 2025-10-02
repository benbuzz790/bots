#!/usr/bin/env python3
"""Comprehensive test matrix for save/load tool functionality."""

import os
import sys
import tempfile
import unittest
from types import ModuleType
from typing import Any, Callable, Dict

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.gemini_bots import GeminiBot
from bots.foundation.base import Bot, Engines

sys.path.insert(0, os.path.abspath("."))

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines

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


    def create_bot_by_provider(self, provider: str, name: str = "TestBot") -> Bot:
        """Create a bot with the specified provider."""
        if provider == "anthropic":
            # Use real API key if available
            if "ANTHROPIC_API_KEY" in os.environ:
                return AnthropicBot(name=name, model_engine=Engines.CLAUDE35_HAIKU, max_tokens=1000, temperature=1)
            else:
                import unittest
                raise unittest.SkipTest("No ANTHROPIC_API_KEY available")
        elif provider == "openai":
            # Use real API key if available
            if "OPENAI_API_KEY" in os.environ:
                bot = ChatGPT_Bot(name=name, model_engine=Engines.GPT4, max_tokens=1000, temperature=1)
                # OpenAI requires a system message to reliably use tools
                bot.set_system_message("You are a helpful assistant. When asked to use a tool, call it directly without asking for clarification.")
                return bot
            else:
                import unittest
                raise unittest.SkipTest("No OPENAI_API_KEY available")
        elif provider == "gemini":
            # Use real API key if available
            if "GOOGLE_API_KEY" in os.environ or "GEMINI_API_KEY" in os.environ:
                return GeminiBot(name=name, model_engine=Engines.GEMINI25_FLASH, max_tokens=1000, temperature=1)
            else:
                import unittest
                raise unittest.SkipTest("No GOOGLE_API_KEY or GEMINI_API_KEY available")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def create_bot_with_tool(self, tool_method: str, tool_source: Any, provider: str = "anthropic") -> Bot:
        """Create a bot with the specified tool addition method and provider."""
        bot = self.create_bot_by_provider(provider, "TestBot")
        if tool_method == "module":
            import inspect

            functions = [name for name, obj in inspect.getmembers(tool_source, inspect.isfunction)]
            print(f"DEBUG: Module functions: {functions}")
        bot.add_tools(tool_source)
        if tool_method == "module":
            print(f"DEBUG: After adding tools, bot has {len(bot.tool_handler.tools)} tools")
        return bot

    def check_tool_usage(self, bot: Bot, expected_result: str, test_prompt: str) -> bool:
        """Test that tools work correctly on the bot."""
        try:
            response = bot.respond(test_prompt)

            # Traverse the entire conversation tree to find tool execution evidence
            def find_tool_evidence(node):
                """Recursively search conversation tree for tool calls and results."""
                evidence = {
                    "tool_calls": [],
                    "tool_results": [],
                    "pending_results": []
                }
                
                # Check current node
                if hasattr(node, "tool_calls") and node.tool_calls:
                    evidence["tool_calls"].extend(node.tool_calls)
                if hasattr(node, "tool_results") and node.tool_results:
                    evidence["tool_results"].extend(node.tool_results)
                if hasattr(node, "pending_results") and node.pending_results:
                    evidence["pending_results"].extend(node.pending_results)
                
                # Check all replies recursively
                if hasattr(node, "replies"):
                    for reply in node.replies:
                        child_evidence = find_tool_evidence(reply)
                        evidence["tool_calls"].extend(child_evidence["tool_calls"])
                        evidence["tool_results"].extend(child_evidence["tool_results"])
                        evidence["pending_results"].extend(child_evidence["pending_results"])
                
                return evidence

            # Start from conversation root and find all tool evidence
            root = bot.conversation._find_root()
            evidence = find_tool_evidence(root)
            
            # Check if any tools were executed
            tool_executed = (len(evidence["tool_calls"]) > 0 or 
                           len(evidence["tool_results"]) > 0 or 
                           len(evidence["pending_results"]) > 0)
            
            if not tool_executed:
                return False
            
            # Check if expected result appears in any tool results
            if ":" in expected_result:
                core_expected = expected_result.split(":", 1)[1].strip()
            else:
                core_expected = expected_result
            
            all_results = evidence["tool_results"] + evidence["pending_results"]
            for result in all_results:
                result_str = str(result)
                if expected_result in result_str or core_expected in result_str:
                    return True

            return False
        except Exception as e:
            print(f"Tool usage failed: {e}")
            return False

    def run_scenario(
        self, tool_method: str, tool_source: Any, scenario: str, expected_result: str, test_prompt: str, provider: str = "anthropic"
    ) -> Dict[str, Any]:
        """Run a specific test scenario."""
        result = {"tool_method": tool_method, "scenario": scenario, "provider": provider, "success": False, "error": None, "details": {}}

        try:
            if scenario == "basic":
                # Basic tool use
                bot = self.create_bot_with_tool(tool_method, tool_source, provider)
                result["success"] = self.check_tool_usage(bot, expected_result, test_prompt)
                result["details"]["tool_count"] = len(bot.tool_handler.tools)

            elif scenario == "save_load":
                # Save and load and tool use
                bot = self.create_bot_with_tool(tool_method, tool_source, provider)

                # Save the bot
                save_path = os.path.join(self.temp_dir, f"{provider}_{tool_method}_save_load")
                bot.save(save_path)

                # Load the bot
                loaded_bot = Bot.load(save_path + ".bot")
                result["success"] = self.check_tool_usage(loaded_bot, expected_result, test_prompt)
                result["details"]["original_tool_count"] = len(bot.tool_handler.tools)
                result["details"]["loaded_tool_count"] = len(loaded_bot.tool_handler.tools)

            elif scenario == "save_load_twice":
                # Save and load twice and tool use
                bot = self.create_bot_with_tool(tool_method, tool_source, provider)

                # First save/load
                save_path1 = os.path.join(self.temp_dir, f"{provider}_{tool_method}_save_load_1")
                bot.save(save_path1)
                loaded_bot1 = Bot.load(save_path1 + ".bot")

                # Second save/load
                save_path2 = os.path.join(self.temp_dir, f"{provider}_{tool_method}_save_load_2")
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
                "test_prompt": "Use tool_with_helpers with input_text 'test' and multiplier 2",
                "expected_result": "COMBINED: HELPER_PROCESSED: TEST + NUMERIC_HELPER: 4",
            },
            {
                "name": "module_with_complex_deps",
                "source": self.create_module_with_complex_dependencies(),
                "tool_name": "complex_tool",
                "test_prompt": "Use complex_tool with input_data 'test_data'",
                "expected_result": "processed_data",  # Should contain JSON with this key
            },
        ]

        scenarios = ["basic", "save_load", "save_load_twice"]
        results = []

        for test_case in test_cases:
            for scenario in scenarios:
                print(f"\nTesting {test_case['name']} + {scenario}...")

                try:
                    # Create bot and add tools
                    bot = self.create_bot_by_provider("anthropic", "HelperTestBot")
                    bot.add_tools(test_case["source"])

                    # Check helper functions before save/load
                    before_helpers = self.check_helper_function_availability(bot, test_case["tool_name"])

                    if scenario == "basic":
                        # Just test basic functionality
                        success = self.check_tool_usage(bot, test_case["expected_result"], test_case["test_prompt"])
                        after_helpers = before_helpers

                    elif scenario == "save_load":
                        # Save and load once
                        save_path = os.path.join(self.temp_dir, f"{test_case['name']}_save_load")
                        bot.save(save_path)
                        loaded_bot = Bot.load(save_path + ".bot")

                        # Check helper functions after save/load
                        after_helpers = self.check_helper_function_availability(loaded_bot, test_case["tool_name"])
                        success = self.check_tool_usage(loaded_bot, test_case["expected_result"], test_case["test_prompt"])

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
                        success = self.check_tool_usage(loaded_bot2, test_case["expected_result"], test_case["test_prompt"])

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
                result = next((r for r in results if r["test_case"] == test_case["name"] and r["scenario"] == scenario), None)
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
        """Run the complete test matrix."""

        # Define test matrix dimensions
        providers = ["anthropic", "openai", "gemini"]

        tool_methods = {
            "file": {
                "source": self.create_test_file(),
                "expected_result": "FILE_RESULT: test",
                "test_prompt": "Use file_test_tool with input_text 'test'",
            },
            "module": {
                "source": self.create_test_module(),
                "expected_result": "MODULE_RESULT: test",
                "test_prompt": "Use module_test_tool with input_text 'test'",
            },
            "callable": {
                "source": self.create_callable_tool(),
                "expected_result": "CALLABLE_RESULT: test",
                "test_prompt": "Use callable_test_tool with input_text 'test'",
            },
            "dynamic": {
                "source": self.create_dynamic_tool(),
                "expected_result": "DYNAMIC_RESULT: test",
                "test_prompt": "Use dynamic_test_tool with input_text 'test'",
            },
        }

        scenarios = ["basic", "save_load", "save_load_twice"]

        # Run all combinations
        results = []
        for provider in providers:
            for tool_method, tool_config in tool_methods.items():
                for scenario in scenarios:
                    print(f"\nTesting {provider} + {tool_method} + {scenario}...")
                    result = self.run_scenario(
                        tool_method, tool_config["source"], scenario, tool_config["expected_result"], tool_config["test_prompt"], provider
                    )
                    results.append(result)

                    # Print result
                    status = "PASS" if result["success"] else "FAIL"
                    print(f"  {provider:10} + {tool_method:10} + {scenario:15} = {status}")
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

        # Create summary table by provider
        for provider in providers:
            print(f"\n{provider.upper()} PROVIDER:")
            print(f"{'Tool Method':<12} {'Basic':<8} {'Save+Load':<12} {'Save+Load2x':<12}")
            print("-" * 50)

            for tool_method in tool_methods.keys():
                row = f"{tool_method:<12} "
                for scenario in scenarios:
                    # Find result for this combination
                    result = next((r for r in results if r["provider"] == provider and r["tool_method"] == tool_method and r["scenario"] == scenario), None)
                    status = "PASS" if result and result["success"] else "FAIL"
                    if scenario == "basic":
                        row += f"{status:<8} "
                    else:
                        row += f"{status:<12} "
                print(row)

        # Overall summary
        failures = [r for r in results if not r["success"]]
        print(f"\nOVERALL SUMMARY:")
        print(f"Total tests: {len(results)}")
        print(f"Failures: {len(failures)}")
        print(f"Success rate: {(len(results) - len(failures)) / len(results) * 100:.1f}%")

        # Show failure details by provider
        if failures:
            print("\nFAILURE DETAILS BY PROVIDER:")
            for provider in providers:
                provider_failures = [f for f in failures if f["provider"] == provider]
                if provider_failures:
                    print(f"\n{provider.upper()} FAILURES ({len(provider_failures)}):")
                    for failure in provider_failures:
                        print(f"  {failure['tool_method']} + {failure['scenario']}: {failure['error']}")

        # Assert that all tests pass
        self.assertEqual(len(failures), 0, f"Found {len(failures)} failures in test matrix")


if __name__ == "__main__":
    unittest.main(verbosity=2)