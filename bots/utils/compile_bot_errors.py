import os
import json
import re


def find_tool_results(content):
    """Find all tool result JSON-like structures in the content."""
    pattern = '\\{\\s*"type":\\s*"tool_result"[^}]+\\}'
    matches = re.finditer(pattern, content)
    return [m.group() for m in matches]


def has_error_content(tool_result_str):
    """Check if a tool result contains error-related content."""
    try:
        tool_result = json.loads(tool_result_str)
        content = tool_result.get('content', '').lower()
        error_terms = ['error', 'tool error', 'exception', 'failed']
        return any(term in content.lower() for term in error_terms)
    except json.JSONDecodeError:
        return False


def process_bot_file(file_path):
    """Process a single .bot file and return any error messages found."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tool_results = find_tool_results(content)
        error_messages = []
        for result in tool_results:
            if has_error_content(result):
                try:
                    parsed = json.loads(result)
                    error_messages.append(parsed.get('content', ''))
                except json.JSONDecodeError:
                    continue
        return error_messages
    except Exception as e:
        return [f'Error processing file: {str(e)}']


def main():
    """Process all .bot files in the current directory and save errors to markdown file."""
    bot_files = [f for f in os.listdir('.') if f.endswith('.bot')]
    with open('bot_tool_failures.md', 'w', encoding='utf-8') as outfile:
        outfile.write('# Bot Tool Failures Report\n\n')
        for bot_file in sorted(bot_files):
            outfile.write(f'## {bot_file}\n\n')
            errors = process_bot_file(bot_file)
            if errors:
                for error in errors:
                    outfile.write(f'```\n{error}\n```\n\n')
            else:
                outfile.write('*No errors found*\n\n')
            outfile.write('---\n\n')


if __name__ == '__main__':
    main()
