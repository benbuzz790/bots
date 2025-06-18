import codecs
import glob
import os
import subprocess
import threading
import time
import traceback
from datetime import datetime
from queue import Empty, Queue
from threading import Lock, Thread, local
from typing import Dict, Generator, List

from bots.dev.decorators import handle_errors, log_errors


class BOMRemover:
    """
    Utility class for removing BOMs from files automatically.
    Integrated into PowerShell execution pipeline.
    """

    # File extensions that commonly contain BOMs and should be processed
    TEXT_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".md",
        ".txt",
        ".csv",
        ".sql",
        ".sh",
        ".ps1",
        ".bat",
        ".cmd",
        ".ini",
        ".cfg",
        ".conf",
        ".log",
        ".gitignore",
        ".gitattributes",
        ".dockerignore",
        ".editorconfig",
        ".env",
        ".properties",
        ".toml",
        ".lock",
    }

    # Directories to skip (common hidden/system directories)
    SKIP_DIRS = {
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        "node_modules",
        ".vscode",
        ".idea",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "env",
    }

    @staticmethod
    def should_process_file(file_path: str) -> bool:
        """
        Determine if a file should be processed for BOM removal.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if file should be processed
        """
        # Skip if file doesn't exist
        if not os.path.isfile(file_path):
            return False

        # Skip hidden files
        if os.path.basename(file_path).startswith("."):
            return False

        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        return ext in BOMRemover.TEXT_EXTENSIONS

    @staticmethod
    def remove_bom_from_file(file_path: str) -> bool:
        """
        Remove BOM from a single file if present.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if BOM was removed, False otherwise
        """
        try:
            if not BOMRemover.should_process_file(file_path):
                return False

            with open(file_path, "rb") as file:
                content = file.read()

            if content.startswith(codecs.BOM_UTF8):
                with open(file_path, "wb") as file:
                    file.write(content[len(codecs.BOM_UTF8) :])
                print(f"[BOM] Removed BOM from: {file_path}")
                return True

        except Exception as e:
            print(f"[BOM] Error processing {file_path}: {str(e)}")

        return False

    @staticmethod
    def remove_bom_from_directory(directory: str, recursive: bool = True) -> int:
        """
        Remove BOMs from all eligible files in a directory.

        Args:
            directory: Directory path to process
            recursive: Whether to process subdirectories

        Returns:
            int: Number of files with BOMs removed
        """
        if not os.path.isdir(directory):
            return 0

        bom_count = 0

        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    # Filter out directories to skip
                    dirs[:] = [d for d in dirs if d not in BOMRemover.SKIP_DIRS]

                    for file in files:
                        file_path = os.path.join(root, file)
                        if BOMRemover.remove_bom_from_file(file_path):
                            bom_count += 1
            else:
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if BOMRemover.remove_bom_from_file(file_path):
                        bom_count += 1

        except Exception as e:
            print(f"[BOM] Error processing directory {directory}: {str(e)}")

        return bom_count

    @staticmethod
    def remove_bom_from_pattern(pattern: str) -> int:
        """
        Remove BOMs from files matching a glob pattern.

        Args:
            pattern: Glob pattern to match files

        Returns:
            int: Number of files with BOMs removed
        """
        bom_count = 0

        try:
            for file_path in glob.glob(pattern, recursive=True):
                if BOMRemover.remove_bom_from_file(file_path):
                    bom_count += 1
        except Exception as e:
            print(f"[BOM] Error processing pattern {pattern}: {str(e)}")

        return bom_count


@log_errors
@handle_errors
def execute_powershell(command: str, output_length_limit: str = "2500", timeout: str = "60") -> str:
    """
    Executes PowerShell commands in a stateful environment with automatic BOM removal

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
    output = "".join(manager.execute(command, int(output_length_limit), float(timeout)))
    return output


class PowerShellSession:
    """
    Manages a persistent PowerShell process for stateful command execution.
    Maintains a single PowerShell process that persists between commands,
    allowing for stateful operations like changing directories, setting
    environment variables, or activating virtual environments.

    Now includes automatic BOM removal after file operations.
    """

    def __init__(self, timeout: float = 300):
        self._process = None
        self._command_counter = 0
        self._output_queue = Queue()
        self._error_queue = Queue()
        self._reader_threads = []
        self._current_directory = os.getcwd()
        self._bom_remover = BOMRemover()
        self.startupinfo = None
        if os.name == "nt":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    def _start_reader_threads(self):
        """Start background threads to read stdout and stderr"""

        def reader_thread(pipe, queue):
            try:
                for line in pipe:
                    queue.put(line.rstrip("\n\r"))
            finally:
                queue.put(None)

        self._reader_threads = [
            Thread(
                target=reader_thread,
                args=(self._process.stdout, self._output_queue),
                daemon=True,
            ),
            Thread(
                target=reader_thread,
                args=(self._process.stderr, self._error_queue),
                daemon=True,
            ),
        ]
        for thread in self._reader_threads:
            thread.start()

    def __enter__(self):
        if not self._process:
            self._process = subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-NoLogo",
                    "-NonInteractive",
                    "-Command",
                    "-",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=self.startupinfo,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            self._start_reader_threads()
            # Initialize PowerShell session with better encoding and error
            # handling
            init_commands = [
                "$VerbosePreference='SilentlyContinue'",
                "$DebugPreference='SilentlyContinue'",
                "$ProgressPreference='SilentlyContinue'",
                "$WarningPreference='SilentlyContinue'",
                "$ErrorActionPreference='Stop'",
                "function prompt { '' }",
                "$PSDefaultParameterValues['*:Encoding']='utf8NoBOM'",
                "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8",
                "[Console]::InputEncoding=[System.Text.Encoding]::UTF8",
                "$OutputEncoding=[System.Text.Encoding]::UTF8",
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
                """.strip(),
            ]
            for cmd in init_commands:
                self._process.stdin.write(cmd + "\n")
            self._process.stdin.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            finally:
                self._process = None
                self._output_queue = Queue()
                self._error_queue = Queue()
                self._reader_threads = []

    def _detect_file_operations(self, code: str) -> List[str]:
        """
        Detect file operations in PowerShell code that might create files with BOMs.

        Args:
            code: PowerShell code to analyze

        Returns:
            List of detected file operations/patterns
        """
        file_operations = []

        # Common PowerShell cmdlets that write files
        write_cmdlets = [
            "Out-File",
            "Set-Content",
            "Add-Content",
            "Export-Csv",
            "Export-Clixml",
            "Export-Json",
            "Tee-Object",
            "Start-Transcript",
            "ConvertTo-Json",
            "ConvertTo-Csv",
            "ConvertTo-Html",
            "ConvertTo-Xml",
        ]

        # File redirection operators
        redirection_patterns = [">", ">>", "|", "Tee"]

        code_lower = code.lower()

        for cmdlet in write_cmdlets:
            if cmdlet.lower() in code_lower:
                file_operations.append(f"file_write:{cmdlet}")

        for pattern in redirection_patterns:
            if pattern in code:
                file_operations.append(f"redirection:{pattern}")

        # Check for common file creation patterns
        if any(pattern in code_lower for pattern in ["new-item", "copy-item", "move-item"]):
            file_operations.append("file_manipulation")

        return file_operations

    def _post_execution_bom_cleanup(self, code: str, current_dir: str) -> int:
        """
        Perform BOM cleanup after command execution based on what the command did.

        Args:
            code: The executed PowerShell code
            current_dir: Current working directory

        Returns:
            int: Number of files cleaned
        """
        file_operations = self._detect_file_operations(code)

        if not file_operations:
            return 0

        print(f"[BOM] Detected file operations: {', '.join(file_operations)}")

        # Clean current directory for any file operations
        bom_count = 0

        try:
            # Always clean the current directory if file operations detected
            bom_count += self._bom_remover.remove_bom_from_directory(current_dir, recursive=False)

            # For specific patterns, do more targeted cleanup
            if any("Export-" in op for op in file_operations):
                # Exported files often have BOMs, check common export locations
                bom_count += self._bom_remover.remove_bom_from_pattern(os.path.join(current_dir, "*.csv"))
                bom_count += self._bom_remover.remove_bom_from_pattern(os.path.join(current_dir, "*.json"))
                bom_count += self._bom_remover.remove_bom_from_pattern(os.path.join(current_dir, "*.xml"))

            if any("redirection" in op for op in file_operations):
                # Check for common output file patterns
                bom_count += self._bom_remover.remove_bom_from_pattern(os.path.join(current_dir, "*.txt"))
                bom_count += self._bom_remover.remove_bom_from_pattern(os.path.join(current_dir, "*.log"))

        except Exception as e:
            print(f"[BOM] Error during post-execution cleanup: {str(e)}")

        if bom_count > 0:
            print(f"[BOM] Post-execution cleanup: {bom_count} BOMs removed")

        return bom_count

    def execute(self, code: str, timeout: float = 60) -> str:
        """
        Execute PowerShell code and return its complete output.
        Includes automatic BOM removal after file operations.

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
            raise Exception("PowerShell process is not running")

        try:
            self._command_counter += 1
            delimiter = f"<<<COMMAND_{self._command_counter}_COMPLETE>>>"

            # Use a more robust approach for complex code execution
            wrapped_code = self._wrap_code_safely(code, delimiter)

            # Clear queues
            while not self._output_queue.empty():
                self._output_queue.get_nowait()
            while not self._error_queue.empty():
                self._error_queue.get_nowait()

            self._process.stdin.write(wrapped_code + "\n")
            self._process.stdin.flush()

            output_lines = []
            error_output = []
            start_time = time.time()
            done = False

            while not done:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Command execution timed out after {timeout} seconds")

                if self._process.poll() is not None:
                    raise Exception("PowerShell process unexpectedly closed")

                try:
                    line = self._output_queue.get(timeout=0.1)
                    if line is None:
                        raise Exception("PowerShell process closed stdout")
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
                            raise Exception("PowerShell process closed stderr")
                        error_output.append(line)
                except Empty:
                    pass

            all_output = [line for line in output_lines if line.strip()]
            if error_output:
                error_lines = [line for line in error_output if line.strip()]
                if error_lines:
                    all_output.extend(["", "Errors:", *error_lines])

            # Get current directory for display and BOM cleanup
            try:
                current_dir = self._get_current_directory()
                dir_info = f"[System: current directory <{current_dir}>]"

                # Perform BOM cleanup after execution
                bom_count = self._post_execution_bom_cleanup(code, current_dir)
                if bom_count > 0:
                    dir_info += f" [BOM cleanup: {bom_count} files processed]"

                if all_output:
                    all_output.insert(0, dir_info)
                else:
                    all_output = [dir_info]
            except Exception:
                pass  # If we can't get directory, continue without it

            return "\n".join(all_output)

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
            delimiter = f"<<<DIR_QUERY_{temp_counter}_COMPLETE>>>"
            # Clear queues first
            while not self._output_queue.empty():
                try:
                    self._output_queue.get_nowait()
                except Exception:
                    break
            # Send directory query
            dir_command = f"(Get-Location).Path; Write-Output '{delimiter}'"
            self._process.stdin.write(dir_command + "\n")
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
                except Exception:
                    continue
            # Return the first non-empty line as the directory
            for line in result_lines:
                if line and not line.startswith("PS ") and (":\\" in line or line.startswith("/")):
                    self._current_directory = line
                    return line
            return self._current_directory
        except Exception:
            return self._current_directory

    def _wrap_code_safely(self, code: str, delimiter: str) -> str:
        """
        Safely wrap code for execution, handling complex strings and
        multiline code.
        """
        # Check if this looks like a complex Python command that might have
        # quote issues
        if "python -c" in code and ('"' in code or "'" in code):
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

    def _handle_python_command_safely(self, code: str, delimiter: str) -> str:
        """
        Handle Python commands with complex strings by using file-based
        execution.
        """
        # Extract the Python code part
        if 'python -c "' in code:
            # Find the Python code between quotes
            start_idx = code.find('python -c "') + len('python -c "')
            # Find the closing quote - this is tricky with nested quotes
            quote_count = 0
            end_idx = start_idx
            for i, char in enumerate(code[start_idx:], start_idx):
                if char == '"' and (i == start_idx or code[i - 1] != "\\"):
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
                    # Write Python code to temp file with UTF-8 encoding (no BOM)
                    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
                    [System.IO.File]::WriteAllText($tempFile, $pythonCode, $utf8NoBom)
                    
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
    Thread-safe PowerShell session manager that maintains separate
    sessions.
    Each instance automatically gets its own unique ID and isolated PowerShell session.
    Includes session recovery logic for lost or failed sessions.
    Now includes integrated BOM removal capabilities.
    """

    _instances: Dict[str, "PowerShellManager"] = {}
    _lock = Lock()

    @classmethod
    def get_instance(cls, bot_id: str = None) -> "PowerShellManager":
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
        raise RuntimeError("Use PowerShellManager.get_instance() to create or get a PowerShell manager")

    @property
    def session(self) -> PowerShellSession:
        """
        Get the PowerShell session for the current thread.
        Creates a new session if none exists or if the current session is
        invalid.
        """
        try:
            if not hasattr(self._thread_local, "session"):
                print(f"Session not found for {self.bot_id}, starting new session")
                self._start_new_session()
            elif not self._is_session_valid():
                print(f"Invalid session detected for {self.bot_id}, starting new session")
                self.cleanup()
                self._start_new_session()
            return self._thread_local.session
        except Exception as e:
            print(f"Error accessing session: {str(e)}. Starting new session.")
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
            if not hasattr(self._thread_local, "session"):
                return False
            session = self._thread_local.session
            if not session._process or session._process.poll() is not None:
                return False
            # Use a simple test that's less likely to cause issues
            test_output = session.execute("Write-Output 'test'", timeout=5)
            return "test" in test_output
        except Exception as e:
            print(f"Session validation failed: {str(e)}")
            return False

    def execute(self, code: str, output_length_limit: str = "60", timeout: float = 60) -> Generator[str, None, None]:
        """
        Execute PowerShell code in the session with automatic recovery and BOM removal.

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
            error_message = f"Tool Failed: {str(error)}\n"
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
                        truncated_output = "\n".join(start_lines)
                        truncated_output += f"\n\n... {lines_omitted} lines omitted ...\n\n"
                        truncated_output += "\n".join(end_lines)

                        output_file = os.path.join(os.getcwd(), f"ps_output_{self.bot_id}.txt")
                        with open(
                            output_file,
                            "w",
                            encoding="utf-8",
                            errors="replace",
                            newline="",
                        ) as f:
                            f.write(output)

                        # Remove BOM from the output file we just created
                        BOMRemover.remove_bom_from_file(output_file)

                        truncated_output += f"\nFull output saved to {output_file}"
                        yield truncated_output
                    else:
                        yield output
                else:
                    yield output
                break

            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    print(f"Command failed, attempt {retry_count} of {max_retries}. " f"Starting new session...")
                    self.cleanup()
                else:
                    yield _process_error(e)

    def cleanup(self):
        """
        Clean up the PowerShell session for the current thread.
        Should be called when work is done or when a session needs to be reset.
        """
        if hasattr(self._thread_local, "session"):
            try:
                self._thread_local.session.__exit__(None, None, None)
            except Exception as e:
                print(f"Error during session cleanup: {str(e)}")
            finally:
                delattr(self._thread_local, "session")


def _get_active_sessions() -> list:
    """
    Get information about all active PowerShell sessions.

    Returns:
        List of dictionaries containing session information
    """
    sessions = []
    for thread in threading.enumerate():
        if hasattr(thread, "_thread_local"):
            local_dict = thread._thread_local.__dict__
            if "ps_manager" in local_dict:
                manager = local_dict["ps_manager"]
                sessions.append(
                    {
                        "bot_id": manager.bot_id,
                        "thread_name": thread.name,
                        "created_at": manager.created_at.isoformat(),
                        "active": hasattr(manager._thread_local, "session"),
                    }
                )
    return sessions


@handle_errors
def _execute_powershell_stateless(code: str, output_length_limit: str = "120"):
    """
    Executes PowerShell code in a stateless environment with BOM removal

    Use when you need to run PowerShell commands and capture their output. If
    you have other tools available, you should use this as a fallback when the
    other tools fail. Coerces to utf-8 encoding without BOM.

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
        error_message = f"Tool Failed: {str(error)}\n"
        error_message += f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}"
        return error_message

    output = ""
    current_dir = os.getcwd()

    try:
        processed_code = _process_commands(code)
        setup_encoding = """
        $PSDefaultParameterValues['*:Encoding'] = 'utf8NoBOM'
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::InputEncoding = [System.Text.Encoding]::UTF8
        $OutputEncoding = [System.Text.Encoding]::UTF8
        $env:PYTHONIOENCODING = "utf-8"
        """
        wrapped_code = f"{setup_encoding}; {processed_code}"

        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                wrapped_code,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = process.communicate(timeout=300)

        output = stdout
        if stderr:
            output += stderr

        # Perform BOM cleanup after stateless execution
        try:
            session = PowerShellSession()
            bom_count = session._post_execution_bom_cleanup(code, current_dir)
            if bom_count > 0:
                output += f"\n[BOM cleanup: {bom_count} files processed]"
        except Exception as e:
            print(f"[BOM] Error during stateless cleanup: {str(e)}")

    except subprocess.TimeoutExpired:
        process.kill()
        output += "Error: Command execution timed out after 300 seconds."
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
            truncated_output = "\n".join(start_lines)
            truncated_output += f"\n\n... {lines_omitted} lines omitted ...\n\n"
            truncated_output += "\n".join(end_lines)

            output_file = os.path.join(os.getcwd(), "ps_output.txt")
            with open(
                output_file,
                "w",
                encoding="utf-8",
                errors="replace",
                newline="",
            ) as f:
                f.write(output)

            # Remove BOM from the output file we just created
            BOMRemover.remove_bom_from_file(output_file)

            truncated_output += f"\nFull output saved to {output_file}"
            return truncated_output

    return output


def _process_commands(code: str) -> str:
    """
    Process PowerShell commands separated by &&, ensuring each command only
    runs if the previous succeeded.
    Uses PowerShell error handling to catch both command failures and
    non-existent commands.

    Enhanced to better handle complex multiline code blocks.

    Args:
        code (str): The original command string with && separators

    Returns:
        str: PowerShell code with proper error checking between commands
    """
    # Don't process commands that look like multiline code blocks
    if "\n" in code.strip() and "&&" not in code:
        return code

    # Split on && but be more careful about it
    commands = []
    current_cmd = ""
    i = 0
    in_quotes = False
    quote_char = None

    while i < len(code):
        char = code[i]

        if char in ['"', "'"] and (i == 0 or code[i - 1] != "\\"):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None

        if not in_quotes and i < len(code) - 1 and code[i : i + 2] == "&&":
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
        wrapped_cmd = (
            f'$ErrorActionPreference = "Stop"; try {{ {cmd}; $LastSuccess = $true }} catch {{ $LastSuccess = $false; $_ }}'
        )
        processed_commands.append(wrapped_cmd)

    return "; ".join([processed_commands[0]] + [f"if ($LastSuccess) {{ {cmd} }}" for cmd in processed_commands[1:]])


# Additional utility functions for BOM management


@handle_errors
def remove_bom_from_current_directory(recursive: bool = True) -> str:
    """
    Manually remove BOMs from all eligible files in the current directory.

    Args:
        recursive: Whether to process subdirectories

    Returns:
        str: Summary of BOM removal operation
    """
    current_dir = os.getcwd()
    bom_count = BOMRemover.remove_bom_from_directory(current_dir, recursive)

    if bom_count > 0:
        return f"BOM removal completed. {bom_count} files processed in {current_dir}"
    else:
        return f"No BOMs found in {current_dir}"


@handle_errors
def remove_bom_from_files(file_pattern: str) -> str:
    """
    Manually remove BOMs from files matching a specific pattern.

    Args:
        file_pattern: Glob pattern to match files (e.g., "*.py", "**/*.txt")

    Returns:
        str: Summary of BOM removal operation
    """
    bom_count = BOMRemover.remove_bom_from_pattern(file_pattern)

    if bom_count > 0:
        return f"BOM removal completed. {bom_count} files processed matching pattern: {file_pattern}"
    else:
        return f"No BOMs found in files matching pattern: {file_pattern}"


@handle_errors
def check_files_for_bom(directory: str = None) -> str:
    """
    Check files for BOMs without removing them.

    Args:
        directory: Directory to check (defaults to current directory)

    Returns:
        str: Report of files containing BOMs
    """
    if directory is None:
        directory = os.getcwd()

    bom_files = []

    try:
        for root, dirs, files in os.walk(directory):
            # Filter out directories to skip
            dirs[:] = [d for d in dirs if d not in BOMRemover.SKIP_DIRS]

            for file in files:
                file_path = os.path.join(root, file)

                if not BOMRemover.should_process_file(file_path):
                    continue

                try:
                    with open(file_path, "rb") as f:
                        content = f.read(3)  # Only read first 3 bytes

                    if content.startswith(codecs.BOM_UTF8):
                        bom_files.append(file_path)

                except Exception as e:
                    print(f"Error checking {file_path}: {str(e)}")

    except Exception as e:
        return f"Error scanning directory {directory}: {str(e)}"

    if bom_files:
        file_list = "\n".join(f"  - {f}" for f in bom_files)
        return f"Found {len(bom_files)} files with BOMs in {directory}:\n{file_list}"
    else:
        return f"No BOMs found in {directory}"
