import pytest


def pytest_collection_modifyitems(items):
    """Mark all tests in test_powershell_tool directory to run serially in same group."""
    for item in items:
        item.add_marker(pytest.mark.xdist_group("terminal_serial"))
