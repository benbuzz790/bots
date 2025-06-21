# Tools Reference Guide
The bots library provides a comprehensive set of tools that enable AI agents to interact with files, execute code, and perform various system operations. This guide covers all available tools organized by category.
## Table of Contents
1. [File Operations](#file-operations)
2. [Code Editing Tools](#code-editing-tools)
3. [Python Execution](#python-execution)
4. [Terminal Operations](#terminal-operations)
5. [Meta Tools](#meta-tools)
6. [Self Tools](#self-tools)
7. [BOM Management](#bom-management)
---
## File Operations
### view()
**Purpose**: Display file contents with line numbers and filtering options.
**When to use**: When you need to examine file contents, search for specific text, or view specific line ranges.
**Parameters**:
- `file_path` (str): Path to the file to view
- `start_line` (str, optional): Starting line number (1-indexed)
- `end_line` (str, optional): Ending line number (1-indexed)
- `around_str_match` (str, optional): String to search for, shows lines around matches
- `dist_from_match` (str, optional): Number of lines to show before/after matches (default: 10)
**Examples**:
```python
# View entire file
view("main.py")
# View specific line range
view("main.py", start_line="10", end_line="20")
# Search for text and show context
view("main.py", around_str_match="def main", dist_from_match="5")
```
### view_dir()
**Purpose**: Create a summary of directory structure with file filtering.
**When to use**: When you need to understand project structure or find files with specific extensions.
**Parameters**:
- `start_path` (str): Root directory to scan (default: ".")
- `output_file` (str, optional): File to save the structure to
- `target_extensions` (str): List of file extensions as string (default: "['py', 'txt', 'md']")
- `max_lines` (int): Maximum output lines (default: 500)
**Examples**:
```python
# View Python project structure
view_dir(".", target_extensions="['py', 'md', 'txt']")
# Save structure to file
view_dir("src/", output_file="project_structure.txt")
# View only Python files
view_dir(".", target_extensions="['py']", max_lines=200)
```
### patch_edit()
**Purpose**: Apply git-style unified diff patches to files.
**When to use**: When you need to make precise, contextual changes to files with exact line matching.
**Parameters**:
- `file_path` (str): Path to the file to modify
- `patch_content` (str): Unified diff format patch content
**Examples**:
```python
# Apply a simple patch
patch_edit("main.py", '''
@@ -10,3 +10,4 @@
 def hello():
     print("Hello")
+    print("World")
     return True
''')
```
**Tips**:
- Small, focused changes work best
- Include surrounding context for better matching
- Exact content matching is important
- Whitespace matters in target lines
---
## Code Editing Tools
### Python Editing Tools
#### add_imports()
**Purpose**: Add import statements to Python files, avoiding duplicates.
**When to use**: When you need to add new imports to existing Python files.
**Parameters**:
- `file_path` (str): Path to the Python file
- `code` (str): Import statements (can include multi-line imports)
**Examples**:
```python
# Add single import
add_imports("main.py", "import os")
# Add multiple imports
add_imports("main.py", """
import os
import sys
from typing import List, Dict
""")
# Add complex import
add_imports("main.py", """
from collections import (
    defaultdict,
    Counter,
    OrderedDict
)
""")
```
#### add_class()
**Purpose**: Add a new class definition to a Python file.
**Parameters**:
- `file_path` (str): Path to the file
- `class_def` (str): Complete class definition
**Examples**:
```python
add_class("models.py", """
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    def get_info(self) -> dict:
        return {"name": self.name, "email": self.email}
""")
```
#### add_function_to_file()
**Purpose**: Add function definitions to Python files.
**Parameters**:
- `file_path` (str): Path to the file
- `new_function_def` (str): Function definition(s)
- `class_name` (str, optional): Add to specific class if provided
**Examples**:
```python
# Add standalone function
add_function_to_file("utils.py", """
def calculate_average(numbers: list) -> float:
    return sum(numbers) / len(numbers) if numbers else 0
""")
# Add method to class
add_function_to_file("models.py", """
def validate_email(self) -> bool:
    return "@" in self.email
""", class_name="User")
```
#### replace_function()
**Purpose**: Replace existing function definitions.
**Parameters**:
- `file_path` (str): Path to the file
- `new_function_def` (str): New function definition
- `class_name` (str, optional): Replace within specific class
**Examples**:
```python
replace_function("utils.py", """
def calculate_average(numbers: list) -> float:
    '''Calculate average with error handling'''
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
""")
```
### Advanced Python Editing
#### python_edit()
**Purpose**: Advanced Python code editing using pytest-style scope syntax.
**When to use**: For precise, scope-aware editing of Python files.
**Parameters**:
- `target_scope` (str): Pytest-style scope (e.g., "file.py::Class::method")
- `code` (str): Python code to insert/replace
- `insert_after` (str, optional): Where to insert code
**Examples**:
```python
# Replace entire function
python_edit("main.py::calculate_sum", """
def calculate_sum(a: int, b: int) -> int:
    '''Add two integers with validation'''
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Arguments must be integers")
    return a + b
""")
# Add method to class
python_edit("models.py::User", """
def get_display_name(self) -> str:
    return f"{self.name} <{self.email}>"
""", insert_after="User::__init__")
# Insert at file start
python_edit("config.py", """
# Configuration constants
DEBUG = True
VERSION = "1.0.0"
""", insert_after="__FILE_START__")
```
**Scope Syntax**:
- `"file.py"` - Whole file
- `"file.py::MyClass"` - Specific class
- `"file.py::my_function"` - Specific function
- `"file.py::MyClass::method"` - Class method
- `"file.py::Outer::Inner::method"` - Nested structures
---
## Python Execution
### _execute_python_code()
**Purpose**: Execute Python code in a stateless environment with timeout handling.
**When to use**: When you need to run Python code and capture its output safely.
**Parameters**:
- `code` (str): Syntactically correct Python code
- `timeout` (int): Maximum execution time in seconds (default: 300)
**Examples**:
```python
# Simple calculation
_execute_python_code("""
result = 2 + 2
print(f"Result: {result}")
""")
# Data processing
_execute_python_code("""
import json
data = {"name": "John", "age": 30}
print(json.dumps(data, indent=2))
""")
# File operations
_execute_python_code("""
with open("test.txt", "w") as f:
    f.write("Hello, World!")
print("File created successfully")
""")
```
**Features**:
- Cross-platform timeout handling
- UTF-8 encoding support
- Automatic error handling and reporting
- Isolated execution environment
---
## Terminal Operations
### execute_powershell()
**Purpose**: Execute PowerShell commands in a stateful environment with automatic BOM removal.
**When to use**: For system operations, file management, git commands, or CLI tool interactions.
**Parameters**:
- `command` (str): PowerShell command to execute
- `output_length_limit` (str): Maximum output lines (default: "2500")
- `timeout` (str): Timeout in seconds (default: "60")
**Examples**:
```python
# Basic file operations
execute_powershell("Get-ChildItem -Path . -Filter '*.py'")
# Git operations
execute_powershell("git status")
execute_powershell("git add . && git commit -m 'Update files'")
# System information
execute_powershell("Get-Process | Where-Object {$_.CPU -gt 100}")
# Package management
execute_powershell("pip install requests")
```
**Features**:
- Stateful session (directory changes persist)
- Automatic BOM removal from created files
- UTF-8 encoding support
- Command chaining with `&&`
- Session recovery on failures
### BOM Management Tools
#### remove_bom_from_current_directory()
**Purpose**: Remove Byte Order Marks (BOMs) from text files in current directory.
**Parameters**:
- `recursive` (bool): Process subdirectories (default: True)
#### remove_bom_from_files()
**Purpose**: Remove BOMs from files matching a pattern.
**Parameters**:
- `file_pattern` (str): Glob pattern (e.g., "*.py", "**/*.txt")
#### check_files_for_bom()
**Purpose**: Check for BOMs without removing them.
**Parameters**:
- `directory` (str): Directory to check (default: current)
**Examples**:
```python
# Clean current directory
remove_bom_from_current_directory(recursive=True)
# Clean specific file types
remove_bom_from_files("*.py")
remove_bom_from_files("**/*.json")
# Check for BOMs
check_files_for_bom("src/")
```
---
## Meta Tools
### message_bot()
**Purpose**: Load a bot, send it a message, and let it work until completion.
**When to use**: When you need to delegate a task to another specialized bot.
**Parameters**:
- `bot_path` (str): File path to the saved bot
- `message` (str): Message to send to the bot
**Examples**:
```python
# Delegate code review task
message_bot("review_bot.bot", """
Please review the code in main.py and identify any potential issues:
- Security vulnerabilities
- Performance problems
- Code style violations
Reply '/DONE' when complete.
""")
```
### initialize_file_bot()
**Purpose**: Create and initialize a new file-editing bot.
**When to use**: When you need a specialized bot for managing specific files.
**Parameters**:
- `file_name` (str): Name/path of file the bot will manage
- `system_message` (str): System message defining the bot's role
**Examples**:
```python
initialize_file_bot("database.py", """
You are a database management specialist. Your role is to:
- Design and implement database schemas
- Write efficient queries
- Ensure data integrity
- Handle database migrations
""")
```
### generate_project()
**Purpose**: Execute the standard project generation process using hierarchical AI assistants.
**When to use**: When you need to create a complete Python project from specifications.
**Parameters**:
- `spec` (str): Project specification describing the desired system
**Examples**:
```python
generate_project("""
Create a web scraping tool that:
- Scrapes product data from e-commerce sites
- Stores data in SQLite database
- Provides REST API for data access
- Includes rate limiting and error handling
- Has comprehensive test suite
""")
```
---
## Self Tools
### get_own_info()
**Purpose**: Get information about the current bot's configuration.
**When to use**: When you need to inspect your current settings and capabilities.
**Returns**: JSON string with bot information including name, role, model settings, and tool count.
**Examples**:
```python
# Check current configuration
info = get_own_info()
print(info)  # {"name": "MyBot", "role": "assistant", ...}
```
### branch_self()
**Purpose**: Create multiple conversation branches to explore different approaches.
**When to use**: When you need to tackle multiple related tasks or try different solutions.
**Parameters**:
- `self_prompts` (str): List of prompts as string array
- `allow_work` (str): "True" to let branches use tools, "False" for single responses
**Examples**:
```python
# Parallel task execution
branch_self("""[
    'Analyze the database schema and create documentation. Done when schema.md exists with complete table descriptions.',
    'Review the API endpoints and create OpenAPI spec. Done when api-spec.yaml exists with all endpoints documented.',
    'Audit the test coverage and create missing tests. Done when coverage is above 90%.'
]""", allow_work="True")
# Different solution approaches
branch_self("""[
    'Implement the feature using a class-based approach',
    'Implement the feature using functional programming',
    'Implement the feature using a hybrid approach'
]""", allow_work="False")
```
**Writing Effective Branch Prompts**:
**Required Elements**:
- **Task instruction**: What specific action to take
- **Definition of done**: How to know when complete (specific file/system effects)
**Optional Elements**:
- Tool suggestions
- Context to gather
- Output format requirements
- Success criteria
**Good Examples**:
```python
"Analyze our Q3 sales data, identify top 3 trends, create visualizations. Done when I have charts showing trends with actionable insights."
"Search recent AI safety papers, create summary highlighting key findings. Done when I have 2-page summary with 5+ citations."
```
**Poor Examples**:
```python
"Research AI"  # Too vague, no completion criteria
"Make a chart"  # Missing context about data source
```
### add_tools()
**Purpose**: Add new Python functions as tools to your toolkit.
**When to use**: When you need to extend your capabilities with custom tools.
**Parameters**:
- `filepath` (str): Path to Python file containing tool functions
**Examples**:
```python
# Add custom tools from file
add_tools("my_custom_tools.py")
```
**Tool Requirements**:
- Must be top-level functions (not in classes)
- Must not start with underscore
- Should take string inputs
- Must return strings
- Must handle all errors gracefully
- Need clear docstrings with "Use when..." sections
---
## Best Practices
### Tool Selection Guidelines
1. **File Viewing**: Use `view()` for reading, `view_dir()` for structure
2. **Simple Edits**: Use `patch_edit()` for precise changes
3. **Python Code**: Use `python_edit()` for complex Python modifications
4. **System Operations**: Use `execute_powershell()` for CLI tasks
5. **Code Execution**: Use `_execute_python_code()` for testing code
6. **Task Delegation**: Use `message_bot()` for specialized tasks
7. **Parallel Work**: Use `branch_self()` for multiple approaches
### Error Handling
All tools include comprehensive error handling:
- Invalid parameters return descriptive error messages
- File operations handle encoding issues automatically
- Execution tools include timeout protection
- BOM removal is automatic for text operations
### Performance Considerations
- **Cost Levels**: Tools are marked with cost indicators (low/medium/high/very high)
- **Output Limits**: Most tools have configurable output limits
- **Timeout Settings**: Execution tools include timeout parameters
- **Resource Management**: Sessions are managed automatically
### Security Features
- **Sandboxed Execution**: Python code runs in isolated environments
- **Input Validation**: All parameters are validated before use
- **Error Isolation**: Failures don't affect other operations
- **Encoding Safety**: UTF-8 handling prevents encoding issues
---
## Tool Combinations
### Common Workflows
**Code Review Workflow**:
```python
# 1. Examine structure
view_dir(".", target_extensions="['py']")
# 2. Review specific files
view("main.py")
view("tests/test_main.py")
# 3. Run tests
execute_powershell("python -m pytest tests/ -v")
# 4. Apply fixes
python_edit("main.py::bug_function", "def bug_function(): ...")
```
**Project Setup Workflow**:
```python
# 1. Create project structure
execute_powershell("mkdir -p src tests docs")
# 2. Initialize files
python_edit("src/__init__.py", "# Package initialization")
python_edit("setup.py", "from setuptools import setup...")
# 3. Set up development environment
execute_powershell("python -m venv venv")
execute_powershell("venv/Scripts/activate && pip install -r requirements.txt")
```
**Parallel Development**:
```python
# Use branching for parallel implementation
branch_self("""[
    'Implement user authentication module in auth.py. Done when auth.py exists with login/logout functions.',
    'Create database models in models.py. Done when models.py has User and Session classes.',
    'Build API endpoints in api.py. Done when api.py has all CRUD operations.'
]""", allow_work="True")
```
This comprehensive tool reference should help you effectively use all available tools in the bots library. Each tool is designed to work together seamlessly, enabling complex workflows and sophisticated automation tasks.
