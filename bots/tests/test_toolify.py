"""
Test suite for the @toolify decorator.

Tests the simplified @toolify decorator that converts functions to
string-in, string-out bot tools with automatic type conversion.
"""

import json
import pytest
from typing import List, Dict

from bots.dev.decorators import toolify


class TestToolifyBasics:
    """Test basic @toolify functionality."""

    def test_simple_function(self):
        """Test toolifying a simple function."""

        @toolify()
        def add_numbers(x: int, y: int = 0) -> int:
            """Add two numbers."""
            return x + y

        # Test with string inputs
        result = add_numbers("5", "3")
        assert result == "8"

        # Test with default parameter
        result = add_numbers("10")
        assert result == "10"

    def test_custom_description(self):
        """Test toolify with custom description."""

        @toolify("Calculate circle area")
        def area(radius: float) -> float:
            return 3.14159 * radius * radius

        assert area.__doc__ == "Calculate circle area"

        result = area("5.0")
        expected = str(3.14159 * 25)
        assert result == expected

    def test_no_type_hints(self):
        """Test function without type hints."""

        @toolify()
        def no_hints(x, y="default"):
            """Function without type hints."""
            return f"{x}_{y}"

        # Should work with strings (no conversion)
        result = no_hints("hello", "world")
        assert result == "hello_world"


class TestTypeConversion:
    """Test type conversion functionality."""

    def test_basic_types(self):
        """Test conversion of basic types."""

        @toolify()
        def test_types(
            text: str,
            number: int, 
            decimal: float,
            flag: bool
        ) -> str:
            return f"{text}|{number}|{decimal}|{flag}"

        result = test_types("hello", "42", "3.14", "true")
        assert result == "hello|42|3.14|True"

    def test_boolean_conversion(self):
        """Test various boolean string representations."""

        @toolify()
        def test_bool(flag: bool) -> str:
            return str(flag)

        # Test true values
        assert test_bool("true") == "True"
        assert test_bool("True") == "True"
        assert test_bool("1") == "True"
        assert test_bool("yes") == "True"
        assert test_bool("on") == "True"

        # Test false values
        assert test_bool("false") == "False"
        assert test_bool("False") == "False"
        assert test_bool("0") == "False"
        assert test_bool("no") == "False"
        assert test_bool("off") == "False"

    def test_list_conversion(self):
        """Test list parameter conversion."""

        @toolify()
        def process_list(items: list) -> str:
            return f"Processed {len(items)} items: {items}"

        # Test with string representation of list
        result = process_list("['a', 'b', 'c']")
        assert "Processed 3 items" in result
        assert "['a', 'b', 'c']" in result

        # Test with numbers
        result = process_list("[1, 2, 3, 4, 5]")
        assert "Processed 5 items" in result

    def test_dict_conversion(self):
        """Test dict parameter conversion."""

        @toolify()
        def process_dict(data: dict) -> str:
            return f"Keys: {list(data.keys())}"

        result = process_dict("{'name': 'test', 'value': 42}")
        assert "Keys: ['name', 'value']" in result


class TestOutputConversion:
    """Test output conversion to strings."""

    def test_none_return(self):
        """Test function that returns None."""

        @toolify()
        def returns_none() -> None:
            pass

        result = returns_none()
        assert result == "Tool execution completed without errors"

    def test_basic_return_types(self):
        """Test various return types."""

        @toolify()
        def return_int() -> int:
            return 42

        @toolify()
        def return_float() -> float:
            return 3.14

        @toolify()
        def return_bool() -> bool:
            return True

        assert return_int() == "42"
        assert return_float() == "3.14"
        assert return_bool() == "True"

    def test_complex_return_types(self):
        """Test list and dict returns (should be JSON)."""

        @toolify()
        def return_list() -> List[str]:
            return ["a", "b", "c"]

        @toolify()
        def return_dict() -> Dict[str, int]:
            return {"x": 1, "y": 2}

        list_result = return_list()
        assert json.loads(list_result) == ["a", "b", "c"]

        dict_result = return_dict()
        assert json.loads(dict_result) == {"x": 1, "y": 2}


class TestErrorHandling:
    """Test error handling behavior."""

    def test_conversion_error(self):
        """Test error when type conversion fails."""

        @toolify()
        def need_int(x: int) -> int:
            return x * 2

        # Should return error string, not raise
        result = need_int("not_a_number")
        assert result.startswith("Tool Failed:")
        assert "invalid literal" in result.lower()

    def test_function_error(self):
        """Test error when function itself fails."""

        @toolify()
        def will_fail(x: int) -> int:
            if x == 0:
                raise ValueError("Cannot be zero")
            return 10 / x

        # Should return error string, not raise
        result = will_fail("0")
        assert result.startswith("Tool Failed:")
        assert "Cannot be zero" in result

    def test_no_errors_raised(self):
        """Ensure toolified functions never raise exceptions."""

        @toolify()
        def problematic(x: int, y: int) -> int:
            return x / y  # Could cause ZeroDivisionError

        # Should not raise, should return error string
        result = problematic("10", "0")
        assert isinstance(result, str)
        assert result.startswith("Tool Failed:")


class TestDocstringHandling:
    """Test docstring behavior."""

    def test_preserve_existing_docstring(self):
        """Test that existing docstrings are preserved."""

        @toolify()
        def has_docstring(x: int) -> int:
            """This function has a docstring."""
            return x

        assert has_docstring.__doc__ == "This function has a docstring."

    def test_generate_docstring_for_undocumented(self):
        """Test docstring generation for undocumented functions."""

        @toolify()
        def no_docstring(x: int) -> int:
            return x

        assert no_docstring.__doc__ == "Execute no docstring"

    def test_override_with_description(self):
        """Test overriding docstring with description parameter."""

        @toolify("Custom description")
        def original_docstring(x: int) -> int:
            """Original docstring."""
            return x

        assert original_docstring.__doc__ == "Custom description"


class TestRealWorldExamples:
    """Test with realistic tool examples."""

    def test_file_operation_tool(self):
        """Test a file operation style tool."""

        @toolify("Count lines in text")
        def count_lines(text: str) -> int:
            return len(text.split('\n'))

        result = count_lines("line1\nline2\nline3")
        assert result == "3"

    def test_calculation_tool(self):
        """Test a calculation tool."""

        @toolify()
        def calculate_average(numbers: list) -> float:
            """Calculate the average of a list of numbers."""
            return sum(numbers) / len(numbers)

        result = calculate_average("[1, 2, 3, 4, 5]")
        assert result == "3.0"

    def test_data_processing_tool(self):
        """Test a data processing tool."""

        @toolify("Process user data")
        def process_user_data(
            name: str, 
            age: int, 
            active: bool = True
        ) -> dict:
            return {
                "name": name.upper(),
                "age": age,
                "status": "active" if active else "inactive"
            }

        result = process_user_data("john", "25", "true")
        data = json.loads(result)

        assert data["name"] == "JOHN"
        assert data["age"] == 25
        assert data["status"] == "active"


if __name__ == "__main__":
    # Run basic tests if executed directly
    print("Running basic @toolify tests...")

    @toolify("Test function")
    def test_func(x: int, y: int = 2) -> int:
        return x * y

    result = test_func("5", "3")
    print(f"test_func('5', '3') = {result}")
    assert result == "15"

    # Test error handling
    @toolify()
    def error_func(x: int) -> int:
        if x == 0:
            raise ValueError("Zero not allowed")
        return 10 / x

    result = error_func("0")
    print(f"error_func('0') = {result}")
    assert result.startswith("Error:")

    print("Basic tests passed! Run with pytest for full test suite.")