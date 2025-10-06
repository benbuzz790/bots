"""Pytest configuration for e2e tests."""

import pytest

# E2E-specific fixtures can be defined here


def pytest_collection_modifyitems(items):
    """Mark only tests in test_cli directory to run serially in same group."""
    for item in items:
        # Only mark CLI tests for serial execution
        test_path = str(item.fspath)
        if "test_cli" in test_path:
            item.add_marker(pytest.mark.xdist_group("cli_serial"))
