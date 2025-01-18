import os, subprocess, traceback
from typing import List


def execute_powershell(code: str, output_length_limit: str='60'):
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
            # Save full output to file
            output_file = os.path.join(os.getcwd(), 'powershell_full_output.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            truncated_output += (
                f'\n\n{lines_omitted} lines omitted due to length limit. Full output saved to {output_file}')
            return truncated_output

    return output
