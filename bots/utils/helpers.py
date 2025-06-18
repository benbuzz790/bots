"""Utility functions for error handling, file operations, and text processing.
This module provides helper functions for common operations including:
- Error formatting and traceback handling
- File system operations and timestamp-based file filtering
- Code block extraction from markdown text
- AST manipulation and code cleaning
- Datetime formatting for filenames
"""

import ast
import datetime as DT
import os
import re
import textwrap
import traceback
from typing import List, Tuple


def _process_error(error: Exception) -> str:
    """Format an exception into a detailed error message string.
    Internal helper function for consistent error message formatting.
    Combines the error message with a full traceback for debugging.
    Used by tool functions to provide detailed error information
    without raising exceptions.
    Parameters:
        error (Exception): The exception to process. Can be any exception type.
    Returns:
        str: Formatted error message including:
            - Error type and message
            - Full traceback with line numbers and context
    """
    error_message = f"Tool Failed: {str(error)}\n"
    traceback_str = "".join(traceback.format_tb(error.__traceback__))
    error_message += f"Traceback:\n{traceback_str}"
    return error_message


def _get_new_files(start_time: float, dir=".", extension=None) -> List[str]:
    """Get all files created after a specified timestamp in a directory tree.
    Internal helper function for finding newly created files.
    Performs a recursive search through the directory tree and its
    subdirectories.
    Parameters:
        start_time (float): Unix timestamp to filter files created after
        dir (str, optional): Root directory to start search from.
            Defaults to current directory
        ext (str, optional): File extension to filter by including the
            dot (e.g. '.py', '.txt'). If None, returns files with any
            extension. Defaults to None
    Returns:
        List[str]: List of absolute file paths for files created after
            start_time. Paths are returned in the order they are discovered
            during directory traversal.
    """
    new_files = []
    for root, _, files in os.walk(dir):
        for file in files:
            path = os.path.join(root, file)
            if os.path.getctime(path) >= start_time:
                if extension is None or os.path.splitext(path)[1] == extension:
                    new_files.append(path)
    return new_files


def _clean(code: str) -> str:
    """Clean and dedent code before parsing by removing common leading
    whitespace.
    Internal helper function for code formatting. Removes any common leading
    whitespace (spaces or tabs) from every line in the text while preserving
    relative indentation. Also strips leading/trailing whitespace from the
    entire string.
    Parameters:
        code (str): The code string to clean. Can be single or multiple lines.
    Returns:
        str: The cleaned and dedented code with consistent indentation
    Example:
        >>> code = '''
        ...     def example():
        ...         print("hello")
        ... '''
        >>> _clean(code)
        'def example():\n    print("hello")'
    """
    return textwrap.dedent(code).strip()


def _py_ast_to_source(node: ast.AST) -> str:
    """Convert a Python AST node back to valid Python source code.
    Internal helper function for AST manipulation. Uses ast.unparse() to
    convert AST nodes back to source code. Works with any valid Python AST
    node type (Module, FunctionDef, ClassDef, etc.).
    Parameters:
        node (ast.AST): The AST node to convert. Must be a valid node from
            the ast module. Common types include: ast.Module, ast.FunctionDef,
            ast.ClassDef, ast.Expr
    Returns:
        str: The source code representation of the AST node. The output will
            be valid Python code that could be executed or compiled.
    Note:
        Requires Python 3.9+ for ast.unparse(). Comments and formatting from
        the original source code are not preserved in the output.
    """
    return ast.unparse(node)


def remove_code_blocks(text: str) -> Tuple[List[str], List[str]]:
    """Extract code blocks and language labels from markdown-formatted text.
    Use when you need to parse markdown text containing fenced code blocks
    (```language code```) and separate the code blocks from the rest of the
    text. Handles multiple code blocks and preserves their order. The function
    matches code blocks using a regex pattern that supports optional language
    labels and handles both single and multi-line code blocks.
    Parameters:
        text (str): Markdown-formatted text containing code blocks. Code blocks
            must be fenced with triple backticks (```). Language label after
            opening fence is optional.
    Returns:
        Tuple[List[str], List[str]]: A tuple containing:
            - List[str]: Extracted code blocks with whitespace trimmed, in
              order of appearance
            - List[str]: Language labels (empty string if no label specified)
            The lists will have matching lengths, with each index corresponding
            to the same code block.
    Example:
        >>> text = '''
        ... Here's some Python code:
        ... ```python
        ... def hello():
        ...     print('hello')
        ... ```
        ... And some unlabeled code:
        ... ```
        ... console.log('hi');
        ... ```
        ... '''
        >>> code_blocks, labels = remove_code_blocks(text)
        >>> code_blocks  # ["def hello():\n    print('hello')",
        ...              #  "console.log('hi');"]
        >>> labels      # ["python", ""]
    """
    pattern = "```(\\w*)\\s*([\\s\\S]*?)```"
    matches = re.findall(pattern, text)
    code_blocks = [match[1].strip() for match in matches]
    labels = [match[0].strip() for match in matches]
    text = re.sub(pattern, "", text)
    return code_blocks, labels


def formatted_datetime() -> str:
    """Get current datetime formatted as a string suitable for filenames.
    Use when you need a timestamp string that is safe to use in file paths
    across different operating systems. The format uses only characters that
    are valid in filenames on Windows, macOS, and Linux.
    Format components:
        YYYY: Four-digit year
        MM: Two-digit month (01-12)
        DD: Two-digit day (01-31)
        HH: Two-digit hour in 24-hour format (00-23)
        MM: Two-digit minute (00-59)
        SS: Two-digit second (00-59)
    Returns:
        str: Current local datetime formatted as 'YYYY-MM-DD_HH-MM-SS'.
            Uses system's local timezone. Time components are separated
            by hyphens, date and time are separated by underscore.
    Example:
        >>> formatted_datetime()
        '2023-12-25_14-30-45'  # December 25th, 2023, 2:30:45 PM local time
    Note:
        Uses local system time. For timezone-aware timestamps, consider using
        datetime.datetime.now(timezone.utc) instead.
    """
    now = DT.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")
