# Branch Self Recursion Bug Fix
## Summary
Fixed the critical bug where recursive branching (calling `branch_self` within a branch created by `branch_self`) caused an infinite loop.
## Problem Description
When `branch_self` was called within a branch, it would enter an infinite loop because:
1. `branch_self` saves the bot state to a temporary file
2. Each branch loads the bot from that file using `Bot.load()`
3. `Bot.load()` always positions the conversation pointer at `replies[-1]` (the newest node)
4. When a branch calls `branch_self` again, it loads the saved state which includes the parent `branch_self` call
5. The loaded bot's conversation pointer moves to the newest node, which may include the `branch_self` tool call
6. This causes the branch to see and potentially re-execute the same `branch_self` call infinitely
## Solution
Implemented a node tagging system to track the correct branching point:
1. **Before saving**: Tag the current conversation node with a unique attribute (e.g., `_branch_self_anchor_abc123`)
2. **After loading in branch**: Search for the tagged node in the conversation tree
3. **Position at tagged node**: Set the branch bot's conversation pointer to the tagged node instead of using the default `replies[-1]`
4. **Clean up**: Remove the tag after positioning to prevent pollution
### Code Changes
**File**: `bots/tools/self_tools.py`
**Key modifications**:
1. Added node tagging before save:
```python
branch_tag = f"_branch_self_anchor_{uuid.uuid4().hex[:8]}"
setattr(original_node, branch_tag, True)
```
2. Added tag search and positioning in `execute_branch()`:
```python
def find_tagged_node(node):
    """Recursively search for the node with the branch tag."""
    # Search entire tree for node with _branch_self_anchor_ attribute
    ...
tagged_node = find_tagged_node(branch_bot.conversation)
if tagged_node:
    branch_bot.conversation = tagged_node
    # Remove tag from this branch's copy
    delattr(tagged_node, attr)
```
3. Added tag cleanup after branching:
```python
if hasattr(original_node, branch_tag):
    delattr(original_node, branch_tag)
```
## Testing
Created comprehensive test suite in `tests/e2e/test_branch_self_recursive.py`:
### Test Results
✅ **test_single_level_recursion** - PASSED
- Verifies that `branch_self` can be called once within a branch
- Confirms nodes are added without infinite loop
✅ **test_two_level_recursion** - PASSED  
- Tests deeper nesting with three levels of `branch_self` calls
- Ensures multiple levels of recursion work correctly
✅ **test_recursive_branching_no_infinite_loop** - PASSED
- Timeout test to catch infinite loops
- Confirms recursive branching completes in reasonable time
✅ **Existing tests** - ALL PASSED
- `test_branch_self_tracking.py` - All 4 tests passed
- Confirms backward compatibility maintained
## Technical Details
### Why This Works
The tag-based approach ensures that:
1. Each branch loads from the same saved file but positions at the correct node
2. The tagged node represents the conversation state *before* the `branch_self` call
3. Branches don't see their parent's `branch_self` call in their conversation context
4. The tag is unique per `branch_self` invocation, preventing conflicts
### Serialization Compatibility
The solution leverages the existing `ConversationNode` serialization:
- `ConversationNode.__init__` accepts `**kwargs` for arbitrary attributes
- `_to_dict_self()` serializes all non-private, non-callable attributes
- Tags are automatically saved and restored through the normal save/load cycle
## Success Criteria Met
- ✅ Recursive branching works correctly without infinite loops
- ✅ Non-recursive branching continues to work as expected  
- ✅ Tests added to prevent regression
- ✅ Backward compatibility maintained
## Future Considerations
1. The current implementation searches the entire tree for the tag - could be optimized if needed
2. Tags are cleaned up immediately, but error handling could be added for edge cases
3. Consider adding a depth limit for recursive branching as a safety measure
## Related Issues
- Fixes the bug described in `_work_orders/WO_branch_self_recursion_bug.md`
- Addresses user observation about save/load positioning behavior
- Prevents expensive infinite loops that consume API credits
