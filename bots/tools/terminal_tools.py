import os, subprocess, traceback
from typing import List
"""Deb: Ah, now I understand! There's a Unicode decoding error in PowerShell when trying to handle certain bytes (0xb0) in pytest's output. This is why we're not seeing any output - it's failing silently due to the encoding error."""
"""Need to appropriately handle && notation"""


def execute_powershell(code: str, output_length_limit: str='60'):
    """
    Executes PowerShell code in a stateless environment

    Use when you need to run PowerShell commands and capture their output. If
    you have other tools available, you should use this as a fallback when the
    other tools fail. Coerces to utf-8 encoding.

    Potential use cases:
    - git commands
    - gh cli
    - other cli (which you may need to install using this tool)

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
        processed_code = _process_commands(code)
        setup_encoding = """
        $PSDefaultParameterValues['*:Encoding'] = 'utf8'
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::InputEncoding = [System.Text.Encoding]::UTF8
        $OutputEncoding = [System.Text.Encoding]::UTF8
        $env:PYTHONIOENCODING = "utf-8"
        """
        wrapped_code = f'{setup_encoding}; {processed_code}'
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(['powershell', '-NoProfile',
            '-NonInteractive', '-Command', wrapped_code], stdout=subprocess
            .PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo,
            encoding='utf-8', errors='replace')
        stdout, stderr = process.communicate(timeout=300)
        output = stdout
        if stderr:
            output += stderr
    except subprocess.TimeoutExpired as e:
        process.kill()
        output += 'Error: Command execution timed out after 300 seconds.'
    except Exception as e:
        output += _process_error(e)
    if output_length_limit is not None and output:
        output_length_limit = int(output_length_limit)
        lines = output.splitlines()
        if len(lines) > output_length_limit:
            half_limit = output_length_limit // 2
            start_lines = lines[:half_limit]
            end_lines = lines[-half_limit:]
            lines_omitted = len(lines) - output_length_limit
            truncated_output = '\n'.join(start_lines)
            truncated_output += (
                f'\n\n... {lines_omitted} lines omitted ...\n\n')
            truncated_output += '\n'.join(end_lines)
            output_file = os.path.join(os.getcwd(), 'ps_output.txt')
            with open(output_file, 'w', encoding='utf-8', errors='replace'
                ) as f:
                f.write(output)
            truncated_output += f'\nFull output saved to {output_file}'
            return truncated_output
    return output


def _process_commands(code: str) ->str:
    """
    Process PowerShell commands separated by &&, ensuring each command only runs if the previous succeeded.
    Uses PowerShell error handling to catch both command failures and non-existent commands.

    Args:
        code (str): The original command string with && separators

    Returns:
        str: PowerShell code with proper error checking between commands
    """
    commands = code.split(' && ')
    if len(commands) == 1:
        return code
    processed_commands = []
    for cmd in commands:
        wrapped_cmd = (
            f'$ErrorActionPreference = "Stop"; try {{ {cmd}; $LastSuccess = $true }} catch {{ $LastSuccess = $false; $_ }}'
            )
        processed_commands.append(wrapped_cmd)
    return '; '.join([processed_commands[0]] + [
        f'if ($LastSuccess) {{ {cmd} }}' for cmd in processed_commands[1:]])
