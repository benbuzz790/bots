import os
import shutil
import tempfile
import time
import unittest

from bots.tools.terminal_tools import PowerShellSession


class TestPowerShellTimeoutDebug(unittest.TestCase):
    """Test suite specifically for debugging PowerShell timeout issues"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_cwd = os.getcwd()
        os.chdir(cls.temp_dir)
        print(f"Test directory: {cls.temp_dir}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        os.chdir(cls.original_cwd)
        try:
            shutil.rmtree(cls.temp_dir)
        except Exception:
            pass

    def setUp(self):
        """Set up for each test"""
        print(f"\n{'='*60}")
        print(f"Running: {self._testMethodName}")
        print(f"{'='*60}")

    def tearDown(self):
        """Clean up after each test"""
        # Clean up any test files
        for pattern in ["*.txt", "*.py", "*.log"]:
            import glob

            for file in glob.glob(pattern):
                try:
                    os.unlink(file)
                except Exception:
                    pass

    def test_here_string_basic(self):
        """Test basic here-string functionality"""
        print("\n=== Testing Basic Here-String ===")
        command = """@'
        Hello World
        '@"""
        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Basic here-string completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
                self.assertIn("Hello World", result)
            except TimeoutError as e:
                elapsed = time.time() - start_time
                print(f"❌ Basic here-string timed out after {elapsed:.2f}s")
                self.fail(f"Basic here-string should not timeout: {e}")

    def test_here_string_with_pipe(self):
        """Test here-string with pipe to Out-File"""
        print("\n=== Testing Here-String with Pipe ===")
        command = """@'
        Test Content
        '@ | Out-File test.txt -Encoding UTF8"""
        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Here-string with pipe completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
                # Check if file was created
                if os.path.exists("test.txt"):
                    print("✅ File created successfully")
                    with open("test.txt", "r", encoding="utf-8") as f:
                        content = f.read()
                    print(f"File content: {repr(content)}")
                else:
                    print("❌ File was not created")
            except TimeoutError as e:
                elapsed = time.time() - start_time
                print(f"❌ Here-string with pipe timed out after {elapsed:.2f}s")
                self.fail(f"Here-string with pipe should not timeout: {e}")

    def test_here_string_multiline(self):
        """Test multiline here-string (the problematic case)"""
        print("\n=== Testing Multiline Here-String ===")
        command = """@'
        Line 1
        Line 2
        Line 3
        '@"""
        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Multiline here-string completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
                # Verify all lines are present
                self.assertIn("Line 1", result)
                self.assertIn("Line 2", result)
                self.assertIn("Line 3", result)
            except TimeoutError as e:
                elapsed = time.time() - start_time
                print(f"❌ Multiline here-string timed out after {elapsed:.2f}s")
                self.fail(f"Multiline here-string should not timeout: {e}")

    def test_here_string_with_special_chars(self):
        """Test here-string with special characters"""
        print("\n=== Testing Here-String with Special Characters ===")
        command = """@'
        Special chars: "quotes" and 'apostrophes'
        Unicode: café résumé naïve
        Symbols: $variable @array %hash
        '@"""
        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Special chars here-string completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
                # Basic verification
                self.assertIn("Special chars", result)
                self.assertIn("Unicode", result)
            except TimeoutError as e:
                elapsed = time.time() - start_time
                print(f"❌ Special chars here-string timed out after {elapsed:.2f}s")
                self.fail(f"Special chars here-string should not timeout: {e}")

    def test_here_string_with_empty_lines(self):
        """Test here-string with empty lines"""
        print("\n=== Testing Here-String with Empty Lines ===")
        command = """@'
        Line 1

        Line 3

        Line 5
        '@"""
        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Empty lines here-string completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
                # Count newlines to verify empty lines were preserved
                result_lines = result.split("\n")
                print(f"Number of lines in result: {len(result_lines)}")
            except TimeoutError as e:
                elapsed = time.time() - start_time
                print(f"❌ Empty lines here-string timed out after {elapsed:.2f}s")
                self.fail(f"Empty lines here-string should not timeout: {e}")

    def test_problematic_python_code_here_string(self):
        """Test the exact problematic case from the error"""
        print("\n=== Testing Problematic Python Code Here-String ===")
        # This is a simplified version of the problematic command
        command = """Remove-Item create_sample.py -ErrorAction SilentlyContinue
        @'
        from bots.tools.python_edit import python_edit
        sample_code = '''#!/usr/bin/env python3

        def hello_world():
            print("Hello, World!")
            return "success"

        if __name__ == "__main__":
            result = hello_world()
            print(f"Result: {result}")
        '''
        result = python_edit("sample_demo.py", sample_code)
        print("SUCCESS: Created sample file")
        '@ | Out-File -FilePath create_sample.py -Encoding UTF8
        python create_sample.py"""
        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=10)
                elapsed = time.time() - start_time
                print(f"✅ Complex here-string completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Complex here-string timed out after {elapsed:.2f}s")
                print("This confirms the timeout issue with complex here-strings")

    def test_delimiter_detection(self):
        """Test if delimiter is being properly written and detected"""
        print("\n=== Testing Delimiter Detection ===")
        session = PowerShellSession()
        with session:
            # Patch the output queue to monitor what's being received
            original_queue = session._output_queue
            received_items = []

            class MonitoringQueue:

                def __init__(self, original):
                    self.original = original

                def get(self, timeout=None):
                    item = self.original.get(timeout=timeout)
                    received_items.append(item)
                    print(f"Queue received: {repr(item)}")
                    return item

                def get_nowait(self):
                    return self.original.get_nowait()

                def empty(self):
                    return self.original.empty()

                def put(self, item):
                    return self.original.put(item)

            session._output_queue = MonitoringQueue(original_queue)
            # Simple command that should complete quickly
            command = "Write-Output 'Test'"
            try:
                session.execute(command, timeout=5)
                print("✅ Command completed")
                print(f"Items received: {len(received_items)}")
                # Check if delimiter was received
                delimiter_found = any(
                    ("COMMAND_" in str(item) and "_COMPLETE" in str(item) for item in received_items if item)
                )
                if delimiter_found:
                    print("✅ Delimiter was properly received")
                else:
                    print("❌ Delimiter was NOT received")
                    print(f"All items: {received_items}")
            except TimeoutError:
                print("❌ Command timed out")
                print(f"Items received before timeout: {received_items}")

    def test_wrap_code_safely_output(self):
        """Test what _wrap_code_safely actually produces"""
        print("\n=== Testing _wrap_code_safely Output ===")
        session = PowerShellSession()
        with session:
            test_code = """@'
            Hello World
            '@"""
            delimiter = "<<<COMMAND_TEST_COMPLETE>>>"
            wrapped = session._wrap_code_safely(test_code, delimiter)
            print("Original code:")
            print(test_code)
            print("\nWrapped code:")
            print(wrapped)
            print("\n" + "=" * 50)
            # Check for potential issues
            if "$LASTOUTPUT" in wrapped:
                print("⚠️  Warning: $LASTOUTPUT is not a standard PowerShell variable")
            # Test if the wrapped code is valid PowerShell
            try:
                # Execute just the wrapped code to see what happens
                session.execute(wrapped.replace(delimiter, "TEST_DELIMITER"), timeout=5)
                print("✅ Wrapped code executed successfully")
            except Exception as e:
                print(f"❌ Wrapped code failed: {e}")

    def test_simple_vs_complex_wrapping(self):
        """Compare simple vs complex command wrapping"""
        print("\n=== Testing Simple vs Complex Wrapping ===")
        session = PowerShellSession()
        with session:
            # Test 1: Very simple wrapping
            simple_command = "Write-Output 'Hello'"
            delimiter = "<<<SIMPLE_COMPLETE>>>"
            # Try minimal wrapping
            minimal_wrap = f"{simple_command}; Write-Output '{delimiter}'"
            start_time = time.time()
            try:
                # Directly write to stdin
                session._process.stdin.write(minimal_wrap + "\n")
                session._process.stdin.flush()
                # Read output manually
                output_lines = []
                while True:
                    line = session._output_queue.get(timeout=2)
                    if line == delimiter:
                        break
                    output_lines.append(line)
                elapsed = time.time() - start_time
                print(f"✅ Minimal wrapping completed in {elapsed:.2f}s")
                print(f"Output: {output_lines}")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Minimal wrapping failed after {elapsed:.2f}s: {e}")

    def test_stdin_write_behavior(self):
        """Test stdin write behavior with different content"""
        print("\n=== Testing stdin.write Behavior ===")
        session = PowerShellSession()
        with session:
            test_cases = [
                ("Simple", "Write-Output 'Simple'"),
                ("With newline", "Write-Output 'Line1'\nWrite-Output 'Line2'"),
                ("Here-string single line", "@'\nHello\n'@"),
                ("Here-string multi line", "@'\nLine1\nLine2\n'@"),
            ]
            for name, command in test_cases:
                print(f"\n--- Testing: {name} ---")
                print(f"Command: {repr(command)}")
                # Clear queues
                while not session._output_queue.empty():
                    session._output_queue.get_nowait()
                delimiter = f"<<<{name.upper()}_COMPLETE>>>"
                full_command = f"{command}; Write-Output '{delimiter}'"
                start_time = time.time()
                try:
                    session._process.stdin.write(full_command + "\n")
                    session._process.stdin.flush()
                    output = []
                    found_delimiter = False
                    while time.time() - start_time < 2:
                        try:
                            line = session._output_queue.get(timeout=0.1)
                            if line == delimiter:
                                found_delimiter = True
                                break
                            output.append(line)
                        except Exception:
                            continue
                    elapsed = time.time() - start_time
                    if found_delimiter:
                        print(f"✅ Completed in {elapsed:.2f}s")
                        print(f"Output: {output}")
                    else:
                        print(f"❌ No delimiter after {elapsed:.2f}s")
                        print(f"Partial output: {output}")
                except Exception as e:
                    print(f"❌ Exception: {e}")

    def test_here_string_terminal_behavior(self):
        """Test how here-strings behave in interactive terminal"""
        print("\n=== Testing Here-String Terminal Behavior ===")
        # Test if here-strings need special handling when sent via stdin
        session = PowerShellSession()
        with session:
            # Method 1: Send as single block
            print("\n--- Method 1: Single Block ---")
            command1 = "@'\nHello World\n'@\nWrite-Output '<<<DONE1>>>'"
            session._process.stdin.write(command1 + "\n")
            session._process.stdin.flush()
            output1 = []
            start_time = time.time()
            while time.time() - start_time < 2:
                try:
                    line = session._output_queue.get(timeout=0.1)
                    if line == "<<<DONE1>>>":
                        print("✅ Method 1 completed")
                        break
                    output1.append(line)
                except Exception:
                    continue
            else:
                print("❌ Method 1 timed out")
            print(f"Output: {output1}")
            # Method 2: Send line by line
            print("\n--- Method 2: Line by Line ---")
            lines = ["@'", "Hello World", "'@", "Write-Output '<<<DONE2>>>'"]
            for line in lines:
                session._process.stdin.write(line + "\n")
                session._process.stdin.flush()
                time.sleep(0.1)  # Small delay between lines
            output2 = []
            start_time = time.time()
            while time.time() - start_time < 2:
                try:
                    line = session._output_queue.get(timeout=0.1)
                    if line == "<<<DONE2>>>":
                        print("✅ Method 2 completed")
                        break
                    output2.append(line)
                except Exception:
                    continue
            else:
                print("❌ Method 2 timed out")
            print(f"Output: {output2}")

    def test_error_in_wrapped_code(self):
        """Test if errors in wrapped code are preventing delimiter output"""
        print("\n=== Testing Error in Wrapped Code ===")
        session = PowerShellSession()
        with session:
            # The $LASTOUTPUT variable doesn't exist in PowerShell
            # This might be causing an error that prevents delimiter output
            # Test accessing $LASTOUTPUT
            test_command = "Write-Output $LASTOUTPUT"
            try:
                result = session.execute(test_command, timeout=5)
                print(f"Result: {repr(result)}")
                if "errors" in result.lower():
                    print("⚠️  $LASTOUTPUT causes an error - this might be the issue!")
            except Exception as e:
                print(f"❌ Error accessing $LASTOUTPUT: {e}")

    def test_alternative_wrapping_approach(self):
        """Test alternative wrapping approach without $LASTOUTPUT"""
        print("\n=== Testing Alternative Wrapping Approach ===")

        class TestSession(PowerShellSession):

            def _wrap_code_safely(self, code: str, delimiter: str) -> str:
                """Alternative wrapping without $LASTOUTPUT"""
                return f"""
                $ErrorActionPreference = 'Stop'
                try {{
                    {code}
                }} catch {{
                    Write-Error $_
                }}
                Write-Output '{delimiter}'
                """

        session = TestSession()
        with session:
            # Test the problematic here-string
            command = """@'
            Hello from alternative wrapper
            Multiple lines
            '@ | Out-File test_alt.txt"""
            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Alternative wrapper completed in {elapsed:.2f}s")
                print(f"Result: {repr(result)}")
                if os.path.exists("test_alt.txt"):
                    print("✅ File created successfully with alternative wrapper")
            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Alternative wrapper timed out after {elapsed:.2f}s")
                print("Issue might not be with $LASTOUTPUT")

    def test_process_communication_health(self):
        """Test if the PowerShell process communication is healthy"""
        print("\n=== Testing Process Communication Health ===")
        session = PowerShellSession()
        with session:
            # Check if process is alive
            print(f"Process alive: {session._process.poll() is None}")
            print(f"Process PID: {session._process.pid}")
            # Test rapid command execution
            for i in range(5):
                try:
                    session.execute(f"Write-Output 'Test {i}'", timeout=2)
                    print(f"✅ Command {i} succeeded")
                except Exception as e:
                    print(f"❌ Command {i} failed: {e}")
            # Check process state after tests
            print(f"Process still alive: {session._process.poll() is None}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
