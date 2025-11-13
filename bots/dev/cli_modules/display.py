"""
Display and formatting utilities for CLI output.
This module contains functions for formatting and displaying bot responses,
tool calls, metrics, and other CLI output.
"""

import json
import re
import textwrap
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bots.dev.cli_modules.config import CLIContext
    from bots.foundation.base import Bot
from bots.dev.cli_modules.utils import (
    COLOR_BOLD,
    COLOR_METRICS,
    COLOR_RESET,
)


def format_tool_data(data: dict, indent: int = 4, color: str = COLOR_RESET) -> str:
    """
    Format tool arguments or results in a clean, minimal way.
    No JSON braces, no quotes around keys, just key: value pairs.
    Keys are bolded for emphasis.
    Special case: If there's only one key-value pair, just return the value
    without the key name (assumes it's the primary/required input).
    """
    if not data:
        return "(empty)"
    # Special case: single input - just show the value without the key
    if len(data) == 1:
        key, value = next(iter(data.items()))
        if isinstance(value, str):
            return "\n" + value
        elif isinstance(value, dict):
            return "\n" + format_tool_data(value, indent, color)
        else:
            return "\n" + str(value)
    # Multiple inputs - show key: value pairs
    lines = []
    for key, value in data.items():
        # Strip underscores from parameter names for cleaner display
        display_key = key.replace("_", " ")
        # Bold the key name with color, keep colon and value colored too
        bold_key = f"{color}{COLOR_BOLD}{display_key}{COLOR_RESET}{color}:"
        if isinstance(value, dict):
            # Nested dict - format recursively with extra indent
            nested = format_tool_data(value, indent, color)
            lines.append(bold_key)
            for nested_line in nested.split("\n"):
                if nested_line:  # Skip empty lines
                    lines.append(" " * indent + nested_line)
        elif isinstance(value, str):
            # String value - handle multiline strings
            if "\n" in value:
                lines.append(bold_key)
                for line in value.split("\n"):
                    lines.append(" " * indent + line)
            else:
                lines.append(f"{bold_key} {value}")
        elif isinstance(value, (list, tuple)):
            # List/tuple - format as compact representation
            lines.append(f"{bold_key} {value}")
        else:
            # Other types (int, bool, None, etc.)
            lines.append(f"{bold_key} {value}")
    # Return the formatted lines joined with newlines
    return "\n" + "\n".join(lines)


def clean_dict(d: dict, indent: int = 4, level: int = 1):
    """
    Clean a dict containing recursive json dumped strings for printing
    Returns: clean string representation of the dict
    """
    for k, v in d.items():
        if isinstance(v, dict):
            clean_dict(v, indent, level + 1)
        if isinstance(v, str) and "\n" in v:
            lines = v.splitlines()
            for i, line in enumerate(lines):
                line = " " * indent * (level + 1) + line
                if i == 0:
                    line = "\n" + line
                lines[i] = line
            d[k] = "\n".join(lines)
    cleaned_dict = json.dumps(d, indent=indent * level)
    cleaned_dict = re.sub(r"(?<!\\)\\n", "\n", cleaned_dict)
    cleaned_dict = cleaned_dict.replace('\\"', '"')
    cleaned_dict = cleaned_dict.replace("\\\\", "\\")
    return cleaned_dict


def display_metrics(context: "CLIContext", bot: "Bot"):
    """Display API metrics if verbose mode is on."""
    if not context.config.verbose:
        return

    try:
        from bots.observability import metrics

        # Use cached metrics from context if available, otherwise get fresh
        if context.last_message_metrics is not None:
            last_metrics = context.last_message_metrics
        else:
            last_metrics = metrics.get_and_clear_last_metrics()

        # Check if there are any metrics to display
        if last_metrics["input_tokens"] == 0 and last_metrics["output_tokens"] == 0:
            return

        # Calculate total tokens for this call
        total_tokens = last_metrics["input_tokens"] + last_metrics["output_tokens"]

        # Format the metrics in a single line: [tokens] | $[cost] | [time]s
        metrics_str = f"{total_tokens:,} | ${last_metrics['cost']:.4f} | " f"{last_metrics['duration']:.2f}s"

        # Add session totals on second line
        try:
            session_tokens = metrics.get_total_tokens(context.session_start_time)
            session_cost = metrics.get_total_cost(context.session_start_time)

            metrics_str += f"\n{session_tokens['total']:,} | ${session_cost:.4f}"
        except Exception:
            # If session totals fail, just show the per-call metrics
            pass

        pretty(
            metrics_str,
            "metrics",
            context.config.width,
            context.config.indent,
            COLOR_METRICS,
            newline_after_name=True,
        )
    except Exception:
        pass


def pretty(
    string: str,
    name: Optional[str] = None,
    width: int = 1400,
    indent: int = 4,
    color: str = COLOR_RESET,
    newline_after_name: bool = True,
) -> None:
    """Print a string nicely formatted with explicit color."""
    print()
    if name is not None:
        if newline_after_name:
            prefix = f"{color}{COLOR_BOLD}{name}:{COLOR_RESET}\n" f"{' ' * indent}{color}"
        else:
            prefix = f"{color}{COLOR_BOLD}{name}: {COLOR_RESET}{color}"
    else:
        prefix = color
    if not isinstance(string, str):
        string = str(string)
    # Safeguard: if string is too long, truncate it to prevent hangs
    max_length = 50000  # Reasonable limit for display
    if len(string) > max_length:
        string = string[:max_length] + "\n... (output truncated)"
    # Quick path for very simple strings - avoid regex overhead
    if len(string) < 1000 and "\n" not in string:
        print(prefix + string + COLOR_RESET)
        print()
        return

    lines = string.split("\n")
    formatted_lines = []

    # Limit number of lines to prevent excessive processing
    max_lines = 1000
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("... (output truncated)")

    for i, line in enumerate(lines):
        # Additional safeguard: skip wrapping for very long lines
        if len(line) > 10000:
            if i == 0:
                formatted_lines.append(prefix + line[:10000] + "... (line truncated)" + COLOR_RESET)
            else:
                formatted_lines.append(" " * indent + color + line[:10000] + "... (line truncated)" + COLOR_RESET)
            continue

        if i == 0:
            initial_line = prefix + line + COLOR_RESET
            try:
                wrapped = textwrap.wrap(
                    initial_line,
                    width=width,
                    subsequent_indent=" " * indent,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
            except Exception:
                # Fallback if textwrap fails
                wrapped = [initial_line]
        else:
            try:
                wrapped = textwrap.wrap(
                    color + line + COLOR_RESET,
                    width=width,
                    initial_indent=" " * indent,
                    subsequent_indent=" " * indent,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
            except Exception:
                # Fallback if textwrap fails
                wrapped = [" " * indent + color + line + COLOR_RESET]
        if wrapped:
            formatted_lines.extend(wrapped)
        else:
            formatted_lines.append(" " * indent if i > 0 else prefix + COLOR_RESET)
    for line in formatted_lines:
        print(line)
    print()
