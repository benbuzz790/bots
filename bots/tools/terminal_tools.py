import subprocess
import traceback


def execute_powershell(code, output_length_limit=60):
    """
    Executes PowerShell code in a stateless environment

    Use when you need to run PowerShell commands and capture their output. If
    you have other tools available, you should use this as a fallback when the
    other tools fail.

    Parameters:
    - code (str): PowerShell code to execute.
    - output_length_limit (int, optional): Maximum number of lines in the output.
      If set, output exceeding this limit will be truncated. Default 60.

    Returns command output or an error message.
    """
    output = ''
    try:
        result = subprocess.run(['powershell', '-Command', code],
            capture_output=True, text=True, timeout=300)
        if result.stderr is not None and result.stdout is not None:
            output += str(result.stdout) + str(result.stderr)
        elif result.stdout is not None:
            output += str(result.stdout)
    except subprocess.TimeoutExpired:
        output += 'Error: Command execution timed out after 30 seconds.'
    except Exception as e:
        output += _process_error(e)

    if output_length_limit is not None:
        lines = output.splitlines()
        if len(lines) > output_length_limit:
            truncated_lines = lines[:output_length_limit]
            lines_omitted = len(lines) - output_length_limit
            truncated_output = '\n'.join(truncated_lines)
            truncated_output += f"\n\n{lines_omitted} lines omitted due to length limit."
            return truncated_output
    return output


def _process_error(error):
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message
