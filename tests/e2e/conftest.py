"""Pytest configuration for e2e tests."""

import pytest

# E2E-specific fixtures can be defined here

# Fixtures from test_cli/conftest.py
import pytest


def pytest_collection_modifyitems(items):
    """Mark all tests in test_cli directory to run serially in same group."""
    for item in items:
        item.add_marker(pytest.mark.xdist_group("cli_serial"))
