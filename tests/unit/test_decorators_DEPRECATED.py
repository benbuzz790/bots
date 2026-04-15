"""DEPRECATED: Tests for lazy implementation decorators.
WARNING: These tests are deprecated. The lazy decorators have been moved
to a separate package: lazy-impl
To use lazy decorators, install the lazy-impl package:
    pip install lazy-impl
Then import from lazy_impl instead of bots.dev.decorators:
    from lazy_impl import lazy, lazy_fn, lazy_class
This file is kept for reference only and will be removed in a future version.
"""

# DEPRECATED - DO NOT RUN
# The tests below reference decorators that have been moved to lazy-impl package

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


# Rest of the file is deprecated and should not be executed
pytest.skip("Deprecated: lazy decorators moved to lazy-impl package", allow_module_level=True)
