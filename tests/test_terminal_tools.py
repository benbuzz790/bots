import unittest
import datetime as DT
import os
import sys
import traceback
import concurrent
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout
from datetime import datetime

class TestTerminalTools(unittest.TestCase):

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
        """Test that output comes as a complete block"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '\n    1..5 | ForEach-Object {\n        Write-Output "Line $_"\n        Start-Sleep -Milliseconds 100\n    }\n    '
        outputs = list(execute_powershell(ps_script))
        self.assertEqual(1, len(outputs), 'Should yield output exactly once')
        lines = outputs[0].splitlines()
        expected_lines = [f'Line {i}' for i in range(1, 6)]
        actual_lines = [line.strip() for line in lines if line.strip().startswith('Line')]
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
        """Test that basic Read-Host input requests work correctly"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('input_test')
        ps_script1 = '$name = Read-Host "Enter your name"'
        result = execute_powershell(ps_script1)
        self.assertContainsNormalized(result, 'Enter your name')
        ps_script2 = 'TestUser'
        result = execute_powershell(ps_script2)
        ps_script3 = 'Write-Output $name'
        result = execute_powershell(ps_script3)
        self.assertEqual(self.normalize_text('TestUser'), self.normalize_text(result))
        manager.cleanup()

    def test_multiple_input_requests(self):
        """Test handling multiple input requests in sequence"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('multi_input_test')
        ps_script1 = '\n    $first = Read-Host "Enter first value"\n    $second = Read-Host "Enter second value"\n    '
        outputs = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertContainsNormalized(outputs[0], 'Enter first value')
        outputs = list(execute_powershell('Value1'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertContainsNormalized(outputs[0], 'Enter second value')
        outputs = list(execute_powershell('Value2'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        ps_script4 = 'Write-Output "$first and $second"'
        outputs = list(execute_powershell(ps_script4))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertEqual(self.normalize_text('Value1 and Value2'), self.normalize_text(outputs[0]))
        manager.cleanup()

    def test_input_error_handling(self):
        """Test error handling when providing input incorrectly"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('error_input_test')
        ps_script1 = 'Write-Output "No input needed"'
        outputs = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertEqual(self.normalize_text('No input needed'), self.normalize_text(outputs[0]))
        try:
            list(execute_powershell('Unexpected input'))
            self.fail('Should have raised an exception')
        except Exception as e:
            self.assertIn('not waiting for input', str(e))
        manager.cleanup()

    def test_state_preservation_through_input(self):
        """Test that PowerShell state is preserved through input sequences"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('state_input_test')
        outputs = list(execute_powershell('$global:counter = 0'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        ps_script1 = '\n    $global:counter++\n    $response = Read-Host "Counter is $global:counter, continue?"\n    $global:counter++\n    Write-Output "Counter is now $global:counter"\n    '
        outputs = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertContainsNormalized(outputs[0], 'Counter is 1, continue?')
        outputs = list(execute_powershell('yes'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertContainsNormalized(outputs[0], 'Counter is now 2')
        outputs = list(execute_powershell('Write-Output $global:counter'))
        self.assertEqual(1, len(outputs), 'Should get exactly one output')
        self.assertEqual(self.normalize_text('2'), self.normalize_text(outputs[0]))
        manager.cleanup()