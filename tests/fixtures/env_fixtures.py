"""Environment setup and cleanup fixtures.

Provides fixtures for managing test environment variables and configuration.
"""
import pytest
import os


@pytest.fixture
def clean_otel_env():
    """Clean OpenTelemetry environment variables.

    Removes OTEL-related environment variables before test and restores after.
    Used in observability tests to ensure clean state.

    Usage:
        def test_something(clean_otel_env):
            # Test runs with clean OTEL environment
            # Original env vars restored after test
    """
    # Save original values
    otel_vars = [
        'OTEL_EXPORTER_OTLP_ENDPOINT',
        'OTEL_EXPORTER_OTLP_HEADERS',
        'OTEL_SERVICE_NAME',
        'OTEL_TRACES_EXPORTER',
        'OTEL_METRICS_EXPORTER',
        'OTEL_LOGS_EXPORTER',
    ]

    original_values = {}
    for var in otel_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def mock_api_keys():
    """Mock API key environment variables.

    Sets mock API keys for testing without real credentials.

    Usage:
        def test_something(mock_api_keys):
            # Test runs with mock API keys
            # Original keys restored after test
    """
    api_key_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'GOOGLE_API_KEY',
    ]

    original_values = {}
    for var in api_key_vars:
        original_values[var] = os.environ.get(var)
        os.environ[var] = f'mock_{var.lower()}_12345'

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def clean_test_env():
    """Clean test environment.

    Provides a clean environment for tests by removing test-specific variables.

    Usage:
        def test_something(clean_test_env):
            # Test runs with clean environment
    """
    test_vars = [
        'TEST_MODE',
        'DEBUG',
        'VERBOSE',
    ]

    original_values = {}
    for var in test_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]
