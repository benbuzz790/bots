
# CLI Tool Crash Bug Fix Summary

## Problem Description
When using the CLI and a tool crashes, the CLI backs up the conversation to restore the previous state. However, the tool handler's state (requests and results) was not being cleared, leading to corruption in the tool request/result structure for subsequent messages.

## Root Cause Analysis
1. **Normal Flow**: `Bot._cvsn_respond()` calls `tool_handler.clear()` at the beginning to reset state
2. **Bug Scenario**: When a tool crashes, an exception is raised
3. **CLI Backup**: The CLI catches the exception and restores `bot.conversation` from backup
4. **Missing Step**: The CLI did NOT clear the `tool_handler` state
5. **Corruption**: Old tool results remain in `tool_handler.results` while new requests are processed
6. **Symptom**: Mismatched `tool_use_id`s between requests and results, causing conversation structure corruption

## The Fix
Added `bot.tool_handler.clear()` calls in two locations in `bots/dev/cli.py`:

### Location 1: `_handle_command()` exception handler (line ~1599)
```python
except Exception as e:
    pretty(f"Command error: {str(e)}", "Error", ...)
    if self.context.conversation_backup:
        # Clear tool handler state to prevent corruption from failed tool executions
        bot.tool_handler.clear()
        bot.conversation = self.context.conversation_backup
```

### Location 2: `_handle_chat()` exception handler (line ~1641)
```python
except Exception as e:
    pretty(f"Chat error: {str(e)}", "Error", ...)
    if self.context.conversation_backup:
        # Clear tool handler state to prevent corruption from failed tool executions
        bot.tool_handler.clear()
        bot.conversation = self.context.conversation_backup
```

## Verification
Created comprehensive tests that demonstrate:
1. **With Fix**: Tool handler state is properly cleared, preventing corruption
2. **Without Fix**: Results accumulate, causing tool_use_id mismatches

## Test Results
✅ **Fix Verified**: After clearing tool handler, no corruption occurs
🐛 **Bug Demonstrated**: Without clearing, results accumulate (1 request, 2 results)

## Impact
- **Before**: Tool crashes could corrupt the conversation structure, making subsequent tool usage unreliable
- **After**: Tool crashes are handled cleanly, conversation state is properly restored without corruption

## Files Modified
- `bots/dev/cli.py`: Added tool handler clearing in exception handlers
- `tests/test_cli_tool_crash_bug.py`: Original bug reproduction test
- `tests/test_cli_tool_crash_bug_fix.py`: Fix verification test
