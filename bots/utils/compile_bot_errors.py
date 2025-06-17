"""Utility module for analyzing bot conversation files and compiling tool
execution errors.
This module provides functionality to scan .bot files for tool execution errors
and generate a markdown report. It helps identify and track tool failures
across multiple bot conversation files.
Use when you need to:
- Analyze bot conversation files for tool errors
- Generate error reports from bot files
- Monitor tool execution failures across multiple conversations
"""

import json
import os
import re


def find_tool_results(content: str) -> list[str]:
    """Find all tool result JSON-like structures in the content.
    Use when you need to extract tool result structures from bot conversation
    logs. Searches for JSON objects that contain a "type": "tool_result" field
    and extracts the complete JSON structure.
    Parameters:
    - content (str): The string content to search for tool results
    Returns:
    list[str]: List of JSON strings containing tool result structures. Each
              structure will be a complete JSON object containing at minimum
              a "type" field.
    """
    pattern = '\\{\\s*"type":\\s*"tool_result"[^}]+\\}'
    matches = re.finditer(pattern, content)
    return [m.group() for m in matches]


def has_error_content(tool_result_str: str) -> bool:
    """Check if a tool result contains error-related content.
    Use when you need to determine if a tool result JSON string contains error
    indicators. Searches the 'content' field of the JSON structure for common
    error terms like 'error', 'tool error', 'exception', and 'failed'.
    Parameters:
    - tool_result_str (str): JSON string containing a tool result. Expected to
                            have a 'content' field with the tool's output
                            message.
    Returns:
    bool: True if error-related content is found in the tool result's content,
          False if no error terms are found or if the JSON cannot be parsed
    """
    try:
        tool_result = json.loads(tool_result_str)
        content = tool_result.get("content", "").lower()
        error_terms = ["error", "tool error", "exception", "failed"]
        return any(term in content.lower() for term in error_terms)
    except json.JSONDecodeError:
        return False


def process_bot_file(file_path: str) -> list[str]:
    """Process a single .bot file and extract error messages from tool results.
    Use when you need to analyze a bot conversation file for tool execution
    errors. Reads a .bot file containing serialized bot conversation data,
    extracts all tool result structures, and identifies those containing error
    messages.
    Parameters:
    - file_path (str): Path to the .bot file to process. File should contain
                      serialized bot conversation data with tool result
                      structures.
    Returns:
    list[str]: List of error messages found in the file. Each entry is the
               content of a tool result that contains error indicators. If file
               processing fails (e.g., file not found, permission error),
               returns a list containing a single error description string.
    Example return value:
    ['Error: File not found: test.py',
     'Error: Permission denied: /root/file.txt']
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tool_results = find_tool_results(content)
        error_messages = []
        for result in tool_results:
            if has_error_content(result):
                try:
                    parsed = json.loads(result)
                    error_messages.append(parsed.get("content", ""))
                except json.JSONDecodeError:
                    continue
        return error_messages
    except Exception as e:
        return [f"Error processing file: {str(e)}"]


def main() -> None:
    """Process all .bot files in the current directory and generate an error
    report.
    Use when you need to compile a markdown report of all tool failures across
    multiple bot files. Scans the current working directory for .bot files,
    processes each one for tool errors, and generates a formatted markdown
    report file.
    The generated report (bot_tool_failures.md) follows this format:
    ```markdown
    # Bot Tool Failures Report
    ## botfile1.bot
    ```error message 1```
    ```error message 2```
    ## botfile2.bot
    *No errors found*
    ---
    ```
    Returns:
    None: Writes results directly to 'bot_tool_failures.md' in the current
          directory. Will overwrite existing file if present.
    Note:
    - Files are processed in alphabetical order
    - Each file section is separated by horizontal rules
    - Errors are wrapped in markdown code blocks
    """
    bot_files = [f for f in os.listdir(".") if f.endswith(".bot")]
    with open("bot_tool_failures.md", "w", encoding="utf-8") as outfile:
        outfile.write("# Bot Tool Failures Report\n\n")
        for bot_file in sorted(bot_files):
            outfile.write(f"## {bot_file}\n\n")
            errors = process_bot_file(bot_file)
            if errors:
                for error in errors:
                    outfile.write(f"```\n{error}\n```\n\n")
            else:
                outfile.write("*No errors found*\n\n")
            outfile.write("---\n\n")


if __name__ == "__main__":
    main()
