import os, subprocess, traceback
from typing import List


# TODO
# def get_file_metadata(file_path: str) ->dict:
#     """
#     Get metadata about a file including size, modification time, etc.

#     Parameters:
#     - file_path (str): Path to the file to analyze

#     Returns:
#     A dictionary containing:
#     - size: File size in bytes
#     - modified: Last modification time as a string
#     - created: Creation time as a string
#     - exists: Whether the file exists
#     """
#     try:
#         if not os.path.exists(file_path):
#             return {'exists': False, 'error':
#                 f'File {file_path} does not exist'}
#         stats = os.stat(file_path)
#         return {'exists': True, 'size': stats.st_size, 'modified': DT.
#             datetime.fromtimestamp(stats.st_mtime).strftime(
#             '%Y-%m-%d %H:%M:%S'), 'created': DT.datetime.fromtimestamp(
#             stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}
#     except Exception as e:
#         return _process_error(e)


def execute_powershell(code: str, output_length_limit: str = '60'):
    """
    Executes PowerShell code in a stateless environment

    Use when you need to run PowerShell commands and capture their output. If
    you have other tools available, you should use this as a fallback when the
    other tools fail. Coerces to utf-8 encoding.

    Parameters:
    - code (str): PowerShell code to execute.
    - output_length_limit (int, optional): Maximum number of lines in the output.
      If set, output exceeding this limit will be truncated. Default 60.

    Returns command output or an error message.
    """

    def _process_error(error):
        error_message = f'Tool Failed: {str(error)}\n'
        error_message += (
            f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
        return error_message

    output = ''
    try:
        # Wrap code to ensure proper utf-8 encoding
        wrapped_code = f'chcp 65001 > $null; {code}'
        
        result = subprocess.run(
            ['powershell', '-Command', wrapped_code],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300
        )
        
        output = result.stdout
        if result.stderr:
            output += result.stderr

    except subprocess.TimeoutExpired:
        output += 'Error: Command execution timed out after 300 seconds.'
    except Exception as e:
        output += _process_error(e)

    # Handle output length limiting
    if output_length_limit is not None and output:
        output_length_limit = int(output_length_limit)
        lines = output.splitlines()
        if len(lines) > output_length_limit:
            truncated_lines = lines[:output_length_limit]
            lines_omitted = len(lines) - output_length_limit
            truncated_output = '\n'.join(truncated_lines)
            truncated_output += (
                f'\n\n{lines_omitted} lines omitted due to length limit.')
            return truncated_output

    return output