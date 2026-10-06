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


def pytest_configure(config):
    """Register custom pytest markers for test categorization.

    Markers:
        slow: Tests that take significant time to run (>5 seconds)
        integration: Integration tests that test multiple components together
        api: Tests that make real API calls to external services (OpenAI, Anthropic, etc.)
        flaky: Tests known to be flaky/intermittent

    Usage:
        @pytest.mark.slow
        @pytest.mark.api
        def test_anthropic_integration():
            pass
    """
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests that call real APIs")
    config.addinivalue_line("markers", "flaky: marks tests as flaky/intermittent")


def pytest_collection_modifyitems(config, items):
    """
    Modify test items to enforce serial execution for tests marked with @serial or @cli_serial.

    This hook adds the pytest-xdist 'xdist_group' marker to tests marked with @serial or @cli_serial,
    ensuring they run serially in the same worker process.
    """
    for item in items:
        # Check if test has cli_serial marker
        if item.get_closest_marker("cli_serial"):
            # Add xdist_group marker to force serial execution
            # All tests with the same xdist_group name run in the same worker, serially
            item.add_marker(pytest.mark.xdist_group("cli_serial"))

        # Check if test has serial marker
        elif item.get_closest_marker("serial"):
            # Add xdist_group marker to force serial execution
            # All tests with the same xdist_group name run in the same worker, serially
            item.add_marker(pytest.mark.xdist_group("serial"))


# Fixed snapshot of the Anthropic model list used to resolve CLAUDE_*_LATEST
# shortcuts offline. Tests marked @pytest.mark.api use the real API instead.
OFFLINE_ANTHROPIC_MODELS = [
    ("claude-haiku-4-5-20251001", "2025-10-15"),
    ("claude-sonnet-4-6", "2026-02-17"),
    ("claude-sonnet-5", "2026-06-29"),
    ("claude-sonnet-5-5", "2026-09-28"),
    ("claude-opus-5", "2026-07-24"),
    ("claude-opus-5-5", "2026-09-21"),
]


@pytest.fixture(autouse=True)
def _offline_latest_model_resolution(request, monkeypatch):
    """Keep "latest" model resolution off the network for non-API tests."""
    from bots.foundation import models

    models.clear_model_cache()
    if request.node.get_closest_marker("api") is None:
        monkeypatch.setattr(models, "_fetch_anthropic_models", lambda api_key=None: list(OFFLINE_ANTHROPIC_MODELS))
    yield
    models.clear_model_cache()
