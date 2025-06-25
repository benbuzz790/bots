import os
import shutil
import tempfile
import threading
import time
import unittest

from bots.tools.terminal_tools import PowerShellManager, PowerShellSession, execute_powershell


class TestPowerShellProductionEdgeCases(unittest.TestCase):
    """Test edge cases that might occur in production but not in isolated tests"""

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

    def test_stateful_session_reuse_with_here_strings(self):
        """Test here-strings in a reused stateful session (production pattern)"""
        print("\n=== Testing Stateful Session Reuse ===")

        # This mimics how the bot might reuse sessions
        manager = PowerShellManager.get_instance("test_bot")

        try:
            # First command - simple
            print("\n--- Command 1: Simple ---")
            result1 = execute_powershell("Write-Output 'Warming up session'")
            print(f"Result 1: {result1}")

            # Second command - here-string
            print("\n--- Command 2: Here-string ---")
            here_string_cmd = """@'
Hello from reused session
'@"""

            start_time = time.time()
            try:
                result2 = execute_powershell(here_string_cmd, timeout="10")
                elapsed = time.time() - start_time
                print(f"✅ Here-string in reused session completed in {elapsed:.2f}s")
                print(f"Result 2: {result2}")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Here-string in reused session failed after {elapsed:.2f}s: {e}")

            # Third command - complex here-string
            print("\n--- Command 3: Complex here-string ---")
            complex_cmd = """@'
Line 1
Line 2 with "quotes"
Line 3 with 'apostrophes'
'@ | Out-File complex_test.txt"""

            start_time = time.time()
            try:
                execute_powershell(complex_cmd, timeout="10")
                elapsed = time.time() - start_time
                print(f"✅ Complex here-string completed in {elapsed:.2f}s")

                if os.path.exists("complex_test.txt"):
                    print("✅ File created in reused session")
                else:
                    print("❌ File not created in reused session")

            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Complex here-string failed after {elapsed:.2f}s: {e}")

        finally:
            manager.cleanup()

    def test_rapid_succession_commands(self):
        """Test rapid command execution (as might happen in production)"""
        print("\n=== Testing Rapid Succession Commands ===")

        commands = [
            "Write-Output 'Command 1'",
            "@'\nRapid test\n'@",
            "Get-Date",
            "@'\nAnother here-string\n'@ | Out-File rapid.txt",
            "Write-Output 'Final command'",
        ]

        results = []
        errors = []

        for i, cmd in enumerate(commands):
            print(f"\n--- Rapid command {i+1} ---")
            start_time = time.time()

            try:
                result = execute_powershell(cmd, timeout="5")
                elapsed = time.time() - start_time
                print(f"✅ Command {i+1} completed in {elapsed:.2f}s")
                results.append(result)
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ Command {i+1} failed after {elapsed:.2f}s: {e}")
                errors.append((i, e))

        print(f"\nSummary: {len(results)} succeeded, {len(errors)} failed")
        if errors:
            print("Failed commands:", [i for i, _ in errors])

    def test_here_string_after_error(self):
        """Test here-string execution after previous command errors"""
        print("\n=== Testing Here-String After Error ===")

        # First, cause an error
        print("\n--- Step 1: Cause an error ---")
        error_cmd = "Get-Content 'nonexistent_file_12345.txt'"

        try:
            execute_powershell(error_cmd, timeout="5")
            print("Error command completed (with error in output)")
        except Exception as e:
            print(f"Error command raised exception: {e}")

        # Now try a here-string
        print("\n--- Step 2: Here-string after error ---")
        here_string_cmd = """@'
Testing after error
Multiple lines
'@"""

        start_time = time.time()
        try:
            result2 = execute_powershell(here_string_cmd, timeout="10")
            elapsed = time.time() - start_time
            print(f"✅ Here-string after error completed in {elapsed:.2f}s")

            if "Testing after error" in result2:
                print("✅ Here-string content correct")
            else:
                print("❌ Here-string content missing")

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Here-string after error failed after {elapsed:.2f}s: {e}")

    def test_here_string_with_powershell_special_vars(self):
        """Test here-strings containing PowerShell special variables"""
        print("\n=== Testing Here-Strings with PS Special Vars ===")

        test_cases = [
            ("Dollar signs", "@'\n$PSVersionTable\n$ErrorActionPreference\n'@"),
            ("Backticks", "@'\nLine 1`nLine 2`tTabbed\n'@"),
            ("Array notation", "@'\n$array[0]\n@{key='value'}\n'@"),
            ("Escape sequences", "@'\n`$escaped `@ symbols\n'@"),
        ]

        for name, cmd in test_cases:
            print(f"\n--- Testing: {name} ---")
            start_time = time.time()

            try:
                result = execute_powershell(cmd, timeout="5")
                elapsed = time.time() - start_time
                print(f"✅ {name} completed in {elapsed:.2f}s")
                print(f"Result preview: {repr(result[:100])}")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {name} failed after {elapsed:.2f}s: {e}")

    def test_here_string_with_bom_removal_interaction(self):
        """Test if BOM removal post-processing affects here-strings"""
        print("\n=== Testing BOM Removal Interaction ===")

        # Create a here-string that will trigger file operations
        cmd = """@'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
print("Testing BOM interaction")
'@ | Out-File -FilePath test_bom.py -Encoding UTF8"""

        start_time = time.time()
        try:
            result = execute_powershell(cmd, timeout="10")
            elapsed = time.time() - start_time
            print(f"✅ Command completed in {elapsed:.2f}s")

            # Check for BOM removal messages
            if "[BOM]" in result:
                print("✅ BOM removal was triggered")

            # Check file creation
            if os.path.exists("test_bom.py"):
                print("✅ File created")
                with open("test_bom.py", "rb") as f:
                    first_bytes = f.read(3)
                if first_bytes == b"\xef\xbb\xbf":
                    print("⚠️  File still has BOM")
                else:
                    print("✅ No BOM in file")
            else:
                print("❌ File not created")

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Failed after {elapsed:.2f}s: {e}")

    def test_powershell_version_and_environment(self):
        """Check PowerShell version and environment settings"""
        print("\n=== PowerShell Environment Check ===")

        env_commands = [
            ("PS Version", "$PSVersionTable.PSVersion"),
            ("Execution Policy", "Get-ExecutionPolicy"),
            ("Error Preference", "$ErrorActionPreference"),
            ("Progress Preference", "$ProgressPreference"),
            ("Encoding Settings", "$OutputEncoding"),
            ("Current Provider", "(Get-Location).Provider.Name"),
        ]

        for name, cmd in env_commands:
            try:
                result = execute_powershell(cmd, timeout="5")
                print(f"{name}: {result.strip()}")
            except Exception as e:
                print(f"{name}: Failed - {e}")

    def test_here_string_stress_test(self):
        """Stress test with many here-strings"""
        print("\n=== Here-String Stress Test ===")

        success_count = 0
        fail_count = 0
        timeout_count = 0

        for i in range(10):
            content = f"Stress test iteration {i}\n" * 5
            cmd = f"@'\n{content}'@"

            start_time = time.time()
            try:
                result = execute_powershell(cmd, timeout="3")
                elapsed = time.time() - start_time

                if f"iteration {i}" in result:
                    success_count += 1
                    print(f"✅ Iteration {i} succeeded in {elapsed:.2f}s")
                else:
                    fail_count += 1
                    print(f"⚠️  Iteration {i} wrong output in {elapsed:.2f}s")

            except TimeoutError:
                timeout_count += 1
                elapsed = time.time() - start_time
                print(f"❌ Iteration {i} timed out after {elapsed:.2f}s")
            except Exception as e:
                fail_count += 1
                print(f"❌ Iteration {i} failed: {e}")

        print(f"\nStress test results: {success_count} success, {fail_count} failed, {timeout_count} timeouts")

        if timeout_count > 0:
            print(f"⚠️  {timeout_count} timeouts suggest intermittent issue")

    def test_here_string_with_thread_contention(self):
        """Test here-strings under thread contention"""
        print("\n=== Testing Thread Contention ===")

        # Simulate multiple threads using PowerShell
        results = {}
        errors = {}

        def run_here_string(thread_id):
            cmd = f"@'\nThread {thread_id} here-string\n'@"
            try:
                result = execute_powershell(cmd, timeout="5")
                results[thread_id] = "success" if f"Thread {thread_id}" in result else "wrong output"
            except Exception as e:
                errors[thread_id] = str(e)

        threads = []
        for i in range(3):
            t = threading.Thread(target=run_here_string, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print(f"Results: {results}")
        print(f"Errors: {errors}")

        if errors:
            print("⚠️  Thread contention causes issues")

    def test_modified_wrap_code_safely(self):
        """Test with a modified _wrap_code_safely that might fix the issue"""
        print("\n=== Testing Modified Wrapper ===")

        class FixedPowerShellSession(PowerShellSession):
            def _wrap_code_safely(self, code: str, delimiter: str) -> str:
                """Fixed wrapper without $LASTOUTPUT"""
                # Much simpler wrapper
                return f"""
try {{
    {code}
}} catch {{
    Write-Host "ERROR: $_"
}}
Write-Output '{delimiter}'
"""

        session = FixedPowerShellSession()
        with session:
            # Test the problematic here-string with fixed wrapper
            cmd = """@'
from bots.tools.python_edit import python_edit
sample_code = '''#!/usr/bin/env python3
import math
'''
'@ | Out-File -FilePath test_fixed.py -Encoding UTF8"""

            start_time = time.time()
            try:
                session.execute(cmd, timeout=5)
                elapsed = time.time() - start_time
                print(f"✅ Fixed wrapper completed in {elapsed:.2f}s")

                if os.path.exists("test_fixed.py"):
                    print("✅ File created with fixed wrapper")
                    with open("test_fixed.py", "r") as f:
                        content = f.read()
                    if "python_edit" in content:
                        print("✅ Content correct")
                else:
                    print("❌ File not created with fixed wrapper")

            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Fixed wrapper still times out after {elapsed:.2f}s")
                print("Issue might be deeper than wrapper")
            except Exception as e:
                print(f"❌ Fixed wrapper failed: {e}")

    def test_here_string_line_endings(self):
        """Test different line ending combinations in here-strings"""
        print("\n=== Testing Line Endings in Here-Strings ===")

        line_endings = [
            ("LF", "@'\nLine1\nLine2\n'@"),
            ("CRLF", "@'\r\nLine1\r\nLine2\r\n'@"),
            ("Mixed", "@'\nLine1\r\nLine2\n'@"),
            ("CR only", "@'\rLine1\rLine2\r'@"),
        ]

        for name, cmd in line_endings:
            print(f"\n--- Testing {name} line endings ---")
            start_time = time.time()

            try:
                result = execute_powershell(cmd, timeout="5")
                elapsed = time.time() - start_time
                print(f"✅ {name} completed in {elapsed:.2f}s")

                # Check if content is preserved
                if "Line1" in result and "Line2" in result:
                    print("✅ Content preserved")
                else:
                    print("⚠️  Content might be corrupted")

            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {name} failed after {elapsed:.2f}s: {e}")

    def test_here_string_with_very_long_lines(self):
        """Test here-strings with very long lines"""
        print("\n=== Testing Very Long Lines ===")

        # Test increasingly long lines
        lengths = [100, 1000, 5000, 10000]

        for length in lengths:
            print(f"\n--- Testing {length} character line ---")
            long_line = "x" * length
            cmd = f"@'\n{long_line}\n'@"

            start_time = time.time()
            try:
                result = execute_powershell(cmd, timeout="5")
                elapsed = time.time() - start_time

                if long_line in result:
                    print(f"✅ {length} chars completed in {elapsed:.2f}s")
                else:
                    print(f"⚠️  {length} chars output truncated in {elapsed:.2f}s")

            except TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ {length} chars timed out after {elapsed:.2f}s")
                print(f"Long lines might be problematic at {length}+ characters")
                break
            except Exception as e:
                print(f"❌ {length} chars failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
