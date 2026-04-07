"""Development decorators for enhancing bot functionality and debugging.

This module provides decorators and utilities for:
- Converting functions to bot tools (@toolify)
- Post-mortem debugging on exceptions (@debug_on_error)
- Error logging to file (@log_errors)
- HTTP logging filters for cleaner output

The primary features are:
- @toolify: Converts functions to bot tools with string-in, string-out interface
- @debug_on_error: Launches pdb debugger on exceptions
- @log_errors: Logs exceptions and error messages to a file
- NoHTTPFilter: Filters out HTTP-related logging noise

Example:
    from bots.dev.decorators import toolify, debug_on_error, log_errors

    @toolify("Add two numbers together")
    def add(x: int, y: int) -> int:
        return x + y

    @debug_on_error
    def risky_operation():
        # Will launch debugger if this raises an exception
        process_data()

    @log_errors
    def might_error():
        # Will log any exceptions or "Error" messages to error_log.txt
        return "Error: Something went wrong"

Note:
    For experimental LLM-powered code generation decorators (@lazy, @lazy_fn, @lazy_class),
    see the separate package: https://github.com/your-org/lazy-impl
    Install with: pip install lazy-impl
"""

import ast
import datetime
import functools
import inspect
import logging
import os
import sys
import traceback
from typing import Any, Callable


class ToolExecutionError(Exception):
    """Custom exception for tool execution failures that should not be treated as user interrupts."""


logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NoHTTPFilter(logging.Filter):
    """Filters out logging records containing 'response' in the logger name.

    Use when you need to reduce noise from HTTP-related logging in the application.
    This filter helps prevent logging output from being flooded with HTTP response
    logs while still maintaining other important log messages.

    Inherits from:
        logging.Filter: Base class for logging filters

    Attributes:
        name (str): The name of the filter (inherited from logging.Filter)

    Example:
        logger = logging.getLogger(__name__)
        http_filter = NoHTTPFilter()
        logger.addFilter(http_filter)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Check if the log record should be filtered.

        Parameters:
            record (logging.LogRecord): The log record to be checked

        Returns:
            bool: True if the record should be kept (doesn't contain 'response'),
                 False if it should be filtered out
        """
        return "response" not in record.name.lower()


logger.addFilter(NoHTTPFilter())


def debug_on_error(func: Callable) -> Callable:
    """Decorator that launches post-mortem debugging on exception.

    Use when you need to automatically start a debugging session when a function
    raises an unhandled exception. This is particularly useful during development
    and troubleshooting.

    Parameters:
        func (Callable): The function to wrap with debugging capabilities

    Returns:
        Callable: A wrapped version of the function that will launch pdb on error

    Example:
        @debug_on_error
        def risky_function():
            # If this raises an exception, pdb will launch
            result = complex_operation()
            return result
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that catches exceptions and launches debugger.

        Parameters:
            *args (Any): Positional arguments to pass to the wrapped function
            **kwargs (Any): Keyword arguments to pass to the wrapped function

        Returns:
            Any: The result of the wrapped function

        Raises:
            Exception: Re-raises the original exception after debugging session ends
        """
        try:
            return func(*args, **kwargs)
        except Exception:
            import pdb

            print(f"\n{'='*80}")
            print(f"Exception in {func.__name__}:")
            print(f"{'='*80}")
            traceback.print_exc()
            print(f"{'='*80}")
            print("Entering post-mortem debugging...")
            print(f"{'='*80}\n")
            pdb.post_mortem()
            raise

    return wrapper


def log_errors(func: Callable) -> Callable:
    """Decorator that logs errors to a file when a function raises an exception or returns an error message.

    This decorator captures both exceptions and return values that contain "Error" in the first few words,
    logging them to 'error_log.txt' in the same directory as this decorators file.

    Parameters:
        func (Callable): The function to wrap with error logging capabilities

    Returns:
        Callable: A wrapped version of the function that logs errors

    Example:
        @log_errors
        def risky_function():
            # Any exceptions or "Error" messages will be logged
            return "Error: Something went wrong"
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = func(*args, **kwargs)
            # Check if result is a string that starts with "Tool Failed:" (the specific format from handle_errors)
            if isinstance(result, str) and result.startswith("Tool Failed:"):
                _log_error_to_file(func.__name__, f"Function returned error message: {result}", args, kwargs)
            return result
        except Exception as e:
            # Log the exception
            error_msg = f"Exception in {func.__name__}: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            _log_error_to_file(func.__name__, error_msg, args, kwargs)
            # Re-raise the exception
            raise

    return wrapper


def toolify(description: str = None, preconditions: list = None, postconditions: list = None):
    """
    Convert any function into a bot tool with string-in, string-out interface.

    - Converts string inputs to proper types using type hints
    - Ensures string output (JSON for complex types)
    - Wraps in error handling (returns error strings, never raises)
    - Enhances docstring if description provided
    - Validates preconditions and postconditions before execution

    Args:
        description (str, optional): Override the function's docstring
        preconditions (list, optional): List of contract functions to check before execution
        postconditions (list, optional): List of contract functions to check before execution
            (despite the name, these run before execution to validate the operation)

    Contract functions should have signature: (*args, **kwargs) -> tuple[bool, str]
    They can also raise exceptions which will be caught and converted to error messages.

    Example:
        @toolify()
        def add_numbers(x: int, y: int = 0) -> int:
            return x + y

        @toolify("Calculate the area of a circle")
        def area(radius: float) -> float:
            return 3.14159 * radius * radius

        def check_positive(x: int, y: int) -> tuple[bool, str]:
            if x > 0 and y > 0:
                return True, ""
            return False, "Both numbers must be positive"

        @toolify(preconditions=[check_positive])
        def add_positive(x: int, y: int) -> int:
            return x + y
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Convert string inputs to proper types using type hints
                converted_args, converted_kwargs = _convert_tool_inputs(func, args, kwargs)

                # Check preconditions
                if preconditions:
                    precondition_errors = []
                    for contract in preconditions:
                        try:
                            is_valid, error_msg = contract(*converted_args, **converted_kwargs)
                            if not is_valid:
                                precondition_errors.append(error_msg)
                        except Exception as e:
                            # Contract raised an exception - treat as validation failure
                            from bots.utils.helpers import _process_error

                            return _process_error(e)

                    if precondition_errors:
                        error_message = "Contract validation failed:\nPreconditions:\n"
                        for error in precondition_errors:
                            error_message += f"  - {error}\n"
                        return error_message.strip()

                # Check postconditions (despite the name, these run before execution)
                if postconditions:
                    postcondition_errors = []
                    for contract in postconditions:
                        try:
                            is_valid, error_msg = contract(*converted_args, **converted_kwargs)
                            if not is_valid:
                                postcondition_errors.append(error_msg)
                        except Exception as e:
                            # Contract raised an exception - treat as validation failure
                            from bots.utils.helpers import _process_error

                            return _process_error(e)

                    if postcondition_errors:
                        error_message = "Contract validation failed:\nPostconditions:\n"
                        for error in postcondition_errors:
                            error_message += f"  - {error}\n"
                        return error_message.strip()

                # Call original function
                result = func(*converted_args, **converted_kwargs)

                # Convert result to string
                return _convert_tool_output(result)

            except KeyboardInterrupt as e:
                # Convert KeyboardInterrupt to ToolExecutionError to prevent it from
                # bubbling up to CLI and being treated as user Ctrl+C
                from bots.utils.helpers import _process_error

                tool_error = ToolExecutionError(f"Tool execution interrupted: {str(e)}")
                return _process_error(tool_error)

            except TypeError as e:
                # Check if this is a missing required argument error
                error_msg = str(e)
                if "missing" in error_msg and "required" in error_msg and "argument" in error_msg:
                    # Add special message for output token limitation
                    enhanced_error = TypeError(
                        f"{error_msg}\n\n"
                        f"⚠️  This error is commonly caused by hitting the max_tokens limit "
                        f"before completing the tool call.\n"
                        f"The response was truncated mid-parameter, making it appear that "
                        f"required parameters are missing.\n"
                        f"To fix this: Work in SMALLER CHUNKS. Edit fewer lines at a time, "
                        f"or break your task into multiple steps."
                    )
                    from bots.utils.helpers import _process_error

                    return _process_error(enhanced_error)
                else:
                    from bots.utils.helpers import _process_error

                    return _process_error(e)

            except Exception as e:
                from bots.utils.helpers import _process_error

                return _process_error(e)

        # Update docstring if description provided
        if description:
            wrapper.__doc__ = description
        elif not wrapper.__doc__:
            # Generate minimal docstring from function name
            wrapper.__doc__ = f"Execute {func.__name__.replace('_', ' ')}"

        return wrapper

    return decorator


def _convert_tool_inputs(func, args, kwargs):
    """Convert string inputs to proper types using function's type hints."""
    import inspect

    sig = inspect.signature(func)

    converted_args = []
    converted_kwargs = {}

    # Convert positional args
    param_names = list(sig.parameters.keys())
    for i, arg in enumerate(args):
        if i < len(param_names):
            param_name = param_names[i]
            param = sig.parameters[param_name]
            converted_value = _convert_string_to_type(arg, param.annotation)
            converted_args.append(converted_value)
        else:
            # No type hint available, keep as string
            converted_args.append(arg)

    # Convert keyword args
    for key, value in kwargs.items():
        if key in sig.parameters:
            param = sig.parameters[key]
            converted_value = _convert_string_to_type(value, param.annotation)
            converted_kwargs[key] = converted_value
        else:
            # No type hint available, keep as string
            converted_kwargs[key] = value

    return tuple(converted_args), converted_kwargs


def _convert_string_to_type(value, type_hint):
    """Convert a string value to the specified type."""

    # Handle None values - don't convert None to string "None"
    if value is None:
        return None

    # If no type hint, return as string
    if type_hint == inspect.Parameter.empty:
        return value

    # If already the right type, return as-is
    if isinstance(value, type_hint):
        return value

    # Convert string to target type
    if type_hint == str:
        return str(value)
    elif type_hint == int:
        return int(value)
    elif type_hint == float:
        return float(value)
    elif type_hint == bool:
        # Handle common boolean string representations
        if isinstance(value, str):
            lower_val = value.lower()
            if lower_val in ("true", "1", "yes", "on"):
                return True
            elif lower_val in ("false", "0", "no", "off"):
                return False
        return bool(value)
    elif type_hint == list:
        # Parse string as Python list literal
        if isinstance(value, str):
            return ast.literal_eval(value)
        return list(value)
    elif type_hint == dict:
        # Parse string as Python dict literal
        if isinstance(value, str):
            return ast.literal_eval(value)
        return dict(value)
    else:
        # For other types, try direct conversion or return as string
        try:
            return type_hint(value)
        except (ValueError, TypeError):
            return value


def _convert_tool_output(result):
    """Convert function result to string output with automatic truncation for long outputs.
    Truncates outputs exceeding 20000 characters to prevent context overload.
    Preserves first and last 8000 characters with a clear truncation notice in the middle.
    Args:
        result: The function result to convert to string
    Returns:
        str: String representation of result, possibly truncated
    """
    import json

    # Convert result to string first
    if result is None:
        output = "Tool execution completed without errors"
    elif isinstance(result, str):
        output = result
    elif isinstance(result, (int, float, bool)):
        output = str(result)
    elif isinstance(result, (list, dict)):
        # JSON serialize complex types
        try:
            output = json.dumps(result, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            # Fallback to string representation
            output = str(result)
    else:
        # For other types, use string representation
        output = str(result)
    # Apply truncation if output exceeds threshold
    threshold = 20000
    preserve = 8000
    if len(output) > threshold:
        truncation_message = "\n\n... (tool result truncated from middle to save you from context overload) ...\n\n"
        truncated_output = output[:preserve] + truncation_message + output[-preserve:]
        return truncated_output
    return output


def _log_error_to_file(function_name: str, error_message: str, args: tuple = None, kwargs: dict = None) -> None:
    """Helper function to log errors to the error log file.

    Parameters:
        function_name (str): Name of the function that had the error
        error_message (str): The error message to log
        args (tuple, optional): Positional arguments passed to the function
        kwargs (dict, optional): Keyword arguments passed to the function
    """
    # Get the directory where this decorators file is located
    decorators_dir = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(decorators_dir, "error_log.txt")

    # Create timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    args_parts = []
    if args:
        args_parts.append(f"args={args}")
    if kwargs:
        args_parts.append(f"kwargs={kwargs}")
    if args_parts:
        args_str = f"\nArguments: {', '.join(args_parts)}"
    else:
        args_str = ""

    # Format the log entry
    log_entry = f"[{timestamp}] Function: {function_name}{args_str}\n{error_message}\n{'-' * 80}\n\n"

    # Append to the log file
    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
    except Exception as e:
        # If we can't write to the log file, at least print to stderr
        print(f"Failed to write to error log: {e}", file=sys.stderr)
        print(f"Original error: {log_entry}", file=sys.stderr)
