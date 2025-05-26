# Infinite Loop in `_tokenize_source` Function Causes Test Timeouts

## Summary

The `_tokenize_source` function in `python_edit.py` contains infinite loop conditions that cause specific test cases to hang indefinitely. The issue occurs during the tokenization phase when processing complex multiline content, particularly content involving nested docstrings, mixed quotes, and complex indentation patterns.

## Problem Description

### Current Behavior
- Test suite hangs on specific test cases involving complex multiline Python code
- The hang occurs specifically during tokenization, not detokenization
- Affected tests timeout rather than completing or failing with error messages
- The issue manifests as 100% CPU usage with no progress

### Expected Behavior
- All tokenization operations should complete within reasonable time bounds
- Complex multiline content should be processed without infinite loops
- Test suite should complete successfully or fail with meaningful error messages

## Root Cause Analysis

### Primary Issue: Catastrophic Backtracking in Regex Patterns

The triple-quote regex patterns contain nested quantifiers that trigger catastrophic backtracking:

```python
triple_quote_patterns = [
    '"""[^"\\\\]*(?:(?:\\\\.|"(?!""))[^"\\\\]*)*"""',  # Problematic pattern
    "'''[^'\\\\]*(?:(?:\\\\.|'(?!''))[^'\\\\]*)*'''"   # Problematic pattern
]
```

These patterns exhibit exponential time complexity when encountering malformed or deeply nested quote structures.

### Secondary Issue: Infinite Replacement Loops

The tokenization logic contains while loops that can cycle indefinitely:

```python
for pattern in triple_quote_patterns:
    while True:  # Potential infinite loop
        match = re.search(pattern, tokenized)
        if not match:
            break
        string_content = match.group()
        if contains_token(string_content):
            continue  # Can loop forever if condition never changes
        # ... replacement logic
```

When `contains_token()` returns `True` for content that continues to match the regex pattern, the loop restarts indefinitely without making progress.

## Steps to Reproduce

1. Create a test case with complex multiline content:
```python
content = '''def example():
    """
    Multiline docstring with "nested quotes"
    """
    # Comment with complex formatting
    pass'''
```

2. Call `_tokenize_source(content)`
3. Observe infinite loop and 100% CPU usage

## Impact Assessment

### Affected Components
- Test suite execution (multiple test timeouts)
- Python code editing functionality for complex multiline content
- Developer productivity due to unreliable test runs

### Severity
**High** - Prevents reliable testing and affects core functionality for certain code patterns

## Proposed Solution

### Phase 1: Immediate Mitigation
Implement iteration limits and progress tracking to prevent infinite loops:

```python
def _tokenize_source_safe(source: str) -> Tuple[str, Dict[str, str]]:
    # Add iteration limits
    MAX_ITERATIONS = 100
    
    for pattern in triple_quote_patterns:
        iteration_count = 0
        while iteration_count < MAX_ITERATIONS:
            iteration_count += 1
            match = re.search(pattern, tokenized)
            if not match:
                break
            
            # Track progress to detect stuck loops
            old_tokenized = tokenized
            
            # ... existing logic ...
            
            # Verify progress was made
            if tokenized == old_tokenized:
                break  # Exit if no progress
                
        if iteration_count >= MAX_ITERATIONS:
            raise ValueError(f"Tokenization iteration limit exceeded for pattern: {pattern}")
```

### Phase 2: Regex Pattern Optimization
Replace complex nested quantifiers with simpler, more predictable patterns:

```python
# Current problematic patterns
'"""[^"\\\\]*(?:(?:\\\\.|"(?!""))[^"\\\\]*)*"""'

# Proposed safer patterns  
r'"""(?:[^"\\]|\\.)*"""'  # Eliminates nested quantifiers
```

### Phase 3: Enhanced Error Handling
Add comprehensive logging and error reporting for tokenization failures to improve debugging capabilities.

## Acceptance Criteria

- [ ] All existing tests complete without timeouts
- [ ] Complex multiline content processes within reasonable time limits (< 1 second for typical cases)
- [ ] Tokenization failures produce clear error messages rather than hanging
- [ ] No regression in tokenization accuracy for existing working cases
- [ ] Performance impact of safety measures is minimal (< 10% slowdown for normal cases)

## Testing Strategy

### Unit Tests
- Test regex patterns in isolation with problematic input
- Verify iteration limits prevent infinite loops
- Validate that safety measures don't break normal functionality

### Integration Tests
- Run full test suite to ensure no regressions
- Test with various complex multiline content patterns
- Performance benchmarking for tokenization operations

## Additional Context

### Environment Details
- Affects all environments where the python_edit functionality is used
- No external dependencies involved
- Issue is deterministic and reproducible

### Related Issues
This issue may be related to similar timeout problems in other parts of the codebase that use complex regex patterns or nested loop structures.

### Priority Justification
The infinite loop behavior blocks essential development workflows and creates unpredictable test execution, making this a high-priority issue for resolution.