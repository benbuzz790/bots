# Tool Handling System Documentation

## Overview

The tool handling system enables bots to use Python functions as tools while preserving their complete execution context. This is more complex than simply passing function references because it needs to:

1. Preserve function source code for serialization
2. Maintain execution context (imports, globals, etc.)
3. Handle various function types (module-level, built-ins, dynamic functions)
4. Support saving and loading of bots with their tools
5. Manage tool execution safely

## Core Components

### ToolHandler Class

The base class that manages tool registration, execution, and persistence. Key responsibilities:

- Tool registration and management
- Request handling and execution
- State serialization/deserialization
- Error handling

### ModuleContext Class

```python
@dataclass
class ModuleContext:
    name: str          # Unique name for the module
    source: str        # Complete source code
    file_path: str     # Original file location or generated path
    namespace: ModuleType  # Execution environment
    code_hash: str     # Hash for integrity checking
```

Each field serves a specific purpose:

- `name`: Identifies the module uniquely in the runtime
- `source`: Enables recreation of functions when loading
- `file_path`: Used for both real files and dynamic modules
- `namespace`: Contains the actual execution environment including imports
- `code_hash`: Verifies code hasn't changed when loading

## Tool Addition Process

### 1. Single Function Addition (`add_tool`)

```python
def add_tool(self, func: Callable) -> None:
```

Process:

1. Generate tool schema (for LLM)
2. Check for existing module context
3. Handle different function types:
   - Built-in functions
   - Module-level functions
   - Dynamic/runtime functions
4. Create or use module context
5. Register tool in function map

#### Function Type Handling

a) Built-in Functions:

```python
if inspect.isbuiltin(func) or inspect.ismethoddescriptor(func):
    source = self._create_builtin_wrapper(func)
    context = {}
```

- Creates wrapper to handle built-in function limitations
- Empty context as built-ins have global availability

b) Regular Functions:

```python
try:
    source = inspect.getsource(func)
    if hasattr(func, '__globals__'):
        code = func.__code__
        names = code.co_names
        context = {name: func.__globals__[name]
                  for name in names
                  if name in func.__globals__}
```

- Captures source code
- Preserves necessary global variables
- Maintains imports and dependencies

### 2. Module Addition (`_add_tools_from_file`)

Process:

1. Read file content
2. Parse AST for function definitions
3. Create module namespace
4. Execute code in namespace
5. Add individual functions

#### AST Parsing Purpose

```python
tree = ast.parse(source)
function_nodes = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)]
```

- Identifies top-level functions before execution
- Ensures consistent order of tool addition
- Provides safety check before execution
- Helps filter private functions

### 3. Dynamic Module Handling (`_add_tools_from_module`)

Handles modules that exist only in memory:

1. Check for file path or source attribute
2. Create dynamic module name
3. Execute source in new namespace
4. Register functions as tools

## Function Serialization Strategy

### Overview

We use a **hybrid serialization approach** that handles different function types optimally:

1. **Regular Functions**: Source code + context (portable, secure, readable)
2. **Helper Functions**: Attempted dill serialization with source code fallback
3. **Dynamic Functions**: Attempted dill serialization with source code fallback
4. **Imported Callables**: Attempted dill serialization with source code fallback

### Why This Strategy?

#### Problem Solved

**Critical Bug**: Helper functions were being lost during save/load cycles because they exist in module globals, not in the reconstructed source code.
**Example**:

```python
# Original module contains:
def _convert_tool_inputs(...): pass  # Helper function
def view_dir(...):
    return _convert_tool_inputs(...)  # Main function uses helper
# After save/load with old strategy:
# ? view_dir() recreated from source
# ? _convert_tool_inputs() LOST - not in source!
# ?? Result: "name '_convert_tool_inputs' is not defined"
```

### Serialization Details

#### 1. Regular Functions (Source Code Strategy)

```python
# Serialization
source = inspect.getsource(func)  # Get source code
context = self._build_function_context(func)  # Capture dependencies
# Storage
modules[file_path] = {
    'source': source,  # Complete source code
    'globals': serialized_globals,  # Separate helper functions
    'code_hash': hash(source)  # Integrity check
}
# Restoration
exec(source, module.__dict__)  # Recreate main functions
_deserialize_globals(module.__dict__, globals)  # Restore helpers
```

**Why Source Code?**

- ? **Portable**: Works across Python versions and environments
- ? **Secure**: Human-readable, can be inspected
- ? **Maintainable**: Easy to debug and modify
- ? **Efficient**: Compact storage for large functions

#### 2. Helper Functions, Dynamic Functions, and Imported Callables (Hybrid Strategy)

**Serialization** (_serialize_globals):

```python
elif k.startswith('_') and callable(v):
    try:
        import dill
        pickled_func = dill.dumps(v)
        encoded_func = base64.b64encode(pickled_func).decode('ascii')
        serialized[k] = {'__helper_func__': True, 'pickled': encoded_func}
    except Exception as e:
        print(f'Warning: Could not dill serialize helper function {k}: {e}')
```

**Deserialization** (_deserialize_globals):

```python
elif isinstance(v, dict) and v.get('__helper_func__'):
    try:
        import dill
        pickled_func = base64.b64decode(v['pickled'].encode('ascii'))
        module_dict[k] = dill.loads(pickled_func)
    except Exception:
        # Silently skip - source code execution will handle this
        pass
```

**Why This Approach?**

- ? **Optimistic**: Try dill first for same-runtime scenarios (e.g., branching)
- ? **Graceful Fallback**: Source code execution recreates functions if dill fails
- ? **Silent Failures**: No warnings for expected failures (dynamic modules across runtimes)
- ? **Automatic**: No manual intervention needed
**When dill Works:**
- Same Python runtime (e.g., branching within a session)
- Functions from stable, importable modules
- Functions without dynamic module dependencies
**When dill Fails (Expected):**
- Cross-runtime serialization (save/load to disk)
- Functions from dynamic modules with `__runtime__.dynamic_module_*` names
- Functions with non-importable `__module__` attributes
**Why Failures Are Silent:**
- Source code execution (`exec(source, module.__dict__)`) runs AFTER deserialization attempts
- All functions referenced in the source code are recreated automatically
- Only truly missing functions would cause errors during execution
- Warnings would be noise since the fallback is automatic and reliable

#### 3. Dynamic Functions (Similar Hybrid Strategy)

```python
# Serialization (_serialize_dynamic_function)
def _serialize_dynamic_function(self, func: Callable) -> Dict[str, Any]:
    try:
        import dill
        serialized_data = dill.dumps(func)
        encoded_data = base64.b64encode(serialized_data).decode('ascii')
        return {
            'type': 'dill',
            'success': True,
            'data': encoded_data,
            'hash': hashlib.sha256(serialized_data).hexdigest()
        }
    except Exception:
        return self._serialize_function_metadata(func)  # Fallback
```

**Why dill attempt for Dynamic Functions?**

- ? **Works in same-runtime**: Useful for branching operations
- ? **Preserves state**: Closures, captured variables when possible
- ? **Verified**: Hash checking prevents tampering
- ? **Fallback**: Graceful degradation to source code or metadata

### Serialization Flow

```
Bot.save()
+-- Regular Functions
�   +-- Source Code ? modules[path]['source']
�   +-- Helper Functions ? modules[path]['globals']['__helper_func__'] (dill attempted)
+-- Dynamic Functions ? dynamic_functions[name] (dill attempted)
+-- Imported Callables ? globals['__imported_callable__'] (dill attempted)
Bot.load() or Branch
+-- Attempt dill deserialization (silent failures expected for cross-runtime)
+-- exec(source) ? Recreate all functions from source code
+-- Verify hashes ? Ensure integrity
```

### Benefits of Hybrid Strategy

1. **Best of Both Worlds**:
   - dill deserialization attempted first (fast, works in same-runtime)
   - Source code execution as automatic fallback (reliable, works cross-runtime)
2. **Robust Error Handling**:
   - Silent failures for expected scenarios (dynamic modules across runtimes)
   - Warnings only for serialization failures (during save)
   - Automatic fallback without user intervention
3. **Performance Optimized**:
   - Same-runtime operations avoid re-parsing source (e.g., branching)
   - Source code re-execution only when necessary
   - No redundant warnings for expected behaviors
4. **Future-Proof**:
   - Can handle new function types
   - Extensible serialization framework
   - Maintains backward compatibility

## Error Handling

Hierarchical error system:

```python
class ToolHandlerError(Exception):
    """Base exception class for ToolHandler errors"""
    pass

class ToolNotFoundError(ToolHandlerError):
    """Raised when a requested tool cannot be found"""
    pass

class ModuleLoadError(ToolHandlerError):
    """Raised when there's an error loading a module"""
    pass
```

Purpose:

- `ToolHandlerError`: Base class for categorizing errors
- `ToolNotFoundError`: Specific to missing tools
- `ModuleLoadError`: Handles module loading failures

Benefits:

- Enables specific error handling
- Facilitates debugging
- Maintains API consistency
- Allows error recovery strategies

## Tool Execution Process

1. Request Processing:
   - Parse LLM request
   - Validate tool existence
   - Prepare arguments

2. Execution:
   - Load correct function
   - Execute in preserved context
   - Capture results/errors

3. Response Handling:
   - Format tool output
   - Handle errors gracefully
   - Return to LLM

## Best Practices

1. Tool Development:
   - Use module-level functions for best portability
   - Provide clear docstrings
   - Handle errors gracefully
   - Return string responses
   - Keep helper functions in same module

2. Context Management:
   - Keep dependencies explicit
   - Avoid global state
   - Use pure functions when possible
   - Test save/load cycles

3. Error Handling:
   - Catch specific exceptions
   - Provide informative messages
   - Allow for recovery

## Common Issues and Solutions

1. **Helper Function Loss** (FIXED):
   - **Problem**: Helper functions missing after save/load
   - **Cause**: Helper functions not in main source code
   - **Solution**: dill serialization of globals preserves helpers
   - **Test**: Use test_specific_helper_bug.py to verify

2. Missing Dependencies:
   - Ensure all imports are in function scope
   - Use try/except for optional imports
   - Document requirements

3. Context Loss:
   - Check function has proper module context
   - Verify globals are captured
   - Test serialization/deserialization

4. Tool Execution Failures:
   - Validate input parameters
   - Handle type conversions
   - Provide clear error messages

## Security Considerations

1. Code Execution:
   - Validate source before execution
   - Check code hashes
   - Limit execution context

2. dill Deserialization:
   - Hash verification prevents tampering
   - Only deserialize trusted data
   - Graceful fallback for failures

3. Module Loading:
   - Verify file paths
   - Check module integrity
   - Control import scope

4. Input Validation:
   - Sanitize parameters
   - Limit resource usage
   - Handle malicious input

## Testing Strategy

Comprehensive test matrix covers:

1. **Helper Function Preservation**: `test_specific_helper_bug.py`
   - Tests exact CLI bug reproduction
   - Verifies _convert_tool_inputs preservation
   - Checks all helper function types

2. **Save/Load Matrix**: `test_save_load_matrix.py`
   - Tests all tool addition methods
   - Covers basic, save_load, save_load_twice scenarios
   - Comprehensive failure analysis

3. **Debug Tracing**: `test_save_load_debug.py`
   - Step-by-step serialization tracing
   - Before/after state comparison
   - Detailed helper function analysis

## Future Improvements

1. Tool System:
   - Support for class methods
   - Better closure handling
   - Improved type checking

2. Serialization:
   - More efficient dill usage
   - Compression for large functions
   - Incremental serialization

3. Context Management:
   - Better dependency tracking
   - Enhanced security measures
   - Lazy loading optimizations

4. Error Handling:
   - More specific error types
   - Better recovery mechanisms
   - Enhanced logging
