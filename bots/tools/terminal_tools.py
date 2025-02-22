import os, subprocess, traceback, time, threading
from queue import Queue, Empty
from threading import Thread, Lock, local
from typing import Dict, Generator
from datetime import datetime

def execute_powershell(command: str, output_length_limit: str='120') -> str:
    """
    Executes PowerShell commands in a stateful environment

    Use when you need to run PowerShell commands and capture their output. If
    you have other tools available, you should use this as a fallback when the
    other tools fail. Coerces to utf-8.

    Potential use cases:
    - git commands
    - gh cli
    - other cli (which you may need to install using this tool)

    Parameters:
    - command (str): PowerShell command to execute.
    - output_length_limit (int, optional): Maximum number of lines in the output.
      If set, output exceeding this limit will be truncated. Default 120.

    Returns:
        str: The complete output from the command execution
    """
    manager = PowerShellManager.get_instance()
    output = ''.join(manager.execute(command, output_length_limit))
    return output

class PowerShellSession:
    """
    Manages a persistent PowerShell process for stateful command execution.
    Maintains a single PowerShell process that persists between commands,
    allowing for stateful operations like changing directories, setting
    environment variables, or activating virtual environments.
    """

    def __init__(self):
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
        self._reader_threads = [Thread(target=reader_thread, args=(self._process.stdout, self._output_queue), daemon=True), Thread(target=reader_thread, args=(self._process.stderr, self._error_queue), daemon=True)]
        for thread in self._reader_threads:
            thread.start()

    def __enter__(self):
        if not self._process:
            self._process = subprocess.Popen(['powershell', '-NoProfile', '-NoLogo', '-NonInteractive', '-Command', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=self.startupinfo, encoding='utf-8', errors='replace', bufsize=1)
            self._start_reader_threads()
            init_commands = ["$VerbosePreference='SilentlyContinue'", "$DebugPreference='SilentlyContinue'", "$ProgressPreference='SilentlyContinue'", "$WarningPreference='SilentlyContinue'", "$ErrorActionPreference='Stop'", "function prompt { '' }", "$PSDefaultParameterValues['*:Encoding']='utf8'", '[Console]::OutputEncoding=[System.Text.Encoding]::UTF8', '[Console]::InputEncoding=[System.Text.Encoding]::UTF8', '$OutputEncoding=[System.Text.Encoding]::UTF8', "$env:PYTHONIOENCODING='utf-8'"]
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

    def execute(self, code: str, timeout: float=300) -> str:
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
            wrapped_code = f"\n            $ErrorActionPreference = 'Stop'\n            \n            # Execute in main scope\n            {code}\n            \n            # Collect output after execution\n            $output = @()\n            try {{\n                if ($?) {{ \n                    # Add any output from the last command\n                    $output += $LASTOUTPUT\n                }}\n            }} catch {{\n                Write-Error $_\n            }}\n            $output | ForEach-Object {{ $_ }}\n            Write-Output '{delimiter}'\n            "
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
            return '\n'.join(all_output)
        except Exception as e:
            self.__exit__(type(e), e, e.__traceback__)
            raise

class PowerShellManager:
    """
    Thread-safe PowerShell session manager that maintains separate sessions.
    Each instance automatically gets its own unique ID and isolated PowerShell session.
    Includes session recovery logic for lost or failed sessions.
    """
    _instances: Dict[str, 'PowerShellManager'] = {}
    _lock = Lock()

    @classmethod
    def get_instance(cls, bot_id: str=None) -> 'PowerShellManager':
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
            test_output = session.execute("Write-Output 'test'", timeout=5)
            return 'test' in test_output
        except Exception as e:
            print(f'Session validation failed: {str(e)}')
            return False

    def execute(self, code: str, output_length_limit: str='60') -> Generator[str, None, None]:
        """
        Execute PowerShell code in the session with automatic recovery.

        Args:
            code: PowerShell code to execute
            output_length_limit: Maximum number of lines in output

        Yields:
            Command output as strings
        """
        max_retries = 1
        retry_count = 0

        def _process_error(error):
            error_message = f'Tool Failed: {str(error)}\n'
            error_message += f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}"
            return error_message
        while retry_count <= max_retries:
            try:
                processed_code = _process_commands(code)
                output = self.session.execute(processed_code)
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
                sessions.append({'bot_id': manager.bot_id, 'thread_name': thread.name, 'created_at': manager.created_at.isoformat(), 'active': hasattr(manager._thread_local, 'session')})
    return sessions

def _execute_powershell_stateless(code: str, output_length_limit: str='120'):
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
        setup_encoding = '\n        $PSDefaultParameterValues[\'*:Encoding\'] = \'utf8\'\n        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n        [Console]::InputEncoding = [System.Text.Encoding]::UTF8\n        $OutputEncoding = [System.Text.Encoding]::UTF8\n        $env:PYTHONIOENCODING = "utf-8"\n        '
        wrapped_code = f'{setup_encoding}; {processed_code}'
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(['powershell', '-NoProfile', '-NonInteractive', '-Command', wrapped_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, encoding='utf-8', errors='replace')
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
        wrapped_cmd = f'$ErrorActionPreference = "Stop"; try {{ {cmd}; $LastSuccess = $true }} catch {{ $LastSuccess = $false; $_ }}'
        processed_commands.append(wrapped_cmd)
    return '; '.join([processed_commands[0]] + [f'if ($LastSuccess) {{ {cmd} }}' for cmd in processed_commands[1:]])