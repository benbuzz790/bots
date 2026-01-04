# Preventing MagicMock Recursion Issues in CLI Tests

## The Problem

When testing CLI functionality with `MagicMock` bots, a circular reference can cause infinite recursion or stack overflow:

1. `MagicMock` bot is assigned to `context.bot_instance`
2. Callbacks are attached: `bot.callbacks = RealTimeDisplayCallbacks(context)`
3. This creates: `mock_bot.callbacks.context.bot_instance` → `mock_bot` (circular reference)
4. When `auto_backup` tries to copy the bot with `(bot * 1)[0]`, it attempts to deep copy the `MagicMock`
5. Deep copying a `MagicMock` with circular references causes infinite recursion

## Structural Solutions Implemented

### 1. **Reusable Fixture** (tests/fixtures/mock_fixtures.py)

Created `safe_cli_context` fixture that provides a pre-configured safe context:

```python
@pytest.fixture
def safe_cli_context():
    context = CLIContext()
    context.config.auto_backup = False
    context.config.auto_stash = False
    context.config.auto_restore_on_error = False

    mock_bot = MagicMock()
    # ... setup mock_bot ...
    context.bot_instance = mock_bot

    return context, mock_bot
```

### 2. **Documentation in Fixture File**

Added comprehensive guidelines at the end of `tests/fixtures/mock_fixtures.py` explaining:
- The problem
- Three solution approaches (fixture, manual, real bots)
- Affected tests
- Usage examples

### 3. **Updated Affected Tests**

Fixed all tests that use `MagicMock` with `CLIContext`:
- `tests/e2e/test_quiet_fix_verification.py` ✅
- `tests/e2e/test_quiet_duplicate.py` ✅ (also removed skip marker)
- `tests/e2e/test_cli_load.py` ✅

All now disable `auto_backup`, `auto_stash`, and `auto_restore_on_error` in their setup.

### 4. **Pattern for Future Tests**

**Option A: Use the fixture (recommended)**
```python
def test_something(safe_cli_context):
    context, mock_bot = safe_cli_context
    # Safe to use
```

**Option B: Manual setup**
```python
def setUp(self):
    self.context = CLIContext()
    self.context.config.auto_backup = False
    self.context.config.auto_stash = False
    self.context.config.auto_restore_on_error = False
    # ... rest of setup ...
```

**Option C: Use real bots (best for integration tests)**
```python
def test_something():
    bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
    context = CLIContext()
    context.bot_instance = bot
    # Real bots handle copying properly
```

## Why This Prevents Future Issues

1. **Centralized fixture**: New tests can use `safe_cli_context` without knowing the details
2. **Documentation**: Guidelines in the fixture file explain the issue for developers
3. **Pattern established**: All existing tests now follow the same pattern
4. **Comments in code**: Each fixed test has a comment pointing to the documentation

## Alternative Considered But Not Implemented

We considered making `CLIConfig` default `auto_backup=False` in test environments, but decided against it because:
- It would hide the real behavior from integration tests
- Tests should explicitly opt-in to safe mocking patterns
- Real bot tests should test with real settings

## Testing the Fix

The fixed tests can now run safely with `-n 0`:
```bash
pytest tests/e2e/test_quiet_fix_verification.py -n 0 -v
pytest tests/e2e/test_quiet_duplicate.py -n 0 -v
pytest tests/e2e/test_cli_load.py -n 0 -v
```
