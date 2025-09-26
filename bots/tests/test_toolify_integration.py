"""
Integration tests for @toolify decorator with bot framework.

Tests the complete flow of:
1. Creating toolified functions
2. Adding them to bots
3. Verifying tool registration and execution
4. Basic save/load functionality
"""

import json
import os
import tempfile
import unittest

from bots.dev.decorators import toolify
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


class TestToolifyIntegration(unittest.TestCase):
    """Integration tests for @toolify decorator with the bot framework."""

    def setUp(self):
        """Set up test environment with bot and toolified functions."""
        self.bot = AnthropicBot(
            api_key=None,  # No actual API calls needed
            model_engine=Engines.CLAUDE35_SONNET_20241022,
            max_tokens=1000,
            temperature=0,
            name="ToolifyTestBot",
            autosave=False,
        )

        # Create temp directory for test files
        self.test_dir = tempfile.mkdtemp()

        # Create toolified functions for testing
        self.create_test_tools()

    def create_test_tools(self):
        """Create various toolified functions for testing."""

        # Basic math tool
        @toolify()
        def add_numbers(x: int, y: int = 0) -> int:
            """Add two numbers together."""
            return x + y

        # String processing tool
        @toolify("Convert text to uppercase")
        def make_uppercase(text: str) -> str:
            """Convert text to uppercase."""
            return text.upper()

        # List processing tool
        @toolify()
        def calculate_average(numbers: list) -> float:
            """Calculate the average of a list of numbers."""
            if not numbers:
                raise ValueError("Cannot calculate average of empty list")
            return sum(numbers) / len(numbers)

        # Dictionary processing tool
        @toolify("Format user information")
        def format_user_data(user_info: dict, style: str = "simple") -> str:
            """Format user information in different styles."""
            name = user_info.get("name", "Unknown")
            age = user_info.get("age", "Unknown")

            if style == "simple":
                return f"{name} ({age})"
            elif style == "detailed":
                return f"Name: {name}, Age: {age} years old"
            else:
                return f"User: {name}, {age}"

        # Tool that might fail (tests error handling)
        @toolify()
        def divide_numbers(x: float, y: float) -> float:
            """Divide two numbers."""
            if y == 0:
                raise ValueError("Cannot divide by zero")
            return x / y

        # Store tools for use in tests
        self.test_tools = {
            "add_numbers": add_numbers,
            "make_uppercase": make_uppercase,
            "calculate_average": calculate_average,
            "format_user_data": format_user_data,
            "divide_numbers": divide_numbers,
        }

    def test_add_toolified_functions_to_bot(self):
        """Test that toolified functions can be added to bot."""
        # Add tools to bot
        self.bot.add_tools(self.test_tools["add_numbers"], self.test_tools["make_uppercase"])

        # Verify tools are registered
        tool_names = list(self.bot.tool_handler.function_map.keys())
        self.assertIn("add_numbers", tool_names)
        self.assertIn("make_uppercase", tool_names)

        # Verify tool schemas are generated
        self.assertEqual(len(self.bot.tool_handler.tools), 2)

        # Verify tool schemas have correct structure
        for tool in self.bot.tool_handler.tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("input_schema", tool)

    def test_toolified_function_execution(self):
        """Test that toolified functions execute correctly when called directly."""
        add_func = self.test_tools["add_numbers"]
        uppercase_func = self.test_tools["make_uppercase"]
        avg_func = self.test_tools["calculate_average"]

        # Test string-in, string-out behavior
        result = add_func("5", "3")
        self.assertEqual(result, "8")

        result = uppercase_func("hello world")
        self.assertEqual(result, "HELLO WORLD")

        result = avg_func("[1, 2, 3, 4, 5]")
        self.assertEqual(result, "3.0")

    def test_toolified_error_handling(self):
        """Test that toolified functions handle errors correctly."""
        divide_func = self.test_tools["divide_numbers"]

        # Test division by zero returns error string
        result = divide_func("10", "0")
        self.assertTrue(result.startswith("Error:"))
        self.assertIn("Cannot divide by zero", result)

        # Test invalid input conversion
        result = divide_func("not_a_number", "5")
        self.assertTrue(result.startswith("Error:"))

    def test_multiple_toolified_functions_integration(self):
        """Test bot with multiple toolified functions."""

        # Add multiple tools
        self.bot.add_tools(
            self.test_tools["add_numbers"], self.test_tools["make_uppercase"], self.test_tools["calculate_average"]
        )

        # Verify all tools are registered
        tool_names = list(self.bot.tool_handler.function_map.keys())
        self.assertIn("add_numbers", tool_names)
        self.assertIn("make_uppercase", tool_names)
        self.assertIn("calculate_average", tool_names)

        # Test that each tool works correctly
        add_result = self.bot.tool_handler.function_map["add_numbers"]("10", "5")
        self.assertEqual(add_result, "15")

        upper_result = self.bot.tool_handler.function_map["make_uppercase"]("test")
        self.assertEqual(upper_result, "TEST")

        avg_result = self.bot.tool_handler.function_map["calculate_average"]("[2, 4, 6]")
        self.assertEqual(avg_result, "4.0")

    def test_complex_toolified_function_types(self):
        """Test toolified functions with complex parameter types."""

        # Add tools that use lists and dicts
        self.bot.add_tools(self.test_tools["calculate_average"], self.test_tools["format_user_data"])

        # Test list parameter
        avg_func = self.bot.tool_handler.function_map["calculate_average"]
        result = avg_func("[10, 20, 30, 40, 50]")
        self.assertEqual(result, "30.0")

        # Test dict parameter
        format_func = self.bot.tool_handler.function_map["format_user_data"]
        result = format_func('{"name": "Alice", "age": 25}', "detailed")
        self.assertEqual(result, "Name: Alice, Age: 25 years old")

    def test_toolified_function_docstring_enhancement(self):
        """Test that toolified functions have proper docstrings for LLM."""

        # Add tool with custom description
        self.bot.add_tools(self.test_tools["make_uppercase"])

        # Check that custom description is used
        tool_func = self.bot.tool_handler.function_map["make_uppercase"]
        self.assertEqual(tool_func.__doc__, "Convert text to uppercase")

        # Add tool without custom description
        self.bot.add_tools(self.test_tools["add_numbers"])

        # Check that original docstring is preserved
        add_func = self.bot.tool_handler.function_map["add_numbers"]
        self.assertEqual(add_func.__doc__, "Add two numbers together.")

    def test_toolified_function_tool_handler_integration(self):
        """Test that toolified functions work correctly with ToolHandler methods."""

        # Add a toolified function
        self.bot.add_tools(self.test_tools["add_numbers"])

        # Test that tool handler can generate schemas
        tools = self.bot.tool_handler.tools
        self.assertEqual(len(tools), 1)

        tool_schema = tools[0]
        self.assertEqual(tool_schema["name"], "add_numbers")
        self.assertEqual(tool_schema["description"], "Add two numbers together.")

        # Test that function map contains the tool
        self.assertIn("add_numbers", self.bot.tool_handler.function_map)

        # Test direct function execution through tool handler
        func = self.bot.tool_handler.function_map["add_numbers"]
        result = func("7", "3")
        self.assertEqual(result, "10")

    def test_toolified_functions_with_different_signatures(self):
        """Test toolified functions with various parameter signatures."""

        # Function with no parameters
        @toolify("Get current timestamp")
        def get_timestamp() -> str:
            """Get current timestamp."""
            import datetime

            return datetime.datetime.now().isoformat()

        # Function with only optional parameters
        @toolify()
        def greet(name: str = "World") -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        # Function with mixed parameters
        @toolify()
        def process_data(data: str, uppercase: bool = False, prefix: str = "") -> str:
            """Process data with options."""
            result = data
            if uppercase:
                result = result.upper()
            if prefix:
                result = f"{prefix}{result}"
            return result

        # Add all functions to bot
        self.bot.add_tools(get_timestamp, greet, process_data)

        # Test functions
        timestamp_func = self.bot.tool_handler.function_map["get_timestamp"]
        result = timestamp_func()
        self.assertIsInstance(result, str)
        self.assertIn("T", result)  # ISO format contains 'T'

        greet_func = self.bot.tool_handler.function_map["greet"]
        result = greet_func()
        self.assertEqual(result, "Hello, World!")

        result = greet_func("Alice")
        self.assertEqual(result, "Hello, Alice!")

        process_func = self.bot.tool_handler.function_map["process_data"]
        result = process_func("test", "true", ">>> ")
        self.assertEqual(result, ">>> TEST")

    def tearDown(self):
        """Clean up test files and directories."""
        import shutil

        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")


class TestToolifyRealWorldScenarios(unittest.TestCase):
    """Test toolified functions in realistic scenarios."""

    def setUp(self):
        """Set up realistic toolified functions."""
        self.bot = AnthropicBot(
            api_key=None,
            model_engine=Engines.CLAUDE35_SONNET_20241022,
            max_tokens=1000,
            temperature=0,
            name="RealWorldTestBot",
            autosave=False,
        )

    def test_file_processing_tools(self):
        """Test toolified functions for file processing."""

        @toolify("Count words in text")
        def count_words(text: str) -> int:
            """Count the number of words in text."""
            return len(text.split())

        @toolify("Extract file extension")
        def get_file_extension(filename: str) -> str:
            """Get the file extension from a filename."""
            return os.path.splitext(filename)[1]

        # Add tools to bot
        self.bot.add_tools(count_words, get_file_extension)

        # Test word counting
        word_count = self.bot.tool_handler.function_map["count_words"]
        result = word_count("This is a test sentence with seven words")
        self.assertEqual(result, "8")  # "seven" is actually the 6th word, total is 8

        # Test file extension extraction
        ext_func = self.bot.tool_handler.function_map["get_file_extension"]
        result = ext_func("document.pdf")
        self.assertEqual(result, ".pdf")

    def test_data_analysis_tools(self):
        """Test toolified functions for data analysis."""

        @toolify("Find maximum value in list")
        def find_max(numbers: list) -> float:
            """Find the maximum value in a list of numbers."""
            return max(numbers)

        @toolify("Calculate statistics for dataset")
        def calculate_stats(data: list) -> dict:
            """Calculate basic statistics for a dataset."""
            if not data:
                return {"error": "Empty dataset"}

            return {"count": len(data), "min": min(data), "max": max(data), "mean": sum(data) / len(data), "sum": sum(data)}

        # Add tools to bot
        self.bot.add_tools(find_max, calculate_stats)

        # Test max finding
        max_func = self.bot.tool_handler.function_map["find_max"]
        result = max_func("[1, 5, 3, 9, 2]")
        self.assertEqual(result, "9")

        # Test statistics calculation
        stats_func = self.bot.tool_handler.function_map["calculate_stats"]
        result = stats_func("[10, 20, 30]")
        stats = json.loads(result)

        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["min"], 10)
        self.assertEqual(stats["max"], 30)
        self.assertEqual(stats["mean"], 20.0)
        self.assertEqual(stats["sum"], 60)

    def test_text_processing_tools(self):
        """Test toolified functions for text processing."""

        @toolify("Clean and normalize text")
        def clean_text(text: str, remove_punctuation: bool = False) -> str:
            """Clean and normalize text."""
            import re

            # Remove extra whitespace
            cleaned = re.sub(r"\s+", " ", text.strip())

            if remove_punctuation:
                cleaned = re.sub(r"[^\w\s]", "", cleaned)

            return cleaned

        @toolify("Extract email addresses from text")
        def extract_emails(text: str) -> list:
            """Extract email addresses from text."""
            import re

            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            return re.findall(email_pattern, text)

        # Add tools to bot
        self.bot.add_tools(clean_text, extract_emails)

        # Test text cleaning
        clean_func = self.bot.tool_handler.function_map["clean_text"]
        result = clean_func("  Hello,    world!  ", "true")
        self.assertEqual(result, "Hello world")

        # Test email extraction
        email_func = self.bot.tool_handler.function_map["extract_emails"]
        text = "Contact us at info@example.com or support@test.org"
        result = email_func(text)
        emails = json.loads(result)
        self.assertIn("info@example.com", emails)
        self.assertIn("support@test.org", emails)


if __name__ == "__main__":
    unittest.main()
