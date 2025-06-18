"""Tests for lazy implementation decorators (@lazy, @lazy_fn, @lazy_class).

This module contains end-to-end tests for the lazy decorators that use LLMs to
implement functions and classes at runtime.

The tests:
1. Create temporary Python files with placeholder implementations
2. Import and use the decorated objects, triggering LLM implementation
3. Verify the implementations work correctly by testing their outputs
4. Clean up temporary files after testing
"""

import importlib.util
import os
import shutil
import sys
from typing import Any

import pytest

# Constants for test file paths
TEST_DIR_NAME = "lazy_decorator_test_dir"
SORT_FILENAME = "lazy_sort_test.py"
CACHE_FILENAME = "lazy_cache_test.py"
CALCULATOR_FILENAME = "lazy_calculator_test.py"


def is_sorted(items):
    """Check if a list is sorted in ascending order."""
    if not items:
        return True
    return all(items[i] <= items[i + 1] for i in range(len(items) - 1))


def setup_module():
    """Set up test environment by creating test directory and files."""
    # Create test directory if it doesn't exist
    if not os.path.exists(TEST_DIR_NAME):
        os.makedirs(TEST_DIR_NAME)

    # Create __init__.py to make directory a package
    with open(os.path.join(TEST_DIR_NAME, "__init__.py"), "w") as f:
        f.write("# Test package for lazy decorators")

    # Create sort test file
    with open(os.path.join(TEST_DIR_NAME, SORT_FILENAME), "w") as f:
        f.write(
            """
# Import decorators - adjust import path as needed
from bots.dev.decorators import lazy, lazy_fn

def is_sorted(items):
    \"\"\"Check if a list is sorted.\"\"\"
    if not items:
        return True
    return all(items[i] <= items[i+1] for i in range(len(items)-1))

@lazy_fn("Implement a mergesort algorithm that sorts a list in ascending order. \\
    The algorithm should be stable, meaning that equal elements maintain their \\
    relative order. Use a divide-and-conquer approach splitting the list in half \\
    recursively and merging the sorted sublists.")
def mergesort(items: list) -> list:
    pass  # Will be implemented by LLM

@lazy("Implement a quicksort algorithm that sorts a list in ascending order. \\
    The implementation should use a divide-and-conquer approach selecting a pivot \\
    and partitioning the list into elements less than the pivot and elements greater \\
    than the pivot. Use a random pivot selection for better average performance.")
def quicksort(items: list) -> list:
    pass  # Will be implemented by LLM
        """
        )

    # Create cache test file
    with open(os.path.join(TEST_DIR_NAME, CACHE_FILENAME), "w") as f:
        f.write(
            """
# Import decorator
from bots.dev.decorators import lazy_class

@lazy_class("Implement an LRU (Least Recently Used) cache with the following methods: \\
    - __init__(self, capacity: int): Initialize the cache with a maximum capacity \\
    - get(self, key: Any) -> Any: Get the value associated with the key if it exists, \\
      otherwise return None. Getting a value should move it to the most recently used position. \\
    - put(self, key: Any, value: Any) -> None: Add or update a key-value pair. If the \\
      cache exceeds capacity, remove the least recently used item. \\
    - size(self) -> int: Return the current number of items in the cache. \\
    The implementation should use an OrderedDict or a combination of a dictionary and \\
    a doubly linked list for O(1) operations.")
class LRUCache:
    pass  # Will be implemented by LLM
        """
        )

    # Create calculator test file
    with open(os.path.join(TEST_DIR_NAME, CALCULATOR_FILENAME), "w") as f:
        f.write(
            """
# Import decorator
from bots.dev.decorators import lazy

@lazy("Implement a scientific calculator class with the following features: \\
    - Basic arithmetic: add, subtract, multiply, divide \\
    - Advanced operations: power, square root, logarithm, factorial \\
    - Trigonometric functions: sin, cos, tan (in radians) \\
    - Memory functions: store, recall, clear memory \\
    - Keep track of calculation history \\
    Include proper error handling for operations like division by zero.")
class ScientificCalculator:
    pass  # Will be implemented by LLM
        """
        )


def teardown_module():
    """Clean up test directory and files after tests."""
    if os.path.exists(TEST_DIR_NAME):
        shutil.rmtree(TEST_DIR_NAME)


def import_module(module_path: str, module_name: str) -> Any:
    """Dynamically import a module from file path.

    Args:
        module_path: Path to the Python module file
        module_name: Name to assign to the imported module

    Returns:
        Imported module object
    """
    # Add the parent directory to sys.path to enable imports
    parent_dir = os.path.dirname(os.path.dirname(module_path))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Use the directory containing the module for relative imports
    module_dir = os.path.dirname(module_path)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestLazyFunctionDecorator:
    """Tests for the @lazy_fn decorator."""

    def test_mergesort_implementation(self):
        """Test that mergesort is implemented correctly."""
        # Import the module with the lazy_fn decorated function
        sort_module = import_module(os.path.join(TEST_DIR_NAME, SORT_FILENAME), "lazy_sort_test")

        # Test cases
        test_cases = [
            [5, 2, 9, 1, 5, 6],  # Random integers
            [3.14, 1.59, 2.65, 3.58],  # Float values
            ["z", "a", "b", "y", "c"],  # Strings
            [5, 5, 3, 3, 7, 7],  # Duplicates
            [],  # Empty list
            [1],  # Single element
        ]

        for test_case in test_cases:
            # Make a copy of the original for comparison
            original = test_case.copy()
            # Apply mergesort - first call will trigger implementation
            sorted_result = sort_module.mergesort(test_case)

            # Verify results
            assert sort_module.is_sorted(sorted_result), f"Failed to sort: {original}"
            assert len(sorted_result) == len(original), f"Length changed for: {original}"
            assert sorted(original) == sorted_result, f"Elements changed for: {original}"

        # Test stability with custom objects
        class Item:
            def __init__(self, value, order):
                self.value = value
                self.order = order

            def __eq__(self, other):
                if isinstance(other, Item):
                    return self.value == other.value and self.order == other.order
                return False

            def __le__(self, other):
                if isinstance(other, Item):
                    return self.value <= other.value
                return NotImplemented

        # Create items with same values but different order
        items = [Item(5, 1), Item(3, 2), Item(5, 3), Item(2, 4), Item(3, 5), Item(5, 6)]
        sorted_items = sort_module.mergesort(items)

        # Check if items with same value maintain relative order
        value_order_map = {}
        for item in sorted_items:
            if item.value not in value_order_map:
                value_order_map[item.value] = []
            value_order_map[item.value].append(item.order)

        # Verify each value's order list is in ascending order
        for value, orders in value_order_map.items():
            assert orders == sorted(orders), f"Mergesort is not stable for value {value}"


class TestLazyDecorator:
    """Tests for the @lazy decorator."""

    def test_quicksort_implementation(self):
        """Test that quicksort is implemented correctly."""
        # Import the module with the lazy decorated function
        sort_module = import_module(os.path.join(TEST_DIR_NAME, SORT_FILENAME), "lazy_sort_test")

        # Test cases for quicksort
        test_cases = [
            [9, 8, 7, 6, 5, 4, 3, 2, 1],  # Reversed list
            [1, 2, 3, 4, 5, 6, 7, 8, 9],  # Already sorted
            [5, 2, 9, 1, 5, 6],  # Random integers
            [3.14, 1.59, 2.65, 3.58],  # Float values
            ["z", "a", "b", "y", "c"],  # Strings
            [5, 5, 3, 3, 7, 7],  # Duplicates
            [],  # Empty list
            [1],  # Single element
        ]

        for test_case in test_cases:
            # Make a copy of the original for comparison
            original = test_case.copy()
            # Apply quicksort - first call will trigger implementation
            sorted_result = sort_module.quicksort(test_case)

            # Verify results
            assert sort_module.is_sorted(sorted_result), f"Failed to sort: {original}"
            assert len(sorted_result) == len(original), f"Length changed for: {original}"
            assert sorted(original) == sorted_result, f"Elements changed for: {original}"

    def test_calculator_implementation(self):
        """Test that ScientificCalculator is implemented correctly."""
        # Import the module with the lazy decorated class
        calc_module = import_module(os.path.join(TEST_DIR_NAME, CALCULATOR_FILENAME), "lazy_calculator_test")

        # Create calculator instance - will trigger implementation
        calculator = calc_module.ScientificCalculator()

        # Test basic arithmetic operations
        assert hasattr(calculator, "add"), "Calculator missing add method"
        assert hasattr(calculator, "subtract"), "Calculator missing subtract method"
        assert hasattr(calculator, "multiply"), "Calculator missing multiply method"
        assert hasattr(calculator, "divide"), "Calculator missing divide method"

        # Test basic functionality
        assert abs(calculator.add(5, 3) - 8) < 1e-10, "Addition failed"
        assert abs(calculator.subtract(5, 3) - 2) < 1e-10, "Subtraction failed"
        assert abs(calculator.multiply(5, 3) - 15) < 1e-10, "Multiplication failed"
        assert abs(calculator.divide(6, 3) - 2) < 1e-10, "Division failed"

        # Test advanced operations if they exist
        if hasattr(calculator, "power"):
            assert abs(calculator.power(2, 3) - 8) < 1e-10, "Power operation failed"

        if hasattr(calculator, "square_root"):
            assert abs(calculator.square_root(9) - 3) < 1e-10, "Square root failed"

        # Test error handling for division by zero
        try:
            calculator.divide(5, 0)
            assert False, "Division by zero should raise an exception"
        except (ValueError, ZeroDivisionError):
            # Either exception type is acceptable
            pass
        except Exception as e:
            # Other exceptions are not expected
            assert False, f"Unexpected exception: {str(e)}"


class TestLazyClassDecorator:
    """Tests for the @lazy_class decorator."""

    def test_lru_cache_implementation(self):
        """Test that LRUCache is implemented correctly."""
        # Import the module with the lazy_class decorated class
        cache_module = import_module(os.path.join(TEST_DIR_NAME, CACHE_FILENAME), "lazy_cache_test")

        # Create cache with capacity 3 - will trigger implementation
        cache = cache_module.LRUCache(3)

        # Test basic functionality
        assert hasattr(cache, "get"), "Cache missing get method"
        assert hasattr(cache, "put"), "Cache missing put method"

        # Test putting and getting values
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)

        assert cache.get("a") == 1, "Failed to get value for key 'a'"
        assert cache.get("b") == 2, "Failed to get value for key 'b'"
        assert cache.get("c") == 3, "Failed to get value for key 'c'"
        assert cache.get("d") is None, "Should return None for non-existent key"

        # Test LRU eviction
        # Access 'a' to make it most recently used,
        # 'b' becomes least recently used
        cache.get("a")
        # Add a new item, should evict 'b'
        cache.put("d", 4)

        assert cache.get("b") is None, "LRU eviction failed, 'b' should be evicted"
        assert cache.get("a") == 1, "Key 'a' should be retained"
        assert cache.get("c") == 3, "Key 'c' should be retained"
        assert cache.get("d") == 4, "Key 'd' should be retained"

        # Test updating existing key
        cache.put("a", 10)
        assert cache.get("a") == 10, "Failed to update value for key 'a'"

        # Test size if implemented
        if hasattr(cache, "size"):
            assert cache.size() == 3, "Cache size should be 3"

        # Test a larger workload
        cache = cache_module.LRUCache(5)
        for i in range(10):
            cache.put(f"key{i}", i)

        # Only last 5 items should be in cache
        for i in range(5):
            assert cache.get(f"key{i}") is None, f"Key 'key{i}' should be evicted"

        for i in range(5, 10):
            assert cache.get(f"key{i}") == i, f"Key 'key{i}' should be in cache"


if __name__ == "__main__":
    print("Setting up test environment...")
    setup_module()

    try:
        print("Running tests...")
        exit_code = pytest.main(["-xvs", __file__])

        if exit_code == 0:
            print("All tests passed successfully!")
        else:
            print(f"Tests failed with exit code: {exit_code}")
    finally:
        print("Cleaning up test environment...")
        teardown_module()
