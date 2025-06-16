import os, subprocess, traceback, time, threading
from queue import Queue, Empty
from threading import Thread, Lock, local
from typing import Dict, Generator
from datetime import datetime
import base64
import tempfile

from bots.dev.decorators import log_errors, handle_errors

@log_errors
@handle_errors
def execute_powershell(command: str, output_length_limit: str='2500', timeout: str = '60') -> str:
    """
    Executes PowerShell commands in a stateful environment

    Use when you need to run PowerShell commands and capture their output. If
    you have other tools available, you should use this as a fallback when the
    other tools fail. Coerces to utf-8 (no BOM).

    Potential use cases:
    - git commands
    - gh cli
    - other cli (which you may need to install using this tool)

    Parameters:
    - command (str): PowerShell command to execute.
    - output_length_limit (int, optional): Maximum number of lines in the output.
      If set, output exceeding this limit will be truncated. Default 200.

    Returns:
        str: The complete output from the command execution
    """
    manager = PowerShellManager.get_instance()
    output = ''.join(manager.execute(command, int(output_length_limit), float(timeout)))
    return output


class PowerShellSession:
    """
    Manages a persistent PowerShell process for stateful command execution.
    Maintains a single PowerShell process that persists between commands,
    allowing for stateful operations like changing directories, setting
    environment variables, or activating virtual environments.
    """

    def __init__(self, timeout: float = 300):
        self._process = None
        self._command_counter = 0
        self._output_queue = Queue()
        self._error_queue = Queue()
        self._reader_threads = []
        self.startupinfo = None
        if os.name == 'nt':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    def _start_reader_threads(self):
        """Start background threads to read stdout and stderr"""

        def reader_thread(pipe, queue):
            try:
                for line in pipe:
                    queue.put(line.rstrip('\n\r'))
            finally:
                queue.put(None)
        self._reader_threads = [
            Thread(target=reader_thread, args=(self._process.stdout, self._output_queue), daemon=True),
            Thread(target=reader_thread, args=(self._process.stderr, self._error_queue), daemon=True)
        ]
        for thread in self._reader_threads:
            thread.start()

    def __enter__(self):
        if not self._process:
            self._process = subprocess.Popen(
                ['powershell', '-NoProfile', '-NoLogo', '-NonInteractive', '-Command', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=self.startupinfo,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            self._start_reader_threads()
            # Initialize PowerShell session with better encoding and error handling
            init_commands = [
                "$VerbosePreference='SilentlyContinue'",
                "$DebugPreference='SilentlyContinue'",
                "$ProgressPreference='SilentlyContinue'",
                "$WarningPreference='SilentlyContinue'",
                "$ErrorActionPreference='Stop'",
                "function prompt { '' }",
                "$PSDefaultParameterValues['*:Encoding']='utf8'",
                '[Console]::OutputEncoding=[System.Text.Encoding]::UTF8',
                '[Console]::InputEncoding=[System.Text.Encoding]::UTF8',
                '$OutputEncoding=[System.Text.Encoding]::UTF8',
                "$env:PYTHONIOENCODING='utf-8'",
                # Add function to handle complex strings safely
                """
function Invoke-SafeCommand {
    param([string]$Command)
    try {
        Invoke-Expression $Command
        return $true
    } catch {
        Write-Error $_
        return $false
    }
}
                """.strip()
            ]
            for cmd in init_commands:
                self._process.stdin.write(cmd + '\n')
            self._process.stdin.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except:
                self._process.kill()
            finally:
                self._process = None
                self._output_queue = Queue()
                self._error_queue = Queue()
                self._reader_threads = []

    def execute(self, code: str, timeout: float = 60) -> str:
        """
        Execute PowerShell code and return its complete output.

        Args:
            code: The PowerShell code to execute
            timeout: Maximum time in seconds to wait for command completion

        Returns:
            The complete output from the command(s)

        Raises:
            Exception if the process is not running or other execution errors
            TimeoutError if command execution exceeds timeout
        """
        if not self._process:
            raise Exception('PowerShell process is not running')

        try:
            self._command_counter += 1
            delimiter = f'<<<COMMAND_{self._command_counter}_COMPLETE>>>'
            
            # Use a more robust approach for complex code execution
            wrapped_code = self._wrap_code_safely(code, delimiter)
            
            # Clear queues
            while not self._output_queue.empty():
                self._output_queue.get_nowait()
            while not self._error_queue.empty():
                self._error_queue.get_nowait()

            self._process.stdin.write(wrapped_code + '\n')
            self._process.stdin.flush()

            output_lines = []
            error_output = []
            start_time = time.time()
            done = False

            while not done:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f'Command execution timed out after {timeout} seconds')

                if self._process.poll() is not None:
                    raise Exception('PowerShell process unexpectedly closed')

                try:
                    line = self._output_queue.get(timeout=0.1)
                    if line is None:
                        raise Exception('PowerShell process closed stdout')
                    if line == delimiter:
                        done = True
                    else:
                        output_lines.append(line)
                except Empty:
                    pass

                try:
                    while True:
                        line = self._error_queue.get_nowait()
                        if line is None:
                            raise Exception('PowerShell process closed stderr')
                        error_output.append(line)
                except Empty:
                    pass

            all_output = [line for line in output_lines if line.strip()]
            if error_output:
                error_lines = [line for line in error_output if line.strip()]
                if error_lines:
                    all_output.extend(['', 'Errors:', *error_lines])

            # Get current directory for display
            try:
                current_dir = self._get_current_directory()
                dir_info = f"[System: current directory <{current_dir}>]"
                if all_output:
                    all_output.insert(0, dir_info)
                else:
                    all_output = [dir_info]
            except:
                pass  # If we can't get directory, continue without it
            return '\n'.join(all_output)

        except Exception as e:
            self.__exit__(type(e), e, e.__traceback__)
            raise

    def _get_current_directory(self) -> str:
        """Get the current directory from the PowerShell session."""
        if not self._process:
            return "unknown"
        try:
            # Use a simple PowerShell command to get current directory
            temp_counter = self._command_counter + 1000  # Use different counter to avoid conflicts
            delimiter = f'<<<DIR_QUERY_{temp_counter}_COMPLETE>>>'
            # Clear queues first
            while not self._output_queue.empty():
                try:
                    self._output_queue.get_nowait()
                except:
                    break
            # Send directory query
            dir_command = f"(Get-Location).Path; Write-Output '{delimiter}'"
            self._process.stdin.write(dir_command + '\n')
            self._process.stdin.flush()
            # Read response with timeout
            start_time = time.time()
            result_lines = []
            while time.time() - start_time < 2:  # 2 second timeout
                try:
                    line = self._output_queue.get(timeout=0.1)
                    if line == delimiter:
                        break
                    elif line and line.strip():
                        result_lines.append(line.strip())
                except:
                    continue
            # Return the first non-empty line as the directory
            for line in result_lines:
                if line and not line.startswith('PS ') and (':\\' in line or line.startswith('/')):
                    return line
            return "unknown"
        except:
            return "unknown"
    def _wrap_code_safely(self, code: str, delimiter: str) -> str:
        """
        Safely wrap code for execution, handling complex strings and multiline code.
        """
        # Check if this looks like a complex Python command that might have quote issues
        if 'python -c' in code and ('"' in code or "'" in code):
            return self._handle_python_command_safely(code, delimiter)
        else:
            # Use the original wrapping approach for simple commands
            return f"""
            $ErrorActionPreference = 'Stop'
            
            # Execute in main scope
            {code}
            
            # Collect output after execution
            $output = @()
            try {{
                if ($?) {{ 
                    # Add any output from the last command
                    $output += $LASTOUTPUT
                }}
            }} catch {{
                Write-Error $_
            }}
            $output | ForEach-Object {{ $_ }}
            Write-Output '{delimiter}'
            """

    def _get_current_directory(self) -> str:
        """Get the current directory from the PowerShell session."""
        if not self._process:
            return "unknown"
        # Send a quick command to get current directory
        self._process.stdin.write("Get-Location | Select-Object -ExpandProperty Path\n")
        self._process.stdin.flush()
        # Read the response (simplified for this specific case)
        import time
        time.sleep(0.1)  # Brief wait for response
        try:
            # Try to get output from queue
            lines = []
            start_time = time.time()
            while time.time() - start_time < 1:  # 1 second timeout
                try:
                    line = self._output_queue.get(timeout=0.1)
                    if line and not line.startswith("PS ") and line.strip():
                        return line.strip()
                except:
                    continue
        except:
            pass
        return "unknown"
    def _handle_python_command_safely(self, code: str, delimiter: str) -> str:
        """
        Handle Python commands with complex strings by using file-based execution.
        """
        # Extract the Python code part
        if 'python -c "' in code:
            # Find the Python code between quotes
            start_idx = code.find('python -c "') + len('python -c "')
            # Find the closing quote - this is tricky with nested quotes
            quote_count = 0
            end_idx = start_idx
            for i, char in enumerate(code[start_idx:], start_idx):
                if char == '"' and (i == start_idx or code[i-1] != '\\'):
                    quote_count += 1
                    if quote_count == 1:  # Found the closing quote
                        end_idx = i
                        break
            
            if end_idx > start_idx:
                python_code = code[start_idx:end_idx]
                # Clean up the Python code - remove extra escaping
                python_code = python_code.replace('\\"', '"').replace("\\'", "'")
                
                # Create a temporary file approach
                return f"""
                $ErrorActionPreference = 'Stop'
                
                # Create temporary file for Python code
                $tempFile = [System.IO.Path]::GetTempFileName() + '.py'
                $pythonCode = @'
{python_code}
'@
                
                try {{
                    # Write Python code to temp file with UTF-8 encoding
                    [System.IO.File]::WriteAllText($tempFile, $pythonCode, [System.Text.Encoding]::UTF8NoBOM)
                    
                    # Execute Python with the temp file
                    python $tempFile
                }} catch {{
                    Write-Error $_
                }} finally {{
                    # Clean up temp file
                    if (Test-Path $tempFile) {{
                        Remove-Item $tempFile -Force
                    }}
                }}
                
                Write-Output '{delimiter}'
                """
        
        # Fallback to original approach
        return f"""
        $ErrorActionPreference = 'Stop'
        {code}
        Write-Output '{delimiter}'
        """


class PowerShellManager:
    """
    Thread-safe PowerShell session manager that maintains separate sessions.
    Each instance automatically gets its own unique ID and isolated PowerShell session.
    Includes session recovery logic for lost or failed sessions.
    """
    _instances: Dict[str, 'PowerShellManager'] = {}
    _lock = Lock()

    @classmethod
    def get_instance(cls, bot_id: str = None) -> 'PowerShellManager':
        """
        Get or create a PowerShell manager instance for the given bot_id.
        If no bot_id is provided, uses the current thread name.
        
        Args:
            bot_id: Optional identifier for the bot instance
            
        Returns:
            The PowerShell manager instance for this bot/thread
        """
        if bot_id is None:
            bot_id = threading.current_thread().name

        with cls._lock:
            if bot_id not in cls._instances:
                instance = cls.__new__(cls)
                instance.bot_id = bot_id
                instance._thread_local = local()
                instance.created_at = datetime.now()
                cls._instances[bot_id] = instance
            return cls._instances[bot_id]

    def __init__(self):
        """
        Private initializer - use get_instance() instead.
        """
        raise RuntimeError('Use PowerShellManager.get_instance() to create or get a PowerShell manager')

    @property
    def session(self) -> PowerShellSession:
        """
        Get the PowerShell session for the current thread.
        Creates a new session if none exists or if the current session is invalid.
        """
        try:
            if not hasattr(self._thread_local, 'session'):
                print(f'Session not found for {self.bot_id}, starting new session')
                self._start_new_session()
            elif not self._is_session_valid():
                print(f'Invalid session detected for {self.bot_id}, starting new session')
                self.cleanup()
                self._start_new_session()
            return self._thread_local.session
        except Exception as e:
            print(f'Error accessing session: {str(e)}. Starting new session.')
            self._start_new_session()
            return self._thread_local.session

    def _start_new_session(self):
        """
        Starts a new PowerShell session for the current thread.
        """
        self._thread_local.session = PowerShellSession()
        self._thread_local.session.__enter__()

    def _is_session_valid(self) -> bool:
        """
        Checks if the current session is valid and responsive.
        Returns:
            bool: True if session is valid, False otherwise
        """
        try:
            if not hasattr(self._thread_local, 'session'):
                return False
            session = self._thread_local.session
            if not session._process or session._process.poll() is not None:
                return False
            # Use a simple test that's less likely to cause issues
            test_output = session.execute("Write-Output 'test'", timeout=5)
            return 'test' in test_output
        except Exception as e:
            print(f'Session validation failed: {str(e)}')
            return False

    def execute(self, code: str, output_length_limit: str = '60', timeout: float = 60) -> Generator[str, None, None]:
        """
        Execute PowerShell code in the session with automatic recovery.

        Args:
            code: PowerShell code to execute
            output_length_limit: Maximum number of lines in output
            timeout: Maximum time in seconds to wait for command completion

        Yields:
            Command output as strings
        """
        max_retries = 0
        retry_count = 0

        def _process_error(error):
            error_message = f'Tool Failed: {str(error)}\n'
            error_message += f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}"
            return error_message

        while retry_count <= max_retries:
            try:
                processed_code = _process_commands(code)
                output = self.session.execute(processed_code, timeout)
                
                if output_length_limit is not None and output:
                    output_length_limit_int = int(output_length_limit)
                    lines = output.splitlines()
                    if len(lines) > output_length_limit_int:
                        half_limit = output_length_limit_int // 2
                        start_lines = lines[:half_limit]
                        end_lines = lines[-half_limit:]
                        lines_omitted = len(lines) - output_length_limit_int
                        truncated_output = '\n'.join(start_lines)
                        truncated_output += f'\n\n... {lines_omitted} lines omitted ...\n\n'
                        truncated_output += '\n'.join(end_lines)
                        
                        output_file = os.path.join(os.getcwd(), f'ps_output_{self.bot_id}.txt')
                        with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
                            f.write(output)
                        truncated_output += f'\nFull output saved to {output_file}'
                        yield truncated_output
                    else:
                        yield output
                else:
                    yield output
                break

            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    print(f'Command failed, attempt {retry_count} of {max_retries}. Starting new session...')
                    self.cleanup()
                else:
                    yield _process_error(e)

    def cleanup(self):
        """
        Clean up the PowerShell session for the current thread.
        Should be called when work is done or when a session needs to be reset.
        """
        if hasattr(self._thread_local, 'session'):
            try:
                self._thread_local.session.__exit__(None, None, None)
            except Exception as e:
                print(f'Error during session cleanup: {str(e)}')
            finally:
                delattr(self._thread_local, 'session')


def _get_active_sessions() -> list:
    """
    Get information about all active PowerShell sessions.

    Returns:
        List of dictionaries containing session information
    """
    sessions = []
    for thread in threading.enumerate():
        if hasattr(thread, '_thread_local'):
            local_dict = thread._thread_local.__dict__
            if 'ps_manager' in local_dict:
                manager = local_dict['ps_manager']
                sessions.append({
                    'bot_id': manager.bot_id,
                    'thread_name': thread.name,
                    'created_at': manager.created_at.isoformat(),
                    'active': hasattr(manager._thread_local, 'session')
                })
    return sessions


@handle_errors
def _execute_powershell_stateless(code: str, output_length_limit: str = '120'):
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
        error_message += f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}"
        return error_message

    output = ''
    try:
        processed_code = _process_commands(code)
        setup_encoding = '''
        $PSDefaultParameterValues['*:Encoding'] = 'utf8'
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::InputEncoding = [System.Text.Encoding]::UTF8
        $OutputEncoding = [System.Text.Encoding]::UTF8
        $env:PYTHONIOENCODING = "utf-8"
        '''
        wrapped_code = f'{setup_encoding}; {processed_code}'

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', wrapped_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            encoding='utf-8',
            errors='replace'
        )
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
            truncated_output += f'\n\n... {lines_omitted} lines omitted ...\n\n'
            truncated_output += '\n'.join(end_lines)
            
            output_file = os.path.join(os.getcwd(), 'ps_output.txt')
            with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(output)
            truncated_output += f'\nFull output saved to {output_file}'
            return truncated_output

    return output


def _process_commands(code: str) -> str:
    """
    Process PowerShell commands separated by &&, ensuring each command only runs if the previous succeeded.
    Uses PowerShell error handling to catch both command failures and non-existent commands.
    
    Enhanced to better handle complex multiline code blocks.

    Args:
        code (str): The original command string with && separators

    Returns:
        str: PowerShell code with proper error checking between commands
    """
    # Don't process commands that look like multiline code blocks
    if '\n' in code.strip() and '&&' not in code:
        return code
        
    # Split on && but be more careful about it
    commands = []
    current_cmd = ""
    i = 0
    in_quotes = False
    quote_char = None
    
    while i < len(code):
        char = code[i]
        
        if char in ['"', "'"] and (i == 0 or code[i-1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        
        if not in_quotes and i < len(code) - 1 and code[i:i+2] == '&&':
            commands.append(current_cmd.strip())
            current_cmd = ""
            i += 2
            continue
            
        current_cmd += char
        i += 1
    
    if current_cmd.strip():
        commands.append(current_cmd.strip())
    
    if len(commands) <= 1:
        return code

    processed_commands = []
    for cmd in commands:
        wrapped_cmd = f'$ErrorActionPreference = "Stop"; try {{ {cmd}; $LastSuccess = $true }} catch {{ $LastSuccess = $false; $_ }}'
        processed_commands.append(wrapped_cmd)

    return '; '.join([processed_commands[0]] + [f'if ($LastSuccess) {{ {cmd} }}' for cmd in processed_commands[1:]])
