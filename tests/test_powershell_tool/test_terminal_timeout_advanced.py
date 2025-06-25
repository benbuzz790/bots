import os
import shutil
import tempfile
import threading
import time
import unittest

from bots.tools.terminal_tools import PowerShellSession


class TestPowerShellAdvancedDiagnostics(unittest.TestCase):
    """Advanced diagnostic tests for PowerShell timeout issues"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        try:
            os.chdir(cls.original_cwd)
            if os.path.exists(cls.temp_dir):
                shutil.rmtree(cls.temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")

    def setUp(self):
        """Set up each test"""
        os.chdir(self.temp_dir)

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

    def test_exact_problematic_command(self):
        """Test the EXACT command that's failing in production"""
        print("\n=== Testing EXACT Problematic Command ===")

        # This is the exact command from your error log
        command = """
                                                    # Clean up and create a
    properly formatted test
                                                    Remove-Item create_sample.py
    -ErrorAction SilentlyContinue
                                                    @'
                            from bots.tools.python_edit import python_edit
                            sample_code = '''#!/usr/bin/env python3
                            \"\"\"
                            Sample Python demonstration file
                            This file showcases various Python features and best
    practices.
                            \"\"\"
                            import math
                            import random
                            from typing import List, Dict, Optional
                            class Calculator:
                                \"\"\"A simple calculator class demonstrating OOP
    concepts.\"\"\"
                                def **init**(self, name: str = "Basic
    Calculator"):
                                    self.name = name
                                    self.history: List[str] = []
                                def add(self, a: float, b: float) -> float:
                                    \"\"\"Add two numbers and record the
    operation.\"\"\"
                                    result = a + b
                                    self.history.append(f"{a} + {b} = {result}")
                                    return result
                            def main():
                                \"\"\"Main function demonstrating the usage of our
    classes and functions.\"\"\"
                                print("=== Python Demo Script ===")
                                calc = Calculator("Demo Calculator")
                                result = calc.add(15, 25)
                                print(f"Addition result: {result}")
                            if **name** == "__main__":
                                main()
                            '''
                            result = python_edit("sample_demo.py", sample_code)
                            print("SUCCESS: Created sample file")
                            print("Result:", result)
                            '@ | Out-File -FilePath create_sample.py -Encoding
    UTF8
                                                    python create_sample.py"""

        session = PowerShellSession()
        with session:
            start_time = time.time()
            try:
                result = session.execute(command, timeout=15)
                elapsed = time.time() - start_time
                print(f"✅ Command completed in {elapsed:.2f}s")
                print(f"Result preview: {repr(result[:500])}...")

                # Check if file was created
                if os.path.exists("create_sample.py"):
                    print("✅ create_sample.py was created")
                    with open("create_sample.py", "rb") as f:
                        first_bytes = f.read(20)
                    print(f"First bytes: {first_bytes}")
                else:
                    print("❌ create_sample.py was NOT created")

            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Command timed out after {elapsed:.2f}s")
                print("Confirming the timeout issue exists")
            except Exception as e:
                print(f"❌ Unexpected error: {type(e).__name__}: {e}")

    def test_whitespace_impact(self):
        """Test if leading whitespace affects here-strings"""
        print("\n=== Testing Whitespace Impact ===")

        test_cases = [
            ("No indent", "@'\nHello World\n'@"),
            ("4 spaces", "    @'\nHello World\n'@"),
            ("8 spaces", "        @'\nHello World\n'@"),
            ("Tab", "\t@'\nHello World\n'@"),
            ("Mixed", "    \t    @'\nHello World\n'@"),
            ("Spaces in terminator", "@'\nHello World\n    '@"),  # Invalid
        ]

        session = PowerShellSession()
        with session:
            for name, command in test_cases:
                print(f"\n--- Testing: {name} ---")
                start_time = time.time()

                try:
                    result = session.execute(command, timeout=3)
                    elapsed = time.time() - start_time
                    print(f"✅ Completed in {elapsed:.2f}s")
                    if "Hello World" in result:
                        print("✅ Output contains expected text")
                    else:
                        print(f"⚠️  Unexpected output: {repr(result)}")
                except TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"❌ Timed out after {elapsed:.2f}s")
                except Exception as e:
                    print(f"❌ Error: {type(e).__name__}: {e}")

    def test_command_preprocessing(self):
        """Test if command preprocessing affects execution"""
        print("\n=== Testing Command Preprocessing ===")

        # Test what _process_commands does to here-strings
        from bots.tools.terminal_tools import _process_commands

        test_commands = [
            "Write-Output 'test'",
            "@'\nHello\n'@",
            "Write-Output 'test' && Write-Output 'test2'",
            "@'\nHello\n'@ && Write-Output 'After'",
        ]

        for cmd in test_commands:
            print(f"\nOriginal: {repr(cmd)}")
            processed = _process_commands(cmd)
            print(f"Processed: {repr(processed)}")

            if "@'" in cmd and processed != cmd:
                print("⚠️  Here-string was modified by processing!")

    def test_queue_blocking_scenarios(self):
        """Test if output/error queues are blocking"""
        print("\n=== Testing Queue Blocking Scenarios ===")

        session = PowerShellSession()
        with session:
            # Test 1: Generate lots of output quickly
            print("\n--- Test 1: High Volume Output ---")
            high_volume_cmd = '1..1000 | ForEach-Object { Write-Output "Line $_" }'

            start_time = time.time()
            try:
                result = session.execute(high_volume_cmd, timeout=5)
                elapsed = time.time() - start_time
                lines = result.split("\n")
                print(f"✅ High volume completed in {elapsed:.2f}s with {len(lines)} lines")
            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ High volume timed out after {elapsed:.2f}s")

            # Test 2: Generate error output
            print("\n--- Test 2: Error Output ---")
            error_cmd = "Write-Error 'Test Error' -ErrorAction Continue; Write-Output 'After error'"

            start_time = time.time()
            try:
                result = session.execute(error_cmd, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Error output completed in {elapsed:.2f}s")
                if "Errors:" in result:
                    print("✅ Error section found in output")
            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Error output timed out after {elapsed:.2f}s")

    def test_reader_thread_health(self):
        """Test if reader threads are functioning properly"""
        print("\n=== Testing Reader Thread Health ===")

        session = PowerShellSession()
        with session:
            # Check reader threads
            print(f"Number of reader threads: {len(session._reader_threads)}")

            for i, thread in enumerate(session._reader_threads):
                print(f"Thread {i}: alive={thread.is_alive()}, daemon={thread.daemon}")

            # Monitor queue activity
            print("\n--- Monitoring Queue Activity ---")

            # Send a simple command and monitor queues
            session._process.stdin.write("Write-Output 'Thread test'\n")
            session._process.stdin.flush()

            # Give threads time to process
            time.sleep(0.5)

            output_items = []
            error_items = []

            # Drain queues
            while not session._output_queue.empty():
                try:
                    output_items.append(session._output_queue.get_nowait())
                except Exception:
                    break

            while not session._error_queue.empty():
                try:
                    error_items.append(session._error_queue.get_nowait())
                except Exception:
                    break

            print(f"Output queue items: {len(output_items)}")
            print(f"Error queue items: {len(error_items)}")
            if output_items:
                print(f"Output samples: {output_items[:5]}")

    def test_encoding_edge_cases(self):
        """Test encoding edge cases that might cause hangs"""
        print("\n=== Testing Encoding Edge Cases ===")

        session = PowerShellSession()
        with session:
            # Test various problematic characters
            test_cases = [
                ("Null char", "Write-Output 'Before\x00After'"),
                ("BOM char", "Write-Output '\ufeffBOM test'"),
                ("Control chars", "Write-Output 'Test\x01\x02\x03'"),
                ("Mixed newlines", "Write-Output 'Line1\r\nLine2\nLine3\rLine4'"),
                ("Unicode escapes", 'Write-Output "Test \\u0041 \\u0042"'),
            ]

            for name, command in test_cases:
                print(f"\n--- Testing: {name} ---")
                start_time = time.time()

                try:
                    result = session.execute(command, timeout=3)
                    elapsed = time.time() - start_time
                    print(f"✅ Completed in {elapsed:.2f}s")
                    print(f"Result: {repr(result[:100])}")
                except TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"❌ Timed out after {elapsed:.2f}s")
                except Exception as e:
                    print(f"❌ Error: {type(e).__name__}: {e}")

    def test_buffer_size_impact(self):
        """Test if buffer sizes affect here-string handling"""
        print("\n=== Testing Buffer Size Impact ===")

        # Test different sizes of here-string content
        sizes = [10, 100, 1000, 10000]

        session = PowerShellSession()
        with session:
            for size in sizes:
                print(f"\n--- Testing {size} byte here-string ---")
                content = "x" * size
                command = f"@'\n{content}\n'@"

                start_time = time.time()
                try:
                    result = session.execute(command, timeout=5)
                    elapsed = time.time() - start_time
                    print(f"✅ {size} bytes completed in {elapsed:.2f}s")
                    if content in result:
                        print("✅ Content preserved correctly")
                except TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"❌ {size} bytes timed out after {elapsed:.2f}s")
                    print(f"Buffer size {size} might be problematic")

    def test_concurrent_io_patterns(self):
        """Test concurrent I/O patterns that might cause deadlock"""
        print("\n=== Testing Concurrent I/O Patterns ===")

        session = PowerShellSession()
        with session:
            # Test interleaved stdout/stderr
            command = """
            1..10 | ForEach-Object {
                if ($_ % 2 -eq 0) {
                    Write-Output "Stdout: $_"
                } else {
                    Write-Error "Stderr: $_" -ErrorAction Continue
                }
            }
            """

            start_time = time.time()
            try:
                result = session.execute(command, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Interleaved I/O completed in {elapsed:.2f}s")

                # Count stdout and stderr lines
                stdout_count = result.count("Stdout:")
                stderr_count = result.count("Stderr:")
                print(f"Stdout lines: {stdout_count}, Stderr lines: {stderr_count}")

            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Interleaved I/O timed out after {elapsed:.2f}s")
                print("Concurrent stdout/stderr might be causing deadlock")

    def test_process_state_during_timeout(self):
        """Monitor process state during a timeout scenario"""
        print("\n=== Testing Process State During Timeout ===")

        session = PowerShellSession()
        with session:
            # Use a command likely to timeout
            command = """@'
                            from bots.tools.python_edit import python_edit
                            sample_code = '''#!/usr/bin/env python3
                            import math
                            '''
                            '@ | Out-File -FilePath test_timeout.py"""

            # Start execution in a thread
            result_container = []
            exception_container = []

            def execute_command():
                try:
                    result = session.execute(command, timeout=3)
                    result_container.append(result)
                except Exception as e:
                    exception_container.append(e)

            thread = threading.Thread(target=execute_command)
            thread.start()

            # Monitor process state while command runs
            start_time = time.time()
            states = []

            while thread.is_alive() and time.time() - start_time < 4:
                state = {
                    "time": time.time() - start_time,
                    "process_alive": session._process.poll() is None,
                    "output_queue_size": (
                        session._output_queue.qsize() if hasattr(session._output_queue, "qsize") else "unknown"
                    ),
                    "error_queue_size": session._error_queue.qsize() if hasattr(session._error_queue, "qsize") else "unknown",
                }
                states.append(state)
                time.sleep(0.5)

            thread.join()

            print("Process state timeline:")
            for state in states:
                print(
                    f"  {state['time']:.1f}s: alive={state['process_alive']}, "
                    f"output_q={state['output_queue_size']}, error_q={state['error_queue_size']}"
                )

            if exception_container:
                print(f"Exception: {type(exception_container[0]).__name__}")

    def test_delimiter_in_different_contexts(self):
        """Test if delimiter output works in different contexts"""
        print("\n=== Testing Delimiter in Different Contexts ===")

        session = PowerShellSession()
        with session:
            delimiter = "<<<TEST_DELIMITER>>>"

            test_cases = [
                ("Direct", f"Write-Output '{delimiter}'"),
                ("After here-string", f"@'\nHello\n'@; Write-Output '{delimiter}'"),
                ("In try-catch", f"try {{ Write-Output '{delimiter}' }} catch {{ }}"),
                ("After error", f"Write-Error 'test' -ErrorAction SilentlyContinue; Write-Output '{delimiter}'"),
                ("In if block", f"if ($true) {{ Write-Output '{delimiter}' }}"),
            ]

            for name, command in test_cases:
                print(f"\n--- Testing delimiter {name} ---")

                # Clear queues
                while not session._output_queue.empty():
                    session._output_queue.get_nowait()

                # Send command directly
                session._process.stdin.write(command + "\n")
                session._process.stdin.flush()

                # Look for delimiter
                found = False
                start_time = time.time()
                collected = []

                while time.time() - start_time < 2:
                    try:
                        line = session._output_queue.get(timeout=0.1)
                        collected.append(line)
                        if delimiter in str(line):
                            found = True
                            break
                    except Exception:
                        continue

                if found:
                    print(f"✅ Delimiter found in {name} context")
                else:
                    print(f"❌ Delimiter NOT found in {name} context")
                    print(f"Collected output: {collected}")

    def test_manual_here_string_execution(self):
        """Manually test here-string execution step by step"""
        print("\n=== Manual Here-String Execution ===")

        session = PowerShellSession()
        with session:
            # Send here-string components separately with timing
            components = [
                ("Start here-string", "@'"),
                ("Content line 1", "Hello from manual test"),
                ("Content line 2", "This is line 2"),
                ("End here-string", "'@"),
                ("Delimiter", "Write-Output '<<<MANUAL_COMPLETE>>>'"),
            ]

            for desc, line in components:
                print(f"\nSending: {desc} -> {repr(line)}")
                session._process.stdin.write(line + "\n")
                session._process.stdin.flush()

                # Give it a moment to process
                time.sleep(0.1)

                # Check for any immediate output
                immediate_output = []
                timeout_time = time.time() + 0.5
                while time.time() < timeout_time:
                    try:
                        output = session._output_queue.get_nowait()
                        immediate_output.append(output)
                    except Exception:
                        break

                if immediate_output:
                    print(f"Immediate output: {immediate_output}")

            # Wait for final output
            print("\nWaiting for final output...")
            final_output = []
            timeout_time = time.time() + 2
            found_delimiter = False

            while time.time() < timeout_time:
                try:
                    output = session._output_queue.get(timeout=0.1)
                    final_output.append(output)
                    if "MANUAL_COMPLETE" in str(output):
                        found_delimiter = True
                        break
                except Exception:
                    continue

            if found_delimiter:
                print("✅ Manual execution completed successfully")
                print(f"Final output: {final_output}")
            else:
                print("❌ Manual execution did not complete")
                print(f"Partial output: {final_output}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
