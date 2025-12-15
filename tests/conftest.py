import os
import tempfile
import uuid

import pytest

# Import shared fixtures from fixtures directory
# These will be automatically discovered by pytest
try:
    from tests.fixtures.bot_fixtures import *  # noqa: F401, F403
    from tests.fixtures.env_fixtures import *  # noqa: F401, F403
    from tests.fixtures.file_fixtures import *  # noqa: F401, F403
    from tests.fixtures.mock_fixtures import *  # noqa: F401, F403
    from tests.fixtures.tool_fixtures import *  # noqa: F401, F403
except ImportError:
    # Fixtures not yet created, will be added in Phase 2
    pass


def get_unique_filename(prefix="test", extension="py"):
    """Generate a unique filename for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}.{extension}"


def create_safe_test_file(content, prefix="test", extension="py", directory=None):
    """Create a safe test file with given content in specified or temp directory."""
    if directory is None:
        # Create in temp directory
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{extension}", prefix=f"{prefix}_", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            return f.name
    else:
        # Create in specified directory
        if directory == "tmp":
            # Use system temp directory
            directory = tempfile.gettempdir()

        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Generate unique filename
        filename = get_unique_filename(prefix, extension)
        filepath = os.path.join(directory, filename)

        # Write content to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath


def pytest_collection_modifyitems(config, items):
    """
    Modify test items to enforce serial execution for tests marked with @cli_serial.

    This hook adds the pytest-xdist 'xdist_group' marker to tests marked with @cli_serial,
    ensuring they run serially in the same worker process.
    """
    for item in items:
        # Check if test has cli_serial marker
        if item.get_closest_marker("cli_serial"):
            # Add xdist_group marker to force serial execution
            # All tests with the same xdist_group name run in the same worker, serially
            item.add_marker(pytest.mark.xdist_group("cli_serial"))
