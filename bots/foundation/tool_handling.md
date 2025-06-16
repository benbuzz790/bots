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

## Serialization and Loading

### Saving State

The `to_dict` method:
1. Captures module details
2. Maps functions to their sources
3. Preserves tool schemas
4. Records request/result history

### Loading State

The `from_dict` method:
1. Recreates module contexts
2. Verifies code integrity
3. Rebuilds function environment
4. Restores tool mappings

#### Code Hash Verification
```python
current_code_hash = cls._get_code_hash(module_data['source'])
if current_code_hash != module_data['code_hash']:
    print(f'Warning: Code hash mismatch for module {file_path}')
```
- Ensures loaded code matches original
- Prevents execution of modified code
- Maintains security and reliability

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
   - Use module-level functions
   - Provide clear docstrings
   - Handle errors gracefully
   - Return string responses

2. Context Management:
   - Keep dependencies explicit
   - Avoid global state
   - Use pure functions when possible

3. Error Handling:
   - Catch specific exceptions
   - Provide informative messages
   - Allow for recovery

## Common Issues and Solutions

1. Missing Dependencies:
   - Ensure all imports are in function scope
   - Use try/except for optional imports
   - Document requirements

2. Context Loss:
   - Check function has proper module context
   - Verify globals are captured
   - Test serialization/deserialization

3. Tool Execution Failures:
   - Validate input parameters
   - Handle type conversions
   - Provide clear error messages

## Security Considerations

1. Code Execution:
   - Validate source before execution
   - Check code hashes
   - Limit execution context

2. Module Loading:
   - Verify file paths
   - Check module integrity
   - Control import scope

3. Input Validation:
   - Sanitize parameters
   - Limit resource usage
   - Handle malicious input

## Future Improvements

1. Tool System:
   - Support for class methods
   - Better closure handling
   - Improved type checking

2. Context Management:
   - More efficient serialization
   - Better dependency tracking
   - Enhanced security measures

3. Error Handling:
   - More specific error types
   - Better recovery mechanisms
   - Enhanced logging
