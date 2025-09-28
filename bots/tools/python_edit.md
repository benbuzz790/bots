# Python Edit Tool

## Overview

The `python_edit` tool is a sophisticated code manipulation utility that enables precise, scope-aware editing of Python files using pytest-style syntax. Unlike simple text-based editors, this tool understands Python's syntactic structure and can safely modify code at various levels of granularity - from entire files down to individual methods within nested classes.

## Core Philosophy

Traditional code editing approaches often rely on line numbers or simple text replacement, which becomes fragile when code changes. The python_edit tool instead uses **scope-based addressing**, allowing you to specify exactly which Python construct you want to modify using a hierarchical path syntax. This approach remains robust even as the surrounding code evolves.

The tool leverages LibCST (Concrete Syntax Tree) for parsing and manipulation, which preserves formatting, comments, and whitespace - crucial for maintaining code quality and readability in automated editing scenarios.

## Scope Addressing Syntax

The tool uses pytest-style scope syntax to identify target locations:

```
file.py::ClassName::method_name
file.py::function_name
file.py::OuterClass::InnerClass::method
```

This hierarchical addressing system allows precise targeting without relying on brittle line numbers or pattern matching that might break when code is refactored.

## Core Functionality

### 1. Scope Replacement
The primary operation replaces an entire scope (function, class, or method) with new code:

```python
python_edit("myfile.py::MyClass::method", "def method(self):\n    return 'new implementation'")
```

This completely replaces the target method while preserving the surrounding class structure.

### 2. Insertion Operations
The tool supports several insertion modes using the `coscope_with` parameter:

#### File-level Insertions
- `__FILE_START__`: Inserts code at the beginning of the file
- `__FILE_END__`: Inserts code at the end of the file

#### Scope-relative Insertions
- `"ClassName::method_name"`: Inserts after the specified method within the current scope
- `"method_name"`: Inserts after a method using simple name matching

#### Expression-based Insertions
- `'"x = 1"'`: Inserts after the first line that starts with the quoted expression
- `'"if condition:"'`: Can match multi-line constructs for complex insertion points

### 3. Import Handling
The tool automatically manages imports when editing files. When new code contains import statements, they are intelligently placed at the appropriate location in the file's import section, maintaining Python's conventional import organization.

## Technical Architecture

### AST vs CST Approach
The tool primarily uses LibCST (Concrete Syntax Tree) rather than Python's built-in AST (Abstract Syntax Tree). This choice is crucial because:

- **CST preserves formatting**: Comments, whitespace, and code style are maintained
- **Round-trip fidelity**: Code can be parsed and regenerated without losing information
- **Comment handling**: Unlike AST, CST can represent and manipulate comments as first-class constructs

### Scope Resolution
The tool implements a sophisticated scope resolution system:

1. **Path Parsing**: Scope paths are split into components and validated
2. **Tree Traversal**: The CST is traversed to locate the target scope
3. **Context Preservation**: Surrounding code structure is maintained during modifications

### Comment Processing
One of the most complex aspects of the tool is handling standalone comments, particularly for `__FILE_END__` insertions. When a user provides a comment like `"# End of file comment"`, the tool must:

1. Detect that the input is a comment-only construct
2. Convert it to a valid Python statement (pass with trailing comment)
3. Ensure proper placement and formatting

This is necessary because LibCST requires valid Python statements, but users often want to insert pure comments.

### Unicode and Encoding Safety
The tool includes robust Unicode handling through the `clean_unicode_string` utility, which:

- Removes byte-order marks (BOMs) that can cause parsing issues
- Handles encoding edge cases in CI environments
- Preserves intentional whitespace while cleaning problematic characters

However, this cleaning process initially caused issues with trailing newlines, requiring careful preservation logic to maintain proper file formatting.

## Error Handling and Safety

### Syntax Validation
All code modifications are validated through CST parsing before being written to files. This ensures that edits never produce syntactically invalid Python code.

### Safety Checks
The tool includes several safety mechanisms:

- **Large deletion protection**: Operations that would delete more than 100 lines require explicit confirmation via `delete_a_lot=True`
- **Scope validation**: Target scopes are verified to exist before modification
- **Ambiguity detection**: When insertion points are ambiguous, the tool reports errors rather than making assumptions

### Graceful Degradation
When operations fail, the tool provides detailed error messages that help users understand what went wrong and how to correct their requests.

## Implementation Challenges and Solutions

### Challenge 1: Comment-Only Modules
**Problem**: When users want to insert standalone comments (like `"# TODO: implement this"`), LibCST parses these as modules with zero statements in the body, causing insertion operations to fail silently.

**Solution**: The tool detects comment-only modules and converts them to `pass` statements with trailing comments, which are valid Python constructs that LibCST can manipulate.

### Challenge 2: Newline Preservation
**Problem**: The Unicode cleaning process strips trailing newlines, causing test failures and formatting issues.

**Solution**: Implemented newline preservation logic that detects when content originally ended with newlines and restores them after cleaning.

### Challenge 3: Logic Flow Complexity
**Problem**: The main editing function had complex conditional logic that could skip important operations (like `__FILE_END__` handling) due to incorrect ordering.

**Solution**: Restructured the conditional flow to prioritize special operations (`__FILE_START__`, `__FILE_END__`) before general scope-based operations.

## Usage Patterns

### Basic File Editing
```python
# Replace entire file content
python_edit("script.py", "print('Hello, World!')")

# Add code to end of file
python_edit("script.py", "# End marker", coscope_with="__FILE_END__")
```

### Class and Method Manipulation
```python
# Replace a method
python_edit("myfile.py::MyClass::old_method", '''
def new_method(self, param):
    """Improved implementation."""
    return param * 2
''')

# Add method after existing one
python_edit("myfile.py::MyClass", '''
def helper_method(self):
    return "helper"
''', coscope_with="MyClass::existing_method")
```

### Complex Insertions
```python
# Insert after specific code pattern
python_edit("myfile.py::function", "# Added comment", coscope_with='"x = calculate()"')
```

## Integration with Bot Framework

The python_edit tool is designed to work seamlessly with the broader bot framework, providing AI agents with the ability to make precise code modifications. The tool's scope-based approach aligns well with how AI models understand code structure, making it easier for bots to perform complex refactoring and code generation tasks.

The `@toolify()` decorator integrates the function into the bot's tool ecosystem, allowing it to be called naturally within AI conversations while maintaining proper error handling and logging.

## Future Considerations

The tool's architecture supports several potential enhancements:

- **Multi-file operations**: Extending scope syntax to handle cross-file refactoring
- **Undo/redo capabilities**: Maintaining operation history for complex editing sessions
- **Diff generation**: Providing detailed change summaries for review
- **Template-based editing**: Supporting parameterized code templates for common patterns

The current implementation provides a solid foundation for these advanced features while maintaining simplicity and reliability for everyday use cases.
