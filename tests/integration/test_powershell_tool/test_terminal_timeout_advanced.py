import os
import shutil
import tempfile
import threading
import time
import unittest

import pytest

from bots.tools.terminal_tools import PowerShellSession

# Define encoding-safe status icons with fallbacks
try:
    OK_ICON = "✅"
    FAIL_ICON = "❌"
    WARN_ICON = "⚠️"
    # Test if they can be encoded
    OK_ICON.encode("utf-8")
except (UnicodeEncodeError, AttributeError):
    OK_ICON = "OK"
    FAIL_ICON = "FAIL"
    WARN_ICON = "WARN"


@pytest.mark.serial
class TestPowerShellAdvancedDiagnostics(unittest.TestCase):
    """Advanced diagnostic tests for PowerShell timeout issues"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.temp_dir = tempfile.mkdtemp(prefix=f"test_timeout_{id(cls)}_")
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

    def test_basic_command_execution(self):
        """Test basic command execution works"""
        print("\n=== Testing Basic Command Execution ===")
        session = PowerShellSession()
        with session:
            result = session.execute("Write-Output 'Hello World'", timeout=5)
            print(f"Result: {result}")
            assert "Hello World" in result

    def test_timeout_handling(self):
        """Test that timeouts are handled correctly"""
        print("\n=== Testing Timeout Handling ===")
        session = PowerShellSession()
        with session:
            try:
                # This should timeout
                session.execute("Start-Sleep -Seconds 10", timeout=2)
                self.fail("Expected timeout exception")
            except Exception as e:
                print(f"Got expected exception: {e}")
                assert "timeout" in str(e).lower() or "timed out" in str(e).lower()

    def test_rapid_command_sequence(self):
        """Test rapid command execution"""
        print("\n=== Testing Rapid Command Sequence ===")
        session = PowerShellSession()
        with session:
            for i in range(10):
                result = session.execute(f"Write-Output 'Command {i}'", timeout=5)
                print(f"Command {i}: {result}")
                assert f"Command {i}" in result

    def test_error_recovery(self):
        """Test recovery from command errors"""
        print("\n=== Testing Error Recovery ===")
        session = PowerShellSession()
        with session:
            # Execute a command that will fail
            try:
                session.execute("Get-Item NonExistentFile.txt", timeout=5)
            except Exception as e:
                print(f"Got expected error: {e}")

            # Session should still work after error
            result = session.execute("Write-Output 'Still working'", timeout=5)
            print(f"Recovery result: {result}")
            assert "Still working" in result

    def test_long_output_handling(self):
        """Test handling of commands with long output"""
        print("\n=== Testing Long Output Handling ===")
        session = PowerShellSession()
        with session:
            # Generate a lot of output
            result = session.execute("1..100 | ForEach-Object { Write-Output $_ }", timeout=10)
            print(f"Output length: {len(result)}")
            assert "100" in result

    def test_special_characters(self):
        """Test handling of special characters in commands"""
        print("\n=== Testing Special Characters ===")
        session = PowerShellSession()
        with session:
            result = session.execute("Write-Output 'Test: $var @array #comment'", timeout=5)
            print(f"Result: {result}")
            assert "Test:" in result

    def test_multiline_command(self):
        """Test execution of multiline commands"""
        print("\n=== Testing Multiline Command ===")
        session = PowerShellSession()
        with session:
            command = """
            $x = 1
            $y = 2
            Write-Output ($x + $y)
            """
            result = session.execute(command, timeout=5)
            print(f"Result: {result}")
            assert "3" in result

    def test_concurrent_sessions(self):
        """Test multiple concurrent PowerShell sessions"""
        print("\n=== Testing Concurrent Sessions ===")
        results = []

        def run_session(session_id):
            session = PowerShellSession()
            with session:
                result = session.execute(f"Write-Output 'Session {session_id}'", timeout=5)
                results.append(result)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_session, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print(f"Results: {results}")
        assert len(results) == 3

    def test_session_cleanup(self):
        """Test that sessions clean up properly"""
        print("\n=== Testing Session Cleanup ===")
        session = PowerShellSession()
        with session:
            session.execute("Write-Output 'Test'", timeout=5)
            # Session should be running
            assert session._process is not None
            assert session._process.poll() is None

        # After context exit, process should be terminated
        # Give it a moment to clean up
        time.sleep(0.5)
        assert session._process is None or session._process.poll() is not None

    def test_unicode_handling(self):
        """Test handling of unicode characters"""
        print("\n=== Testing Unicode Handling ===")
        session = PowerShellSession()
        with session:
            result = session.execute("Write-Output '你好世界'", timeout=5)
            print(f"Result: {result}")
            # Just verify it doesn't crash

    def test_environment_variables(self):
        """Test that environment variables work"""
        print("\n=== Testing Environment Variables ===")
        session = PowerShellSession()
        with session:
            session.execute("$env:TEST_VAR = 'test_value'", timeout=5)
            result = session.execute("Write-Output $env:TEST_VAR", timeout=5)
            print(f"Result: {result}")
            assert "test_value" in result

    def test_whitespace_impact(self):
        """Test impact of whitespace in commands"""
        print("\n=== Testing Whitespace Impact ===")
        session = PowerShellSession()
        with session:
            # Test with various whitespace patterns
            commands = [
                "Write-Output 'test'",
                "  Write-Output 'test'  ",
                "\nWrite-Output 'test'\n",
                "Write-Output    'test'",
            ]

            for cmd in commands:
                try:
                    result = session.execute(cmd, timeout=5)
                    print(f"Command: {repr(cmd)} -> Result: {result}")
                    assert "test" in result
                except Exception as e:
                    self.fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)