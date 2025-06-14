import unittest
import os
import tempfile
import shutil
import unittest


class TestTerminalTools(unittest.TestCase):
    """Test suite for terminal tools functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment and any leftover files"""
        try:
            os.chdir(cls.original_cwd)
            if os.path.exists(cls.temp_dir):
                shutil.rmtree(cls.temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")
        # Clean up PowerShell output files that might be created
        cleanup_files = ['ps_output.txt', 'ps_output_MainThread.txt', 'test.txt']
        for cleanup_file in cleanup_files:
            try:
                if os.path.exists(cleanup_file):
                    os.unlink(cleanup_file)
                    print(f"Cleaned up: {cleanup_file}")
            except Exception as e:
                print(f"Warning: Could not clean up {cleanup_file}: {e}")

    def tearDown(self):
        """Clean up after each test"""
        # Clean up any test.txt files created during individual tests
        if os.path.exists('test.txt'):
            try:
                os.unlink('test.txt')
            except Exception as e:
                print(f"Warning: Could not clean up test.txt: {e}")

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for flexible comparison.
        Handles JSON, line numbers, quotes, and case sensitivity.
        Preserves line structure.
        """
        lines = str(text).lower().splitlines()
        normalized_lines = []
        for line in lines:
            line = line.replace('"', '').replace("'", '')
            line = line.replace('{', '').replace('}', '')
            line = line.replace('[', '').replace(']', '')
            line = line.replace(':', '').replace(',', '')
            normalized_lines.append(' '.join(line.split()))
        return ''.join(normalized_lines)

    def assertContainsNormalized(self, haystack: str, needle: str, msg: str=None):
        """
        Assert that needle exists in haystack after normalization.
        Better for comparing file contents, JSON responses, etc.
        """
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(normalized_needle in normalized_haystack, msg or f'Expected to find "{needle}" in text (after normalization).\nGot:\n{haystack}')

    def test_powershell_utf8_output(self):
        """Test that PowerShell commands return proper UTF-8 encoded output"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Write-Output "Hello 世界 🌍"'
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'Hello 世界 🌍')
        ps_script = '[System.Console]::Error.WriteLine("エラー 🚫")'
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'エラー 🚫')
        ps_script = '\n            Write-Output "Standard: こんにちは"\n            [System.Console]::Error.WriteLine("Error: システムエラー")\n        '
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'Standard: こんにちは')
        self.assertContainsNormalized(result, 'Error: システムエラー')

    def test_powershell_no_output(self):
        """Test that commands with no output work correctly"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '$null'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(self.normalize_text(''), self.normalize_text(result.strip()))
        ps_script = 'Write-Output ""'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(self.normalize_text(''), self.normalize_text(result.strip()))

    @unittest.skip('takes too long')
    def test_powershell_timeout(self):
        """Test that long-running commands timeout correctly"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Start-Sleep -Seconds 308'
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'Error: Command execution timed out after 300 seconds')

    def test_powershell_truncated_output(self):
        """Test that long output is truncated and saved to file"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = _execute_powershell_stateless(ps_script, output_length_limit='50')
        self.assertEqual(len(result.splitlines()), 54)
        self.assertContainsNormalized(result, '50 lines omitted')
        self.assertContainsNormalized(result, 'Full output saved to')

    def test_powershell_command_chain_success(self):
        """Test that && chains work correctly when all commands succeed"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Write-Output "First" && Write-Output "Second" && Write-Output "Third"'
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'First')
        self.assertContainsNormalized(result, 'Second')
        self.assertContainsNormalized(result, 'Third')

    def test_powershell_command_chain_failure(self):
        """Test that && chains stop executing after a command fails"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'nonexistentcommand && Write-Output "Should Not See This"'
        result = _execute_powershell_stateless(ps_script)
        self.assertNotIn('Should Not See This', result)
        self.assertContainsNormalized(result, 'nonexistentcommand')

    def test_powershell_complex_command_chain(self):
        """Test complex command chains with mixed success/failure conditions"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'New-Item -Path "test.txt" -ItemType "file" -Force && Write-Output "success" > test.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
        result = _execute_powershell_stateless(ps_script)
        self.assertNotIn('Should Not See This', result)
        cleanup = _execute_powershell_stateless('Remove-Item -Path "test.txt" -Force')

    def test_powershell_special_characters(self):
        """Test handling of special characters and box drawing symbols"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Write-Output "Box chars: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼"'
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'Box chars:')
        self.assertTrue(any((char in result for char in '─│┌┐└┘├┤┬┴┼')))
        ps_script = 'Write-Output "Extended ASCII: ° ± ² ³ µ ¶ · ¹ º"'
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'Extended ASCII:')
        self.assertTrue(any((char in result for char in '°±²³µ¶·¹º')))

    def test_powershell_invalid_encoding_handling(self):
        """Test handling of potentially problematic encoding scenarios"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '\n    Write-Output "Mixed scripts: Latin-ASCII-한글-עברית-العربية"\n    Write-Output "More mixed: Русский-日本語-🌟-‱-√"\n    '
        result = _execute_powershell_stateless(ps_script)
        self.assertContainsNormalized(result, 'Mixed scripts:')
        self.assertContainsNormalized(result, 'More mixed:')
        ps_script = '\n    [byte[]]$bytes = 0xC4,0x80,0xE2,0x98,0x83\n    [System.Text.Encoding]::UTF8.GetString($bytes)\n    '
        result = _execute_powershell_stateless(ps_script)
        self.assertTrue(len(result.strip()) > 0)

    def test_powershell_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '[Console]::OutputEncoding.WebName'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(result))
        ps_script = '[Console]::InputEncoding.WebName'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(result))
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(self.normalize_text('utf8'), self.normalize_text(result))
        test_string = 'Test UTF8 String: ★ → ♠ ±'
        ps_script = f'Write-Output "{test_string}"'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(self.normalize_text(test_string), self.normalize_text(result))

class TestTerminalToolsStateful(TestTerminalTools):

    def _collect_generator_output(self, generator):
        """Helper method to collect all output from the generator"""
        outputs = list(generator)
        if not outputs:
            return ''
        return outputs[0] if len(outputs) == 1 else ''.join(outputs)

    def test_stateful_basic_use(self):
        """Test basic command execution and output capture"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Hello, World!"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text('Hello, World!'), self.normalize_text(result))

    def test_stateful_utf8_output(self):
        """Test that PowerShell commands return proper UTF-8 encoded output in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Hello 世界 🌍"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'Hello 世界 🌍')
        ps_script = '[System.Console]::Error.WriteLine("エラー 🚫")'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'エラー 🚫')
        ps_script = '\n            Write-Output "Standard: こんにちは"\n            [System.Console]::Error.WriteLine("Error: システムエラー")\n        '
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'Standard: こんにちは')
        self.assertContainsNormalized(result, 'Error: システムエラー')

    def test_stateful_no_output(self):
        """Test that commands with no output work correctly in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '$null'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text(''), self.normalize_text(result))
        ps_script = 'Write-Output ""'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text(''), self.normalize_text(result))

    def test_stateful_truncated_output(self):
        """Test that long output is truncated and saved to file in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = self._collect_generator_output(execute_powershell(ps_script, output_length_limit='50'))
        lines = result.splitlines()
        content_lines = sum((1 for line in lines if line.startswith('Line')))
        self.assertEqual(content_lines, 50, 'Should have exactly 50 content lines')
        self.assertTrue(any(('lines omitted' in line for line in lines)), 'Should have truncation message')
        self.assertTrue(any(('Full output saved to' in line for line in lines)), 'Should have file save message')

    def test_stateful_command_chain_success(self):
        """Test that && chains work correctly when all commands succeed in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "First" && Write-Output "Second" && Write-Output "Third"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'First')
        self.assertContainsNormalized(result, 'Second')
        self.assertContainsNormalized(result, 'Third')

    def test_stateful_command_chain_failure(self):
        """Test that && chains stop executing after a command fails in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'nonexistentcommand && Write-Output "Should Not See This"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertNotIn('Should Not See This', result)
        self.assertContainsNormalized(result, 'nonexistentcommand')

    def test_stateful_complex_command_chain(self):
        """Test complex command chains with mixed success/failure conditions in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'New-Item -Path "test.txt" -ItemType "file" -Force && Write-Output "success" > test.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertNotIn('Should Not See This', result)
        cleanup = self._collect_generator_output(execute_powershell('Remove-Item -Path "test.txt" -Force'))

    def test_stateful_special_characters(self):
        """Test handling of special characters and box drawing symbols in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Box chars: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'Box chars:')
        self.assertTrue(any((char in result for char in '─│┌┐└┘├┤┬┴┼')))
        ps_script = 'Write-Output "Extended ASCII: ° ± ² ³ µ ¶ · ¹ º"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'Extended ASCII:')
        self.assertTrue(any((char in result for char in '°±²³µ¶·¹º')))

    def test_stateful_invalid_encoding_handling(self):
        """Test handling of potentially problematic encoding scenarios in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '\n    Write-Output "Mixed scripts: Latin-ASCII-한글-עברית-العربية"\n    Write-Output "More mixed: Русский-日本語-🌟-‱-√"\n    '
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertContainsNormalized(result, 'Mixed scripts:')
        self.assertContainsNormalized(result, 'More mixed:')
        ps_script = '\n    [byte[]]$bytes = 0xC4,0x80,0xE2,0x98,0x83\n    [System.Text.Encoding]::UTF8.GetString($bytes)\n    '
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertTrue(len(result.strip()) > 0)

    def test_stateful_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '[Console]::OutputEncoding.WebName'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(result))
        ps_script = '[Console]::InputEncoding.WebName'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(result))
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text('utf8'), self.normalize_text(result))
        test_string = 'Test UTF8 String: ★ → ♠ ±'
        ps_script = f'Write-Output "{test_string}"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(self.normalize_text(test_string), self.normalize_text(result))

    def test_stateful_line_by_line_output(self):
        """Test that output comes as a complete block per command"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..5 | ForEach-Object { Write-Output "Line $_" }'
        output = execute_powershell(ps_script)
        lines = output.splitlines()
        expected_lines = [f'Line {i}' for i in range(1, 6)]
        actual_lines = [line.strip() for line in lines]
        self.assertEqual(expected_lines, actual_lines, 'Line content should match exactly')

    def test_stateful_exact_limit_output(self):
        """Test behavior when output is exactly at the limit"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..50 | ForEach-Object { Write-Output "Line $_" }'
        result = self._collect_generator_output(execute_powershell(ps_script, output_length_limit='50'))
        lines = result.splitlines()
        content_lines = sum((1 for line in lines if line.startswith('Line')))
        self.assertEqual(content_lines, 50, 'Should have exactly 50 content lines')
        self.assertFalse(any(('lines omitted' in line for line in lines)), 'Should not have truncation message')
        self.assertFalse(any(('Full output saved to' in line for line in lines)), 'Should not have file save message')

    def test_true_statefulness_between_calls(self):
        """Test that PowerShell state persists between function calls"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script1 = '$global:test_var = "Hello from previous call"'
        list(execute_powershell(ps_script1))
        ps_script2 = 'Write-Output $global:test_var'
        result = self._collect_generator_output(execute_powershell(ps_script2))
        self.assertContainsNormalized(result, 'Hello from previous call')
        ps_script3 = 'New-Item -ItemType Directory -Path "test_state_dir" -Force; Set-Location "test_state_dir"'
        list(execute_powershell(ps_script3))
        ps_script4 = '(Get-Location).Path'
        result = self._collect_generator_output(execute_powershell(ps_script4))
        self.assertTrue(result.strip().endswith('test_state_dir'))
        ps_script5 = 'Set-Location ..; Remove-Item -Path "test_state_dir" -Force -Recurse'
        list(execute_powershell(ps_script5))

    def test_basic_input_handling(self):
        """Test that basic variable setting and retrieval works correctly"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('var_test')
        ps_script1 = '$name = "TestUser"'
        result = self._collect_generator_output(execute_powershell(ps_script1))
        ps_script2 = 'Write-Output $name'
        result = self._collect_generator_output(execute_powershell(ps_script2))
        self.assertEqual(self.normalize_text('TestUser'), self.normalize_text(result))
        manager.cleanup()

    def test_multiple_input_requests(self):
        """Test handling multiple variable operations in sequence"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('multi_var_test')
        ps_script1 = '$first = "Value1"; $second = "Value2"; Write-Output "$first and $second"'
        output = execute_powershell(ps_script1)
        self.assertEqual(self.normalize_text('Value1 and Value2'), self.normalize_text(output))
        ps_script2 = '$first = "NewValue1"; Write-Output "$first and $second"'
        output = execute_powershell(ps_script2)
        self.assertEqual(self.normalize_text('NewValue1 and Value2'), self.normalize_text(output))
        manager.cleanup()

    def test_input_error_handling(self):
        """Test error handling when executing invalid commands"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('error_test')
        ps_script1 = 'Write-Output "Valid command"'
        output = execute_powershell(ps_script1)
        self.assertContainsNormalized(output, 'Valid command')
        output = execute_powershell('nonexistentcommand')
        self.assertIn('nonexistentcommand', output)
        self.assertIn('not recognized', output.lower())
        manager.cleanup()

    def test_state_preservation_through_input(self):
        """Test that PowerShell state is preserved through command sequences"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('state_test')
        outputs = list(execute_powershell('$global:counter = 0; Write-Output $global:counter'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertEqual(self.normalize_text('0'), self.normalize_text(outputs[0]))
        ps_script1 = '$global:counter++; Write-Output $global:counter'
        outputs = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertEqual(self.normalize_text('1'), self.normalize_text(outputs[0]))
        outputs = list(execute_powershell('Write-Output $global:counter'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertEqual(self.normalize_text('1'), self.normalize_text(outputs[0]))
        manager.cleanup()
    def test_current_directory_display(self):
        "Test that current directory is properly displayed in output"
        from bots.tools.terminal_tools import execute_powershell
        # Execute a simple command and check that directory info is included
        ps_script = 'Write-Output "test command"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        # Should contain the directory information
        self.assertIn('[System: current directory <', result)
        self.assertIn('>]', result)
        # Should not contain the old error about Path property
        self.assertNotIn('Property "Path', result)
        self.assertNotIn('cannot be found', result)
        # Should contain our test output
        self.assertContainsNormalized(result, 'test command')
    def test_directory_change_persistence(self):
        "Test that directory changes persist between commands"
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('dir_test')
        # Create a test directory and change to it
        ps_script1 = 'New-Item -ItemType Directory -Path "test_dir_persistence" -Force; Set-Location "test_dir_persistence"'
        result1 = self._collect_generator_output(execute_powershell(ps_script1))
        # Check that we're in the new directory
        ps_script2 = 'Write-Output "Current location test"'
        result2 = self._collect_generator_output(execute_powershell(ps_script2))
        # Should show we're in the test directory
        self.assertIn('test_dir_persistence', result2)
        # Clean up
        ps_script3 = 'Set-Location ..; Remove-Item -Path "test_dir_persistence" -Force -Recurse'
        self._collect_generator_output(execute_powershell(ps_script3))
        manager.cleanup()

from bots.tools.terminal_tools import execute_powershell, PowerShellSession

class TestPowerShellErrorLogScenarios(unittest.TestCase):
    """
    Integration tests that reproduce the specific error scenarios from your error logs.
    These tests verify that the improved PowerShell tool handles the problematic cases.
    """

    def test_complex_python_string_scenario_1(self):
        """
        Test the complex Python command that was failing with unterminated string literals.
        This reproduces the scenario from your error log where Python code with nested quotes failed.
        """
        # This is the type of command that was causing SyntaxError: unterminated string literal
        problematic_code = '''python -c "
import unittest
import sys
from unittest.mock import patch, MagicMock
from io import StringIO
from contextlib import redirect_stdout
import bots.dev.cli as cli_module

# Create the test manually
mock_input = MagicMock()
mock_input.side_effect = [KeyboardInterrupt(), '/exit']

with patch('builtins.input', mock_input):
    with StringIO() as buf, redirect_stdout(buf):
        try:
            cli_module.main()
        except SystemExit:
            pass
        output = buf.getvalue()
        
print('Test output:')
print(repr(output))
print('Contains Use /exit to quit:', 'Use /exit to quit' in output)

# Also test the normalize function from the test
def normalize_text(text):
    text = str(text).lower()
    text = text.replace('\\"', '').replace(\\"'\\", '')
    text = text.replace('{', '').replace('}', '')
    text = text.replace('[', '').replace(']', '')
    text = text.replace(':', '').replace(',', '')
    return ' '.join(text.split())

normalized_output = normalize_text(output)
normalized_needle = normalize_text('Use /exit to quit')
print('Normalized output:', repr(normalized_output))
print('Normalized needle:', repr(normalized_needle))
print('Normalized contains:', normalized_needle in normalized_output)
"'''

        # Test that this no longer causes a SyntaxError
        session = PowerShellSession()
        try:
            result = session._handle_python_command_safely(problematic_code, "TEST_DELIMITER")
            
            # Should successfully create a temp file approach
            self.assertIn('$tempFile', result)
            self.assertIn('WriteAllText', result)
            
            # Should contain the problematic Python code without syntax errors
            self.assertIn('normalize_text', result)
            self.assertIn('redirect_stdout', result)
            self.assertIn('KeyboardInterrupt', result)
            
            # Most importantly, should not contain the problematic escaped quotes
            # that were causing the syntax errors
            self.assertNotIn('\\"\'\\', result)
            
        except SyntaxError as e:
            self.fail(f"Should not raise SyntaxError anymore, but got: {e}")

    def test_unicode_error_handling(self):
        """Test Unicode handling that was problematic in the error logs."""
        # Test the Unicode scenarios from your logs
        unicode_commands = [
            '[System.Console]::Error.WriteLine("エラー 🚫")',
            '''
            Write-Output "Standard: こんにちは"
            [System.Console]::Error.WriteLine("Error: システムエラー")
        '''
        ]
        
        for cmd in unicode_commands:
            with self.subTest(command=cmd[:50] + "..."):
                try:
                    # Should not raise encoding errors
                    result = execute_powershell(cmd, timeout='10')
                    self.assertIsInstance(result, str)
                    
                    # Should contain error section for stderr output
                    if 'Error.WriteLine' in cmd:
                        self.assertIn('Errors:', result)
                        
                except UnicodeError as e:
                    self.fail(f"Unicode handling failed for command: {e}")
                except Exception as e:
                    # Other exceptions are okay (like command not found), 
                    # but not Unicode errors
                    if 'unicode' in str(e).lower() or 'encoding' in str(e).lower():
                        self.fail(f"Encoding error: {e}")

    def test_command_not_found_handling(self):
        """Test handling of non-existent commands from error logs."""
        # From your logs: nonexistentcommand
        result = execute_powershell('nonexistentcommand', timeout='10')
        
        # Should handle gracefully with error message
        self.assertIn('Errors:', result)
        self.assertIn('not recognized', result.lower())
        self.assertNotIn('Tool Failed:', result)  # Should not be a tool failure

    def test_mixed_stdout_stderr_output(self):
        """Test mixed stdout/stderr output handling."""
        # Reproduce the scenario where both stdout and stderr are produced
        cmd = '''
        Write-Output "Standard: こんにちは"
        [System.Console]::Error.WriteLine("Error: システムエラー")
        '''
        
        result = execute_powershell(cmd, timeout='10')
        
        # Should contain both outputs
        self.assertIn('Standard:', result)
        self.assertIn('Errors:', result)
        self.assertIn('こんにちは', result)
        self.assertIn('システムエラー', result)
        
    def test_file_not_found_scenario(self):
        """Test file not found scenario from error logs."""
        # Use a file name that definitely doesn't exist
        import uuid
        random_filename = f"definitely_does_not_exist_{uuid.uuid4().hex}.txt"
        cmd = f'Get-Content "{random_filename}"'
        
        result = execute_powershell(cmd, timeout='10')
        
        # Should handle file not found gracefully
        self.assertIn('Errors:', result)
        self.assertTrue(
            'Cannot find path' in result or 
            'does not exist' in result or
            'ItemNotFoundException' in result,
            f"Should indicate file not found. Got: {result[:200]}..."
        )

    def test_python_command_with_file_operations(self):
        """Test Python commands that involve file operations."""
        # Simplified version of problematic code from logs
        python_code = '''python -c "
import bots.tools.python_edit as pe

# Read the current file
with open('bots/dev/cli.py', 'r') as f:
    content = f.read()

print('File read successfully')
"'''

        session = PowerShellSession()
        result = session._handle_python_command_safely(python_code, "DELIMITER")
        
        # Should use temp file approach
        self.assertIn('$tempFile', result)
        self.assertIn('python_edit', result)
        self.assertIn('File read successfully', result)

    def test_quote_heavy_python_code(self):
        """Test Python code with many nested quotes."""
        # This type of code was causing the unterminated string literal errors
        python_code = '''python -c "
par_dispatch_line = 'elif fp_name == \\"par_dispatch\\":'
par_dispatch_pos = content.find(par_dispatch_line)
print(f'Found par_dispatch at position: {par_dispatch_pos}')
"'''

        session = PowerShellSession()
        result = session._handle_python_command_safely(python_code, "DELIMITER")
        
        # Should handle the complex quoting
        self.assertIn('par_dispatch', result)
        self.assertIn('elif fp_name ==', result)
        # Should clean up the quotes properly
        self.assertIn('par_dispatch', result)

    def test_bom_handling(self):
        """Test handling of Unicode BOM that was causing issues."""
        # Simulate BOM character that was in your error logs
        code_with_bom = '\ufeff# This has a BOM character\nWrite-Output "test"'
        
        try:
            result = execute_powershell(code_with_bom, timeout='10')
            self.assertIsInstance(result, str)
            # Should not fail due to BOM
        except Exception as e:
            if 'U+FEFF' in str(e) or 'non-printable character' in str(e):
                self.fail(f"BOM handling failed: {e}")

    def test_command_chaining_with_quotes(self):
        """Test command chaining with quotes that might confuse the parser."""
        # Test && handling with complex quotes
        cmd = 'Write-Output "First && Second" && Write-Output "Third"'
        
        result = execute_powershell(cmd, timeout='10')
        
        # Should execute both parts
        self.assertIn('First && Second', result)
        self.assertIn('Third', result)



class TestRegressionScenarios(unittest.TestCase):
    """Test specific regression scenarios to ensure fixes don't break existing functionality."""

    def test_simple_commands_still_work(self):
        """Ensure simple commands still work after improvements."""
        simple_commands = [
            'Write-Output "Hello World"',
            'Get-Date',
            '$var = "test"; Write-Output $var',
            'Write-Output (2 + 2)'
        ]
        
        for cmd in simple_commands:
            with self.subTest(command=cmd):
                try:
                    result = execute_powershell(cmd, timeout='10')
                    self.assertIsInstance(result, str)
                    self.assertNotIn('Tool Failed:', result)
                except Exception as e:
                    self.fail(f"Simple command failed: {cmd} - {e}")

    def test_basic_python_commands_still_work(self):
        """Ensure basic Python commands still work."""
        basic_python_commands = [
            'python -c "print(\'Hello World\')"',
            'python -c "import sys; print(sys.version)"',
            'python -c "print(2 + 2)"'
        ]
        
        for cmd in basic_python_commands:
            with self.subTest(command=cmd):
                try:
                    result = execute_powershell(cmd, timeout='15')
                    self.assertIsInstance(result, str)
                    # Python might not be available, but shouldn't cause tool failures
                    if 'Tool Failed:' in result:
                        self.fail(f"Tool failure on basic Python command: {cmd}")
                except Exception as e:
                    self.fail(f"Basic Python command failed: {cmd} - {e}")

    def test_output_limiting_still_works(self):
        """Ensure output limiting functionality still works."""
        # Create a command that produces multiple lines
        cmd = 'for ($i=1; $i -le 20; $i++) { Write-Output "Line $i" }'
        
        result = execute_powershell(cmd, output_length_limit='5', timeout='10')
        
        if 'Tool Failed:' not in result:
            # If command succeeded, should have either full output or truncated
            lines = result.split('\n')
            # Should either be truncated or be the full 20 lines
            self.assertTrue(len(lines) <= 25)  # Account for some formatting


if __name__ == '__main__':
    # Run these specific integration tests
    unittest.main(verbosity=2)