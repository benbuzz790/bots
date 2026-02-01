# Fix for Recursion Error in Bot Deepcopy with Tool Management Tools
## Problem
When loading a bot from disk and sending a message, users encountered maximum recursion depth errors:
```
Warning: Could not dill serialize imported callable view_tools: maximum recursion depth exceeded
Warning: Could not dill serialize imported callable load_tools: maximum recursion depth exceeded
```
This occurred during auto-backup operations (enabled by default in CLI).
## Root Cause
The issue was caused by circular references in tool functions:
1. Tool functions (view_tools, load_tools, etc.) use the @toolify decorator
2. This decorator injects a _bot parameter for dependency injection
3. This creates circular references: bot → tool_handler → tool_functions → _bot → bot
4. During deepcopy (triggered by auto-backup via bot * 1):
   - __getstate__ tried to dill-serialize the tool_handler
   - Dill attempted to follow the circular references infinitely
   - Python hit maximum recursion depth
## Solution
Implemented a custom __deepcopy__ method that properly handles circular references:
### Key Changes:
1. **Custom __deepcopy__ method** (Bot class):
   - Manually copies each bot attribute
   - For tool_handler: uses to_dict(for_persistence=True) + from_dict()
   - This leverages the existing save/load serialization infrastructure
   - Properly handles tool functions without hitting circular references
   - Skips mailbox (reconstructed) and callbacks (environment-specific)
2. **Added for_persistence parameter** to ToolHandler.to_dict():
   - When True: serializes globals (for disk storage)
   - When False: skips globals (for in-memory deepcopy, avoids circular refs)
3. **Updated _serialize_for_deepcopy()** and **_deserialize_from_deepcopy()**:
   - Try to dill-preserve tool_handler first
   - Fallback to dict serialization without globals if dill fails
   - Handle dill-preserved tool_handler during deserialization
## Why This is the Right Fix
1. **Structural solution**: Addresses the root cause (circular references) rather than hiding symptoms
2. **Leverages existing infrastructure**: Uses the proven save/load serialization mechanism
3. **No silent failures**: Errors are properly handled, not suppressed
4. **Maintains all functionality**: Deepcopy, save/load, branch_self all work correctly
5. **Backward compatible**: Existing saved bots load correctly
## Testing
All tests pass:
- ✓ Manual test: deepcopy with tool management tools
- ✓ Manual test: bot multiplication (bot * 2)
- ✓ Manual test: save/load cycle with deepcopy
- ✓ Unit test: test_branch_self_preserves_callbacks
- ✓ Unit tests: test_dill_serialization.py (all 3 tests)
## Impact
- **User-facing**: No more recursion errors when loading bots
- **Performance**: Efficient deepcopy using existing serialization
- **Functionality**: All features work correctly (save/load, backup/restore, branch_self)
- **Code quality**: Proper structural fix, not a band-aid
## Files Changed
- bots/foundation/base.py:
  - Added Bot.__deepcopy__() method
  - Added for_persistence parameter to ToolHandler.to_dict()
  - Updated Bot._serialize_for_deepcopy()
  - Updated Bot._deserialize_from_deepcopy()
