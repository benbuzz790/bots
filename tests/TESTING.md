# Testing Guide

This document describes the testing infrastructure and best practices for the bots project.

## Test Organization

Our test suite is organized into three categories following pytest best practices:

```
tests/
â”œâ”€â”€ unit/           # Fast, isolated tests with mocks
â”œâ”€â”€ integration/    # Tests with real APIs, file I/O, tool execution
â”œâ”€â”€ e2e/           # End-to-end workflow tests
â”œâ”€â”€ fixtures/      # Shared test fixtures
â””â”€â”€ helpers/       # Test utilities and helpers
```

### Test Categories

#### Unit Tests (`tests/unit/`)

- **Purpose**: Test individual functions/classes in isolation
- **Characteristics**:
  - No external API calls (use mocks)
  - No file I/O (use in-memory or temp fixtures)
  - Fast execution (< 1 second each)
  - Deterministic results
- **Examples**: Tool handler logic, message formatting, conversation tree operations
- **Run with**: `pytest tests/unit/ -v`

#### Integration Tests (`tests/integration/`)

- **Purpose**: Test interactions between components
- **Characteristics**:
  - Real API calls (with rate limiting/retry)
  - File system operations
  - Tool execution
  - Moderate execution time (1-10 seconds each)
- **Examples**: Bot save/load, provider-specific behavior, code tool execution
- **Run with**: `pytest tests/integration/ -v`

#### E2E Tests (`tests/e2e/`)

- **Purpose**: Test complete user workflows
- **Characteristics**:
  - Multiple components working together
  - CLI interactions
  - Functional prompt chains
  - Slower execution (10+ seconds each)
- **Examples**: CLI workflows, functional prompt sequences, full conversation flows
- **Run with**: `pytest tests/e2e/ -v`

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest

# Run only unit tests (fast feedback)
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run e2e tests
pytest tests/e2e/ -v

# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m e2e

# Run tests in parallel
pytest -n auto

# Run with coverage
pytest --cov=bots --cov-report=term-missing
```


### Smart Test Selection with pytest-testmon

pytest-testmon tracks which source files each test depends on and only runs tests affected by your changes:

```bash
# First run: builds dependency map (runs full suite)
pytest --testmon

# Subsequent runs: only runs tests affected by changed files
pytest --testmon

# Force full run (rebuild dependency map)
pytest --testmon --testmon-forceselect

# Combine with other options
pytest --testmon -v tests/unit/
```

**How it works:**
- Stores dependency data in `.testmondata` (gitignored)
- Automatically detects which tests depend on which source files
- Skips tests whose dependencies haven't changed
- Great for local development; CI still runs full suite

**Note:** The first run after installing testmon will run all tests to build the dependency map.

### Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.flaky` - Tests that may fail intermittently
- `@pytest.mark.serial` - Tests that must run serially (not in parallel)

**Examples:**

```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests that aren't flaky
pytest -m "integration and not flaky"

# Run unit and integration tests
pytest -m "unit or integration"
```

## Using Fixtures

### Shared Fixtures

Common fixtures are available in `tests/fixtures/`:

#### Bot Fixtures (`bot_fixtures.py`)

```python
def test_with_mock_bot(mock_bot_class):
    """Use a mocked bot for unit testing."""
    bot = mock_bot_class()
    response = bot.respond("test")
    assert response is not None

def test_with_real_bot(real_anthropic_bot):
    """Use a real bot for integration testing."""
    response = real_anthropic_bot.respond("Hello")
    assert "hello" in response.lower()
```

#### File Fixtures (`file_fixtures.py`)

```python
def test_with_temp_file(temp_test_file):
    """Automatically cleaned up temp file."""
    filepath = temp_test_file("print('hello')", extension="py")
    assert os.path.exists(filepath)
    # File is automatically cleaned up after test
```

#### Mock Fixtures (`mock_fixtures.py`)

```python
def test_with_mock_input(mock_input):
    """Mock user input for CLI tests."""
    mock_input.return_value = "test input"
    result = get_user_input()
    assert result == "test input"
```

### Creating Custom Fixtures

Add category-specific fixtures to the appropriate `conftest.py`:

```python
# tests/unit/conftest.py
import pytest

@pytest.fixture
def sample_conversation():
    """Sample conversation for unit tests."""
    return {
        'messages': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'}
        ]
    }
```

## Writing Tests

### Test Structure (AAA Pattern)

Follow the Arrange-Act-Assert pattern:

```python
def test_example():
    # Arrange - Set up test data and conditions
    bot = MockBot()
    prompt = "test prompt"

    # Act - Execute the code under test
    response = bot.respond(prompt)

    # Assert - Verify the results
    assert response is not None
    assert "test" in response
```

### Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`
- Fixtures: descriptive names (e.g., `mock_bot_class`, `temp_test_file`)

### Parameterized Tests

Use `@pytest.mark.parametrize` for testing multiple inputs:

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("test", "TEST"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### Async Tests

Mark async tests with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

## Test Coverage

### Checking Coverage

```bash
# Run tests with coverage report
pytest --cov=bots --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Coverage Requirements

- Minimum coverage: 80%
- New code should have 90%+ coverage
- Critical paths should have 100% coverage


## Special Test Cases

### Installation Tests

The `test_install_in_fresh_environment.py` tests verify that package dependencies are correctly specified:

- **Auto-skip in parallel mode**: These tests automatically skip when running with `pytest` (parallel mode)
- **Run explicitly with**: `pytest tests/test_install_in_fresh_environment.py -n0 -v`
- **Why serial only**: They create virtual environments and install packages, which causes worker crashes in parallel mode
- **CI handling**: PR checks run them separately with `-n0`; main CI runs them automatically (uses `-n 0` by default)

See `tests/README_INSTALL_TESTS.md` for more details.

### Tests with Input Patching

Some tests use `@patch("builtins.input")` to mock user input:
- `tests/unit/test_fp_handler.py`
- `tests/unit/test_prompt_handler.py`
- `tests/unit/test_cli_frontend.py`
- `tests/unit/test_cli/test_fp_wizard_complete.py`
- `tests/unit/test_cli/test_save_auto_commands.py`

These tests automatically skip when running with xdist (parallel mode) because input patching is incompatible with worker processes.

## CI/CD Integration

Tests run automatically on every PR:

1. **Unit tests** run first (fail fast)
2. **Integration tests** run in parallel
3. **E2E tests** run last

All tests must pass before merging.

## Troubleshooting

### Common Issues

**Tests fail locally but pass in CI:**

- Check for environment-specific issues
- Ensure all dependencies are installed
- Check for file path differences (Windows vs Linux)

**Flaky tests:**

- Add `@pytest.mark.flaky(reruns=3)` marker
- Investigate race conditions
- Add appropriate waits/timeouts

**Slow tests:**

- Consider moving to integration or e2e category
- Add `@pytest.mark.slow` marker
- Optimize test setup/teardown

### Getting Help

- Check existing tests for examples
- Review fixture documentation in `tests/fixtures/`
- Ask in PR comments or issues

## Best Practices

1. **Keep unit tests fast** - Use mocks, avoid I/O
2. **Make tests independent** - No shared state between tests
3. **Use descriptive names** - Test name should describe what it tests
4. **One assertion per test** - Or at least one logical concept
5. **Clean up resources** - Use fixtures for automatic cleanup
6. **Document complex tests** - Add comments explaining non-obvious logic
7. **Test edge cases** - Don't just test the happy path
8. **Keep tests maintainable** - Refactor tests when needed

## Statistics

- **Total Tests**: 809
- **Unit Tests**: 33 files (36.7%)
- **Integration Tests**: 31 files (34.4%)
- **E2E Tests**: 26 files (28.9%)
- **Pass Rate**: 97%+
- **Parallel Execution**: 27% speed improvement

---

*Last updated: 7-Oct-2025*
*Work Order: WO012_Test_Suite_Organization*
