import datetime
import math
from collections import defaultdict

import pytest

from bots.foundation.base import ToolHandler


# Create a mock ToolHandler for testing since ToolHandler is abstract
class MockToolHandler(ToolHandler):
    def generate_tool_schema(self, func):
        return {"name": func.__name__, "description": func.__doc__ or "No description", "parameters": {}}

    def generate_request_schema(self, response):
        return []

    def tool_name_and_input(self, request_schema):
        return None, {}

    def generate_response_schema(self, request, tool_output_kwargs):
        return {"result": tool_output_kwargs}

    def generate_error_schema(self, request_schema, error_msg):
        return {"error": error_msg}


# Global variables that should be preserved
VALIDATION_THRESHOLD = 100
ALLOWED_OPERATIONS = ["add", "multiply", "divide"]


def validation_decorator(func):
    """A decorator that validates inputs - has its own globals"""

    def wrapper(*args, **kwargs):
        # This decorator uses its own globals
        if len(args) > VALIDATION_THRESHOLD:
            raise ValueError(f"Too many arguments: {len(args)} > {VALIDATION_THRESHOLD}")
        return func(*args, **kwargs)

    # Preserve original function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__wrapped__ = func  # Store reference to original
    return wrapper


@validation_decorator
def calculate_area(radius: float) -> float:
    """Calculate circle area using math.pi"""
    # This function uses math from its globals
    return math.pi * radius * radius


@validation_decorator
def format_timestamp() -> str:
    """Format current timestamp using datetime"""
    # This function uses datetime from its globals
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@validation_decorator
def count_items(items: list) -> dict:
    """Count items using defaultdict"""
    # This function uses defaultdict from its globals
    counter = defaultdict(int)
    for item in items:
        counter[item] += 1
    return dict(counter)


def complex_decorator_with_state(operation_type):
    """A decorator factory that creates decorators with state"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if operation is allowed using global ALLOWED_OPERATIONS
            if operation_type not in ALLOWED_OPERATIONS:
                raise ValueError(f"Operation {operation_type} not allowed")
            result = func(*args, **kwargs)
            # Use math for some post-processing
            if isinstance(result, (int, float)):
                result = math.ceil(result)
            return result

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__wrapped__ = func
        wrapper.__operation_type__ = operation_type
        return wrapper

    return decorator


@complex_decorator_with_state("multiply")
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


class TestDecoratedFunctionGlobals:
    """Test that decorated functions preserve their original global namespace"""

    def test_decorated_function_preserves_original_globals(self):
        """Test that a decorated function's original globals are preserved"""
        handler = MockToolHandler()
        # Add the decorated function as a tool
        handler.add_tool(calculate_area)
        # The function should work correctly
        func = handler.function_map["calculate_area"]
        result = func(5.0)
        expected = math.pi * 25.0
        assert abs(result - expected) < 0.001
        # Check that the function has access to math
        # This should work if globals are preserved correctly
        assert "math" in func.__globals__

    def test_decorated_function_with_datetime_globals(self):
        """Test decorated function that uses datetime module"""
        handler = MockToolHandler()
        handler.add_tool(format_timestamp)
        func = handler.function_map["format_timestamp"]
        result = func()
        # Should return a formatted timestamp string
        assert isinstance(result, str)
        assert len(result) > 10  # Basic sanity check
        # Check that datetime is available in globals
        assert "datetime" in func.__globals__

    def test_decorated_function_with_collections_globals(self):
        """Test decorated function that uses collections module"""
        handler = MockToolHandler()
        handler.add_tool(count_items)
        func = handler.function_map["count_items"]
        result = func(["a", "b", "a", "c", "b", "a"])
        expected = {"a": 3, "b": 2, "c": 1}
        assert result == expected
        # Check that defaultdict is available in globals
        assert "defaultdict" in func.__globals__

    def test_complex_decorator_with_state_preserves_globals(self):
        """Test complex decorator with state preserves all necessary globals"""
        handler = MockToolHandler()
        handler.add_tool(multiply_numbers)
        func = handler.function_map["multiply_numbers"]
        result = func(3.7, 2.1)
        # Should be ceil(3.7 * 2.1) = ceil(7.77) = 8
        assert result == 8
        # Check that both decorator and original function globals are preserved
        assert "math" in func.__globals__
        assert "ALLOWED_OPERATIONS" in func.__globals__

    def test_decorator_validation_works_after_serialization(self):
        """Test that decorator validation still works after serialize/deserialize"""
        handler = MockToolHandler()
        handler.add_tool(calculate_area)
        # Serialize and deserialize
        data = handler.to_dict()
        new_handler = MockToolHandler.from_dict(data)
        # Function should still work
        func = new_handler.function_map["calculate_area"]
        result = func(5.0)
        expected = math.pi * 25.0
        assert abs(result - expected) < 0.001
        # Validation should still work (this will fail if globals aren't preserved)
        with pytest.raises(ValueError, match="Too many arguments"):
            # Create a list with more than VALIDATION_THRESHOLD items
            args = [1.0] * (VALIDATION_THRESHOLD + 1)
            func(*args)

    def test_multiple_decorated_functions_preserve_distinct_globals(self):
        """Test that multiple decorated functions preserve their distinct globals"""
        handler = MockToolHandler()
        # Add multiple decorated functions
        handler.add_tool(calculate_area)
        handler.add_tool(format_timestamp)
        handler.add_tool(count_items)
        # Each should have access to their required globals
        area_func = handler.function_map["calculate_area"]
        timestamp_func = handler.function_map["format_timestamp"]
        count_func = handler.function_map["count_items"]
        assert "math" in area_func.__globals__
        assert "datetime" in timestamp_func.__globals__
        assert "defaultdict" in count_func.__globals__
        # Test they all work
        assert area_func(2.0) > 12.0  # pi * 4 > 12
        assert len(timestamp_func()) > 10
        assert count_func(["x", "y", "x"]) == {"x": 2, "y": 1}

    def test_nested_decorator_globals_preservation(self):
        """Test that nested/complex decorators preserve all levels of globals"""
        handler = MockToolHandler()
        handler.add_tool(multiply_numbers)
        # Serialize and deserialize to test persistence
        data = handler.to_dict()
        new_handler = MockToolHandler.from_dict(data)
        func = new_handler.function_map["multiply_numbers"]
        # Should work with both decorator and original function globals
        result = func(2.5, 3.0)
        assert result == 8  # ceil(7.5) = 8
        # Check all necessary globals are present
        assert "math" in func.__globals__
        assert "ALLOWED_OPERATIONS" in func.__globals__
        assert "VALIDATION_THRESHOLD" in func.__globals__

    def test_decorator_with_closure_variables(self):
        """Test decorator that captures closure variables"""
        # Create a decorator with closure variables
        multiplier = 10

        def scaling_decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                # Use the closure variable
                return result * multiplier

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            wrapper.__wrapped__ = func
            return wrapper

        @scaling_decorator
        def simple_add(a: float, b: float) -> float:
            """Add two numbers"""
            return a + b

        handler = MockToolHandler()
        handler.add_tool(simple_add)
        # Test the function works
        func = handler.function_map["simple_add"]
        result = func(2.0, 3.0)
        assert result == 50.0  # (2 + 3) * 10
        # Test after serialization (this might fail if closure isn't preserved)
        data = handler.to_dict()
        new_handler = MockToolHandler.from_dict(data)
        new_func = new_handler.function_map["simple_add"]
        new_result = new_func(2.0, 3.0)
        assert new_result == 50.0

    def test_deeply_nested_closure_decorator(self):
        """Test decorator with multiple levels of closure variables"""
        base_multiplier = 5
        offset = 100

        def create_complex_decorator(factor):
            def complex_decorator(func):
                def wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    # Use multiple closure variables
                    return (result * base_multiplier * factor) + offset

                wrapper.__name__ = func.__name__
                wrapper.__doc__ = func.__doc__
                wrapper.__wrapped__ = func
                return wrapper

            return complex_decorator

        @create_complex_decorator(2)
        def simple_multiply(a: float, b: float) -> float:
            """Multiply two numbers"""
            return a * b

        handler = MockToolHandler()
        handler.add_tool(simple_multiply)
        # Test the function works: (2 * 3) * 5 * 2 + 100 = 6 * 10 + 100 = 160
        func = handler.function_map["simple_multiply"]
        result = func(2.0, 3.0)
        assert result == 160.0
        # Test after serialization
        data = handler.to_dict()
        new_handler = MockToolHandler.from_dict(data)
        new_func = new_handler.function_map["simple_multiply"]
        new_result = new_func(2.0, 3.0)
        assert new_result == 160.0

    def test_decorator_with_imported_modules_in_closure(self):
        """Test decorator that uses imported modules within closure"""
        seed_value = 42

        def random_decorator(func):
            def wrapper(*args, **kwargs):
                import random

                # Use imported module and closure variable
                random.seed(seed_value)
                result = func(*args, **kwargs)
                return result + random.randint(1, 10)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            wrapper.__wrapped__ = func
            return wrapper

        @random_decorator
        def base_calculation(x: float) -> float:
            """Basic calculation"""
            return x * 2

        handler = MockToolHandler()
        handler.add_tool(base_calculation)
        # Test the function works (should be deterministic due to seed)
        func = handler.function_map["base_calculation"]
        result1 = func(5.0)
        result2 = func(5.0)
        # Both results should be the same due to seeding
        assert result1 == result2
        assert result1 > 10.0  # 5*2 + random(1-10) > 10
        # Test after serialization
        data = handler.to_dict()
        new_handler = MockToolHandler.from_dict(data)
        new_func = new_handler.function_map["base_calculation"]
        new_result = new_func(5.0)
        # Should still be deterministic
        assert new_result == result1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
