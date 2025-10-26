"""Pytest configuration for e2e tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_isolated_filesystem(request, isolated_filesystem):
    """Automatically use isolated_filesystem for all E2E tests.

    This ensures that E2E tests (which often use bots with file creation tools)
    run in an isolated temporary directory, preventing test artifacts from
    polluting the repository.

    The fixture can be disabled for specific tests if needed using:
        @pytest.mark.no_isolation
    """
    # Check if test is marked to skip isolation
    if request.node.get_closest_marker("no_isolation"):
        yield
    else:
        # Use the isolated filesystem
        yield isolated_filesystem


# E2E-specific fixtures can be defined here


def pytest_collection_modifyitems(items):
    """Mark only tests in test_cli directory to run serially in same group."""
    for item in items:
        # Only mark CLI tests for serial execution
        test_path = str(item.fspath)
        if "test_cli" in test_path:
            item.add_marker(pytest.mark.xdist_group("cli_serial"))
