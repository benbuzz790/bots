# Specification: Contract-Based Tool Validation for toolify
## Overview
Enhance the `toolify` decorator in `bots.dev.decorators` to support preconditions and postconditions, enabling tools to validate their operations before execution.
## Motivation
Some tools need to maintain system invariants. For example:
- Python editing tools must maintain syntactic correctness
- Vault management tools must preserve link integrity
- File operations must respect filesystem constraints
Currently, these checks are implemented ad-hoc within each tool. This specification provides a general mechanism for declarative contract checking.
## Design
### Contract Functions
A contract is a callable with signature:
```python
def contract(*args, **kwargs) -> tuple[bool, str]:
    """
    Args: Same parameters as the tool being validated
    Returns: (is_valid, error_message)
        - is_valid: True if contract passes, False otherwise
        - error_message: Empty string if valid, explanation if invalid
    """
```
**Contract Requirements:**
- Must be pure functions (no side effects)
- Can read system state but cannot modify it
- Receive the same parameters as the tool they validate
- Return (bool, str) tuple
- **May raise exceptions** - toolify already has exception-to-string handling that will be reused
### Enhanced toolify Signature
```python
def toolify(
    description: Optional[str] = None,
    preconditions: Optional[List[Callable]] = None,
    postconditions: Optional[List[Callable]] = None
) -> Callable:
    """
    Decorator that converts a function into a bot tool with contract validation.
    Args:
        description: Override the function's docstring
        preconditions: List of contracts to check before execution
        postconditions: List of contracts to check before execution
            (despite the name, these run before execution to validate the operation)
    Returns:
        Decorated function with contract checking and error handling
    """
```
### Execution Flow
1. **Precondition Checking**
   - Run each precondition with tool parameters
   - If any fails (returns False or raises exception), skip execution and return error
2. **Postcondition Checking**
   - Run each postcondition with tool parameters
   - If any fails (returns False or raises exception), skip execution and return error
3. **Tool Execution**
   - If all contracts pass, execute the actual tool
4. **Error Handling**
   - Collect all failed contract messages
   - Use existing `_process_error` logic from `bots.utils.helpers`
   - Return combined error message to the LLM
   - Format: "Contract violations:\nPreconditions:\n  - [error1]\nPostconditions:\n  - [error2]"
### Example Usage
```python
from bots.dev.decorators import toolify
def title_not_empty(title: str, content: str) -> tuple[bool, str]:
    if not title.strip():
        return False, "Title cannot be empty"
    return True, ""
def content_is_valid_markdown(title: str, content: str) -> tuple[bool, str]:
    issues = check_markdown(content)
    if issues:
        return False, f"Invalid markdown: {issues}"
    return True, ""
@toolify(
    description="Create a new note with the given title and content.",
    preconditions=[title_not_empty],
    postconditions=[content_is_valid_markdown]
)
def create_note(title: str, content: str) -> str:
    """Create a new note."""
    # Implementation
    return f"Created note: {title}"
```
### Backward Compatibility
- Existing `@toolify()` and `@toolify("description")` usage continues to work
- `preconditions` and `postconditions` default to None (no checking)
- No changes to existing tool behavior
## Implementation Notes
### Location
- Modify `bots/dev/decorators.py`
- Add contract checking logic to existing `toolify` decorator
- Reuse existing exception handling via `_process_error` from `bots.utils.helpers`
### Error Message Format
When contracts fail:
```
Contract validation failed:
Preconditions:
  - Title cannot be empty
Postconditions:
  - Invalid markdown: Missing closing bracket on line 5
```
### Exception Handling
- Contracts can return `(False, "message")` OR raise exceptions
- Both are handled uniformly via existing `_process_error` logic
- This reuses the robust exception-to-string conversion already in toolify
### Performance Considerations
- Contracts run synchronously before tool execution
- Keep contracts lightweight (read-only checks)
- No caching or memoization needed initially
## Testing Requirements
1. **Unit tests** for contract checking logic
2. **Integration tests** with sample tools
3. **Edge cases**:
   - Empty contract lists
   - Contracts that raise exceptions
   - Contracts that return (False, message)
   - Multiple failing contracts
   - Contracts with complex parameter signatures
   - Backward compatibility with existing toolify usage
## Future Enhancements (Out of Scope)
- True invariants (contracts that check state after execution with rollback)
- Contract composition/dependencies
- Performance profiling for contracts
- Contract violation metrics
## Success Criteria
- Existing toolify usage unaffected
- New contract parameters work as specified
- Clear error messages for contract failures
- Exceptions in contracts handled gracefully
- Documentation updated with examples
- Tests pass
