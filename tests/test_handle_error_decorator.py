from unittest.mock import patch

import pytest

from bots.dev.decorators import handle_errors

"""Tests for the handle_errors decorator.

This module tests the handle_errors decorator functionality including:
- Exception catching and error string formatting
- Preservation of function metadata
- Proper return values for successful operations
- Integration with _process_error helper function
"""


class TestHandleErrorsDecorator:
    """Test suite for the handle_errors decorator."""

    def test_successful_function_execution(self):
        """Test that successful function calls return normal results."""

        @handle_errors
        def successful_function(x, y):
            return x + y

        result = successful_function(2, 3)
        assert result == 5

    def test_exception_handling_returns_error_string(self):
        """Test that exceptions are caught and returned as formatted error
        strings."""

        @handle_errors
        def failing_function():
            raise ValueError("Test error message")

        result = failing_function()
        assert isinstance(result, str)
        assert result.startswith("Tool Failed:")
        assert "ValueError" in result
        assert "Test error message" in result

    def test_different_exception_types(self):
        """Test that different exception types are properly handled."""

        @handle_errors
        def type_error_function():
            raise TypeError("Type error message")

        @handle_errors
        def runtime_error_function():
            raise RuntimeError("Runtime error message")

        type_result = type_error_function()
        runtime_result = runtime_error_function()
        assert "TypeError" in type_result
        assert "Type error message" in type_result
        assert "RuntimeError" in runtime_result
        assert "Runtime error message" in runtime_result

    def test_function_with_arguments(self):
        """Test that decorated functions properly handle arguments."""

        @handle_errors
        def function_with_args(a, b, c=None, **kwargs):
            if c is None:
                raise ValueError("c cannot be None")
            return a + b + c

        # Test successful call
        result = function_with_args(1, 2, c=3)
        assert result == 6
        # Test exception with arguments
        error_result = function_with_args(1, 2)
        assert "Tool Failed:" in error_result
        assert "ValueError" in error_result

    def test_function_metadata_preservation(self):
        """Test that function metadata is preserved by the decorator."""

        @handle_errors
        def documented_function(x):
            """This is a test function with documentation."""
            return x * 2

        assert documented_function.__name__ == "documented_function"
        doc = documented_function.__doc__
        assert "test function with documentation" in doc

    def test_nested_exceptions(self):
        """Test handling of nested function calls that raise exceptions."""

        def inner_function():
            raise ZeroDivisionError("Division by zero in inner function")

        @handle_errors
        def outer_function():
            return inner_function()

        result = outer_function()
        assert "Tool Failed:" in result
        assert "ZeroDivisionError" in result
        assert "Division by zero in inner function" in result

    def test_traceback_included_in_error(self):
        """Test that traceback information is included in error strings."""

        @handle_errors
        def function_with_traceback():
            x = 1
            y = 0
            return x / y  # This will raise ZeroDivisionError

        result = function_with_traceback()
        assert "Tool Failed:" in result
        assert "Traceback:" in result
        assert "ZeroDivisionError" in result

    @patch("bots.utils.helpers._process_error")
    def test_process_error_integration(self, mock_process_error):
        """Test that the decorator properly calls _process_error."""
        mock_process_error.return_value = "Mocked error message"

        @handle_errors
        def failing_function():
            raise ValueError("Test error")

        result = failing_function()
        # Verify _process_error was called
        mock_process_error.assert_called_once()
        # Verify the exception passed to _process_error is correct
        called_exception = mock_process_error.call_args[0][0]
        assert isinstance(called_exception, ValueError)
        assert str(called_exception) == "Test error"
        # Verify the result is what _process_error returned
        assert result == "Mocked error message"

    def test_multiple_decorated_functions(self):
        """Test that multiple functions can be decorated independently."""

        @handle_errors
        def function_one():
            raise ValueError("Error from function one")

        @handle_errors
        def function_two():
            raise TypeError("Error from function two")

        result_one = function_one()
        result_two = function_two()
        assert "ValueError" in result_one
        assert "Error from function one" in result_one
        assert "TypeError" in result_two
        assert "Error from function two" in result_two

    def test_return_none_handling(self):
        """Test that functions returning None work correctly."""

        @handle_errors
        def function_returning_none():
            return None

        result = function_returning_none()
        assert result is None

    def test_complex_return_types(self):
        """Test that complex return types are preserved."""

        @handle_errors
        def function_returning_dict():
            return {"key": "value", "number": 42}

        @handle_errors
        def function_returning_list():
            return [1, 2, 3, "test"]

        dict_result = function_returning_dict()
        list_result = function_returning_list()
        assert dict_result == {"key": "value", "number": 42}
        assert list_result == [1, 2, 3, "test"]

    def test_class_method_decoration(self):
        """Test that the decorator works with class methods."""

        class TestClass:

            @handle_errors
            def method_that_fails(self):
                raise AttributeError("Method error")

            @handle_errors
            def method_that_succeeds(self, value):
                return value * 2

        obj = TestClass()
        # Test successful method
        result = obj.method_that_succeeds(5)
        assert result == 10
        # Test failing method
        error_result = obj.method_that_fails()
        assert "Tool Failed:" in error_result
        assert "AttributeError" in error_result
        assert "Method error" in error_result


if __name__ == "__main__":
    pytest.main([__file__])
