import subprocess
import traceback


def execute_powershell(code):
    """
    Executes PowerShell code in a stateless environment

    Use when you need to run PowerShell commands and capture their output.

    Parameters:
    - code (str): PowerShell code to execute.

    Returns command output or an error message.
    """
    output = ''
    try:
        result = subprocess.run(['powershell', '-Command', code],
            capture_output=True, text=True, timeout=300)
        output += result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output += 'Error: Command execution timed out after 30 seconds.'
    except Exception as e:
        output += _process_error(e)
    return output


def _process_error(error):
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message



# Suggestions for advanced tools:
"""
You make an excellent point. Many of the suggestions I provided earlier are indeed within easy reach of typical PowerShell commands. You're right that we should focus on more complex operations that usually require composite or complicated commands. With that in mind, let me suggest some more advanced tools that could be valuable additions:

1. Recursive File Search and Replace:
   A tool that can search for a pattern across multiple files in a directory (and subdirectories) and perform replacements. This often requires a combination of Get-ChildItem, Select-String, and (Get-Content | Set-Content) in PowerShell.

2. Log Parser:
   A tool that can parse complex log files, extract specific information based on patterns or time ranges, and potentially aggregate or summarize the data. This often involves a mix of regex, date parsing, and data aggregation.

3. System Information Gatherer:
   A tool that collects comprehensive system information, including hardware details, installed software, running processes, and network configuration. This typically requires multiple PowerShell commands and potentially WMI queries.

4. Scheduled Task Manager:
   A tool to create, modify, or delete scheduled tasks, which often involves the schtasks command or the ScheduledTasks module in PowerShell, both of which can be complex to use directly.

5. Network Port Scanner:
   A tool to scan for open ports on a local or remote machine, which usually requires a combination of Test-NetConnection commands in a loop.

6. Active Directory Query Tool:
   If applicable to your environment, a tool that simplifies querying and manipulating Active Directory objects, which often involves complex LDAP queries.

7. Registry Editor:
   A tool to safely edit the Windows Registry, including the ability to backup keys before modifying them. This typically involves a series of registry commands and error handling.

8. Service Manager:
   A tool to manage Windows services, including starting, stopping, modifying, and querying their status. While individual operations are simple, a comprehensive tool often requires multiple commands and error handling.

9. Event Log Analyzer:
   A tool to query and analyze Windows Event Logs across multiple log types, potentially correlating events from different sources. This usually involves complex Get-WinEvent queries with XML filters.

10. File Difference and Patch Tool:
    A tool that can not only show differences between files (like the earlier suggestion) but also generate and apply patches. This functionality often requires third-party tools in PowerShell.

11. PowerShell Module Manager:
    A tool to manage PowerShell modules, including installing, updating, and removing modules from various repositories. This could simplify the often multi-step process of module management.

These tools focus more on complex operations that typically require multiple PowerShell commands, careful error handling, or interaction with more advanced Windows features. They could provide significant value by encapsulating complicated logic into simple-to-use functions.
"""
