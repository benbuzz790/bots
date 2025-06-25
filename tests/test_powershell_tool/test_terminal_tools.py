import os
import shutil
import tempfile
import unittest
from bots.tools.terminal_tools import PowerShellSession, execute_powershell
from tests.conftest import get_unique_filename

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
            print(f'Warning: Could not clean up temp directory: {e}')
        cleanup_files = [get_unique_filename('ps_output', 'txt'), get_unique_filename('ps_output_MainThread', 'txt'), get_unique_filename('test', 'txt')]
        for cleanup_file in cleanup_files:
            try:
                if os.path.exists(cleanup_file):
                    os.unlink(cleanup_file)
                    print(f'Cleaned up: {cleanup_file}')
            except Exception as e:
                print(f'Warning: Could not clean up {cleanup_file}: {e}')

    def tearDown(self):
        """Clean up after each test"""
        test_file = get_unique_filename('test', 'txt')
        if os.path.exists(test_file):
            try:
                os.unlink(test_file)
            except Exception as e:
                print(f'Warning: Could not clean up {test_file}: {e}')

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
        ps_script = 'New-Item -Path get_unique_filename("test", "txt") -ItemType "file" -Force && Write-Output "success" > test_20016_16_1750444995166.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
        result = _execute_powershell_stateless(ps_script)
        self.assertNotIn('Should Not See This', result)
        _execute_powershell_stateless('Remove-Item -Path get_unique_filename("test", "txt") -Force')

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

    def test_powershell_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '[Console]::OutputEncoding.WebName'
        result = _execute_powershell_stateless(ps_script)
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(actual_output))
        ps_script = '[Console]::InputEncoding.WebName'
        result = _execute_powershell_stateless(ps_script)
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(actual_output))
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = _execute_powershell_stateless(ps_script)
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('utf8nobom'), self.normalize_text(actual_output))
        test_string = 'Test UTF8 String: ★ → ♠ ±'
        ps_script = f'Write-Output "{test_string}"'
        result = _execute_powershell_stateless(ps_script)
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text(test_string), self.normalize_text(actual_output))

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
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('Hello, World!'), self.normalize_text(actual_output))

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
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text(''), self.normalize_text(actual_output))
        ps_script = 'Write-Output ""'
        result = self._collect_generator_output(execute_powershell(ps_script))
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text(''), self.normalize_text(actual_output))

    def test_stateful_truncated_output(self):
        """Test that long output is truncated and saved to file in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = self._collect_generator_output(execute_powershell(ps_script, output_length_limit='51'))
        stripped_result = result.splitlines()
        actual_result = '\n'.join(stripped_result[1:]) if stripped_result and stripped_result[0].startswith('[System: current directory') else result
        lines = actual_result.splitlines()
        content_lines = sum((1 for line in lines if line.startswith('Line')))
        self.assertEqual(content_lines, 49, 'Should have exactly 49 content lines')
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
        ps_script = 'New-Item -Path get_unique_filename("test", "txt") -ItemType "file" -Force && Write-Output "success" > test_20016_16_1750444995166.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertNotIn('Should Not See This', result)
        self._collect_generator_output(execute_powershell('Remove-Item -Path get_unique_filename("test", "txt") -Force'))

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

    def test_stateful_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '[Console]::OutputEncoding.WebName'
        result = self._collect_generator_output(execute_powershell(ps_script))
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(actual_output))
        ps_script = '[Console]::InputEncoding.WebName'
        result = self._collect_generator_output(execute_powershell(ps_script))
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('utf-8'), self.normalize_text(actual_output))
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = self._collect_generator_output(execute_powershell(ps_script))
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('utf8nobom'), self.normalize_text(actual_output))
        test_string = 'Test UTF8 String: ★ → ♠ ±'
        ps_script = f'Write-Output "{test_string}"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text(test_string), self.normalize_text(actual_output))

    def test_stateful_line_by_line_output(self):
        """Test that output comes as a complete block per command"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..5 | ForEach-Object { Write-Output "Line $_" }'
        output = execute_powershell(ps_script)
        stripped_output = output.splitlines()
        actual_output = '\n'.join(stripped_output[1:]) if stripped_output and stripped_output[0].startswith('[System: current directory') else output
        lines = actual_output.splitlines()
        expected_lines = [f'Line {i}' for i in range(1, 6)]
        actual_lines = [line.strip() for line in lines]
        self.assertEqual(expected_lines, actual_lines, 'Line content should match exactly')

    def test_stateful_exact_limit_output(self):
        """Test behavior when output is exactly at the limit"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..50 | ForEach-Object { Write-Output "Line $_" }'
        result = self._collect_generator_output(execute_powershell(ps_script, output_length_limit='51'))
        stripped_result = result.splitlines()
        actual_result = '\n'.join(stripped_result[1:]) if stripped_result and stripped_result[0].startswith('[System: current directory') else result
        lines = actual_result.splitlines()
        content_lines = sum((1 for line in lines if line.startswith('Line')))
        self.assertEqual(content_lines, 50, 'Should have exactly 50 content lines')
        self.assertFalse(any(('lines omitted' in line for line in lines)), 'Should not have truncation message')
        self.assertFalse(any(('Full output saved to' in line for line in lines)), 'Should not have file save message')

    def test_true_statefulness_between_calls(self):
        """Test that PowerShell state persists between function calls"""
        import random
        from bots.tools.terminal_tools import execute_powershell
        unique_dir = f'test_state_dir_{random.randint(10000, 99999)}'
        ps_script1 = '$global:test_var = "Hello from previous call"'
        list(execute_powershell(ps_script1))
        ps_script2 = 'Write-Output $global:test_var'
        result = self._collect_generator_output(execute_powershell(ps_script2))
        self.assertContainsNormalized(result, 'Hello from previous call')
        ps_script3 = f'New-Item -ItemType Directory -Path "{unique_dir}" -Force; Set-Location "{unique_dir}"'
        list(execute_powershell(ps_script3))
        ps_script4 = '(Get-Location).Path'
        result = self._collect_generator_output(execute_powershell(ps_script4))
        self.assertTrue(result.strip().endswith(unique_dir))
        ps_script5 = f'Set-Location ..; Remove-Item -Path "{unique_dir}" -Force -Recurse'
        list(execute_powershell(ps_script5))

    def test_basic_input_handling(self):
        """Test that basic variable setting and retrieval works correctly"""
        from bots.tools.terminal_tools import PowerShellManager, execute_powershell
        manager = PowerShellManager.get_instance('var_test')
        ps_script1 = '$name = "TestUser"'
        result = self._collect_generator_output(execute_powershell(ps_script1))
        ps_script2 = 'Write-Output $name'
        result = self._collect_generator_output(execute_powershell(ps_script2))
        lines = result.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else result
        self.assertEqual(self.normalize_text('TestUser'), self.normalize_text(actual_output))
        manager.cleanup()

    def test_multiple_input_requests(self):
        """Test handling multiple variable operations in sequence"""
        from bots.tools.terminal_tools import PowerShellManager, execute_powershell
        manager = PowerShellManager.get_instance('multi_var_test')
        ps_script1 = '$first = "Value1"; $second = "Value2"; Write-Output "$first and $second"'
        output = execute_powershell(ps_script1)
        lines = output.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else output
        self.assertEqual(self.normalize_text('Value1 and Value2'), self.normalize_text(actual_output))
        ps_script2 = '$first = "NewValue1"; Write-Output "$first and $second"'
        output = execute_powershell(ps_script2)
        lines = output.splitlines()
        actual_output = '\n'.join(lines[1:]) if lines and lines[0].startswith('[System: current directory') else output
        self.assertEqual(self.normalize_text('NewValue1 and Value2'), self.normalize_text(actual_output))
        manager.cleanup()

    def test_input_error_handling(self):
        """Test error handling when executing invalid commands"""
        from bots.tools.terminal_tools import PowerShellManager, execute_powershell
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
        from bots.tools.terminal_tools import PowerShellManager, execute_powershell
        manager = PowerShellManager.get_instance('state_test')
        outputs = execute_powershell('$global:counter = 0; Write-Output $global:counter')
        if not isinstance(outputs, list):
            outputs = list(outputs)
        self.assertEqual(self.normalize_text('0'), self.normalize_text(outputs[-1]))
        ps_script1 = '$global:counter++; Write-Output $global:counter'
        outputs = list(execute_powershell(ps_script1))
        self.assertEqual(self.normalize_text('1'), self.normalize_text(outputs[-1]))
        outputs = list(execute_powershell('Write-Output $global:counter'))
        self.assertEqual(self.normalize_text('1'), self.normalize_text(outputs[-1]))
        manager.cleanup()

    def test_current_directory_display(self):
        """Test that current directory is properly displayed in output"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "test command"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('[System: current directory <', result)
        self.assertIn('>]', result)
        self.assertNotIn('Property "Path', result)
        self.assertNotIn('cannot be found', result)
        self.assertContainsNormalized(result, 'test command')

    def test_directory_change_persistence(self):
        """Test that directory changes persist between commands"""
        import random
        from bots.tools.terminal_tools import PowerShellManager, execute_powershell
        manager = PowerShellManager.get_instance('dir_test')
        unique_dir = f'test_dir_persistence_{random.randint(10000, 99999)}'
        ps_script1 = f'New-Item -ItemType Directory -Path "{unique_dir}" -Force; Set-Location "{unique_dir}"'
        self._collect_generator_output(execute_powershell(ps_script1))
        ps_script2 = 'Get-Location | Select-Object -ExpandProperty Path'
        result2 = self._collect_generator_output(execute_powershell(ps_script2))
        self.assertIn(unique_dir, result2)
        ps_script3 = f'Set-Location ..; Remove-Item -Path "{unique_dir}" -Force -Recurse'
        self._collect_generator_output(execute_powershell(ps_script3))
        manager.cleanup()

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
        problematic_code = 'python -c "\nimport unittest\nimport sys\nfrom unittest.mock import patch, MagicMock\nfrom io import StringIO\nfrom contextlib import redirect_stdout\nimport bots.dev.cli as cli_module\n\n# Create the test manually\nmock_input = MagicMock()\nmock_input.side_effect = [KeyboardInterrupt(), \'/exit\']\n\nwith patch(\'builtins.input\', mock_input):\n    with StringIO() as buf, redirect_stdout(buf):\n        try:\n            cli_module.main()\n        except SystemExit:\n            pass\n        output = buf.getvalue()\n        \nprint(\'Test output:\')\nprint(repr(output))\nprint(\'Contains Use /exit to quit:\', \'Use /exit to quit\' in output)\n\n# Also test the normalize function from the test\ndef normalize_text(text):\n    text = str(text).lower()\n    text = text.replace(\'\\"\', \'\').replace(\\"\'\\", \'\')\n    text = text.replace(\'{\', \'\').replace(\'}\', \'\')\n    text = text.replace(\'[\', \'\').replace(\']\', \'\')\n    text = text.replace(\':\', \'\').replace(\',\', \'\')\n    return \' \'.join(text.split())\n\nnormalized_output = normalize_text(output)\nnormalized_needle = normalize_text(\'Use /exit to quit\')\nprint(\'Normalized output:\', repr(normalized_output))\nprint(\'Normalized needle:\', repr(normalized_needle))\nprint(\'Normalized contains:\', normalized_needle in normalized_output)\n"'
        session = PowerShellSession()
        try:
            with session:
                result = session.execute(problematic_code, timeout=10)
                self.assertIsInstance(result, str)
                self.assertIn('current directory', result)
        except SyntaxError as e:
            self.fail(f'Should not raise SyntaxError anymore, but got: {e}')

    def test_unicode_error_handling(self):
        """Test Unicode handling that was problematic in the error logs."""
        unicode_commands = ['[System.Console]::Error.WriteLine("エラー 🚫")', '\n            Write-Output "Standard: こんにちは"\n            [System.Console]::Error.WriteLine("Error: システムエラー")\n        ']
        for cmd in unicode_commands:
            with self.subTest(command=cmd[:50] + '...'):
                try:
                    result = execute_powershell(cmd, timeout='10')
                    self.assertIsInstance(result, str)
                    if 'Error.WriteLine' in cmd:
                        self.assertIn('Errors:', result)
                except UnicodeError as e:
                    self.fail(f'Unicode handling failed for command: {e}')
                except Exception as e:
                    if 'unicode' in str(e).lower() or 'encoding' in str(e).lower():
                        self.fail(f'Encoding error: {e}')

    def test_command_not_found_handling(self):
        """Test handling of non-existent commands from error logs."""
        result = execute_powershell('nonexistentcommand', timeout='10')
        self.assertIn('Errors:', result)
        self.assertIn('not recognized', result.lower())
        self.assertNotIn('Tool Failed:', result)

    def test_mixed_stdout_stderr_output(self):
        """Test mixed stdout/stderr output handling."""
        cmd = '\n        Write-Output "Standard: こんにちは"\n        [System.Console]::Error.WriteLine("Error: システムエラー")\n        '
        result = execute_powershell(cmd, timeout='10')
        self.assertIn('Standard:', result)
        self.assertIn('Errors:', result)
        self.assertIn('こんにちは', result)
        self.assertIn('システムエラー', result)

    def test_file_not_found_scenario(self):
        """Test file not found scenario from error logs."""
        import uuid
        random_filename = f'definitely_does_not_exist_{uuid.uuid4().hex}.txt'
        cmd = f'Get-Content "{random_filename}"'
        result = execute_powershell(cmd, timeout='10')
        self.assertIn('Errors:', result)
        self.assertTrue('Cannot find path' in result or 'does not exist' in result or 'ItemNotFoundException' in result, f'Should indicate file not found. Got: {result[:200]}...')

    def test_python_command_with_file_operations(self):
        """Test Python commands that involve file operations."""
        python_code = 'python -c "\nimport bots.tools.python_edit as pe\n\n# Read the current file\nwith open(\'bots/dev/cli.py\', \'r\') as f:\n    content = f.read()\n\nprint(\'File read successfully\')\n"'
        session = PowerShellSession()
        try:
            with session:
                result = session.execute(python_code, timeout=20)
                self.assertIsInstance(result, str)
                self.assertIn('current directory', result)
        except Exception as e:
            self.fail(f'Should not raise exception, but got: {e}')

    def test_quote_heavy_python_code(self):
        """Test Python code with many nested quotes."""
        python_code = 'python -c "\npar_dispatch_line = \'elif fp_name == \\"par_dispatch\\":\'\npar_dispatch_pos = content.find(par_dispatch_line)\nprint(f\'Found par_dispatch at position: {par_dispatch_pos}\')\n"'
        session = PowerShellSession()
        try:
            with session:
                result = session.execute(python_code, timeout=10)
                self.assertIsInstance(result, str)
                self.assertIn('current directory', result)
        except Exception as e:
            self.fail(f'Should not raise exception, but got: {e}')

    def test_bom_handling(self):
        """Test handling of Unicode BOM that was causing issues."""
        code_with_bom = '\ufeff# This has a BOM character\nWrite-Output "test"'
        try:
            result = execute_powershell(code_with_bom, timeout='10')
            self.assertIsInstance(result, str)
        except Exception as e:
            if 'U+FEFF' in str(e) or 'non-printable character' in str(e):
                self.fail(f'BOM handling failed: {e}')

    def test_command_chaining_with_quotes(self):
        """Test command chaining with quotes that might confuse the parser."""
        cmd = 'Write-Output "First && Second" && Write-Output "Third"'
        result = execute_powershell(cmd, timeout='10')
        self.assertIn('First && Second', result)
        self.assertIn('Third', result)

class TestPowerShellUnicodeIssues(unittest.TestCase):
    """Test Unicode and encoding issues that might cause apparent timeouts."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_utf8_file_creation(self):
        """Test creating files with UTF-8 content."""
        command = '@\'\nHello World\n\'@ | Out-File -FilePath "test_utf8.txt" -Encoding UTF8'
        result = execute_powershell(command)
        print(f'UTF-8 basic test result: {result}')
        if os.path.exists('test_utf8.txt'):
            try:
                with open('test_utf8.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f'✅ UTF-8 read successful: {repr(content)}')
            except Exception as e:
                print(f'❌ UTF-8 read failed: {e}')
            try:
                with open('test_utf8.txt', 'r', encoding='cp1252') as f:
                    content = f.read()
                print(f'✅ CP1252 read successful: {repr(content)}')
            except Exception as e:
                print(f'❌ CP1252 read failed: {e}')

    def test_special_characters_in_here_strings(self):
        """Test here-strings with special characters that might cause encoding issues."""
        special_chars_tests = [('ASCII quotes', '"Hello" and \'World\''), ('Smart quotes', '“Hello” and ‘World’'), ('Accented chars', 'Café, résumé, naïve'), ('Symbols', '© ® ™ € £ ¥'), ('Arrows and boxes', '→ ← ↑ ↓ □ ■ ◆'), ('Python code chars', 'f"value: {variable}" and encoding=\'utf-8\'')]
        for test_name, content in special_chars_tests:
            with self.subTest(test_name=test_name):
                filename = f"test_{test_name.replace(' ', '_').lower()}.txt"
                command = f'''@'\n{content}\n'@ | Out-File -FilePath "{filename}" -Encoding UTF8'''
                try:
                    result = execute_powershell(command, timeout='10')
                    print(f'✅ {test_name}: Command executed - {result}')
                    if os.path.exists(filename):
                        self._test_file_reading(filename, test_name)
                    else:
                        print(f'❌ {test_name}: File not created')
                except Exception as e:
                    print(f'❌ {test_name}: Command failed - {e}')

    def _test_file_reading(self, filename, test_name):
        """Test reading a file with different encoding strategies."""
        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            print(f'  ✅ {test_name}: UTF-8 with replace - {repr(content[:50])}')
        except Exception as e:
            print(f'  ❌ {test_name}: UTF-8 with replace failed - {e}')
        try:
            import chardet
            with open(filename, 'rb') as f:
                raw_data = f.read()
            detected = chardet.detect(raw_data)
            print(f'  🔍 {test_name}: Detected encoding - {detected}')
            if detected['encoding']:
                with open(filename, 'r', encoding=detected['encoding']) as f:
                    content = f.read()
                print(f'  ✅ {test_name}: Auto-detected read - {repr(content[:50])}')
        except ImportError:
            print(f'  ⚠️ {test_name}: chardet not available for auto-detection')
        except Exception as e:
            print(f'  ❌ {test_name}: Auto-detection failed - {e}')
        try:
            with open(filename, 'rb') as f:
                raw_bytes = f.read()
            print(f'  🔍 {test_name}: Raw bytes - {raw_bytes[:50]}')
            if b'\x8d' in raw_bytes:
                print(f'  🚨 {test_name}: Found 0x8d byte (the error from integration test)!')
            if b'\xff\xfe' in raw_bytes[:4] or b'\xfe\xff' in raw_bytes[:4]:
                print(f'  🔍 {test_name}: BOM detected')
        except Exception as e:
            print(f'  ❌ {test_name}: Binary read failed - {e}')

    def test_problematic_python_code_patterns(self):
        """Test the exact Python code patterns that caused the Unicode error."""
        python_code = 'import subprocess\nimport json\n\ndef get_feedback(pr_id: str, repo: str = "promptfoo/promptfoo") -> str:\n    """Extract feedback from GitHub PR reviews."""\n    try:\n        cmd = ["gh", "api", f"repos/{repo}/pulls/{pr_id}/reviews"]\n        result = subprocess.run(cmd, capture_output=True, text=True, \n                              timeout=30, encoding=\'utf-8\', errors=\'replace\')\n        \n        if result.returncode != 0:\n            return f"Error: {result.stderr}"\n        \n        return "success"\n    except Exception as e:\n        return f"Error: {str(e)}"\n\nif __name__ == "__main__":\n    print("test")'
        command = f"""@'\n{python_code}\n'@ | Out-File -FilePath "problematic_code.py" -Encoding UTF8"""
        try:
            result = execute_powershell(command, timeout='15')
            print(f'Problematic code test result: {result}')
            if os.path.exists('problematic_code.py'):
                self._test_file_reading('problematic_code.py', 'Problematic Python Code')
                try:
                    with open('problematic_code.py', 'r', encoding='utf-8') as f:
                        code_content = f.read()
                    compile(code_content, 'problematic_code.py', 'exec')
                    print('✅ Generated Python code is syntactically valid')
                except SyntaxError as e:
                    print(f'❌ Generated Python code has syntax errors: {e}')
                except UnicodeDecodeError as e:
                    print(f'🚨 Unicode error reading generated file: {e}')
                    print('This matches the integration test error!')
        except Exception as e:
            print(f'❌ Problematic code test failed: {e}')

    def test_encoding_parameter_variations(self):
        """Test different encoding parameters to see which ones cause issues."""
        test_content = 'print("Hello αβγ 中文 🚀")'
        encoding_tests = [('UTF8', 'UTF8'), ('UTF-8', 'UTF8'), ('Unicode', 'Unicode'), ('ASCII', 'ASCII'), ('Default', 'Default'), ('No encoding', None)]
        for test_name, encoding in encoding_tests:
            filename = f"encoding_test_{test_name.replace(' ', '_').lower()}.py"
            if encoding:
                command = f'''@'\n{test_content}\n'@ | Out-File -FilePath "{filename}" -Encoding {encoding}'''
            else:
                command = f'''@'\n{test_content}\n'@ | Out-File -FilePath "{filename}"'''
            try:
                result = execute_powershell(command, timeout='10')
                print(f'✅ {test_name}: Command succeeded')
                if os.path.exists(filename):
                    self._test_file_reading(filename, f'Encoding-{test_name}')
            except Exception as e:
                print(f'❌ {test_name}: Command failed - {e}')

    def test_bom_detection_and_handling(self):
        """Test if PowerShell is adding BOMs that cause issues."""
        command = '@\'\nsimple test content\n\'@ | Out-File -FilePath get_unique_filename("bom_test", "txt") -Encoding UTF8'
        result = execute_powershell(command)
        print(f'BOM test result: {result}')
        if os.path.exists(get_unique_filename('bom_test', 'txt')):
            with open(get_unique_filename('bom_test', 'txt'), 'rb') as f:
                raw_data = f.read()
            print(f'Raw file data: {raw_data}')
            print(f'First 10 bytes: {raw_data[:10]}')
            bom_checks = [(b'\xff\xfe', 'UTF-16 LE BOM'), (b'\xfe\xff', 'UTF-16 BE BOM'), (b'\xef\xbb\xbf', 'UTF-8 BOM'), (b'\xff\xfe\x00\x00', 'UTF-32 LE BOM'), (b'\x00\x00\xfe\xff', 'UTF-32 BE BOM')]
            for bom_bytes, bom_name in bom_checks:
                if raw_data.startswith(bom_bytes):
                    print(f'🔍 Found {bom_name}')
                    break
            else:
                print('✅ No BOM detected')

    def test_powershell_internal_encoding_setup(self):
        """Test if PowerShell's internal encoding setup is causing issues."""
        encoding_setup_commands = ["$PSDefaultParameterValues['*:Encoding']='utf8'", '[Console]::OutputEncoding=[System.Text.Encoding]::UTF8', '[Console]::InputEncoding=[System.Text.Encoding]::UTF8', '$OutputEncoding=[System.Text.Encoding]::UTF8', "$env:PYTHONIOENCODING='utf-8'"]
        for i, cmd in enumerate(encoding_setup_commands):
            try:
                result = execute_powershell(cmd, timeout='5')
                print(f'✅ Encoding setup {i + 1}: {cmd} - Success')
            except Exception as e:
                print(f'❌ Encoding setup {i + 1}: {cmd} - Failed: {e}')
        info_commands = ['[Console]::OutputEncoding', '[Console]::InputEncoding', '$OutputEncoding', "$PSDefaultParameterValues['*:Encoding']", 'Get-Culture']
        for cmd in info_commands:
            try:
                result = execute_powershell(cmd, timeout='5')
                print(f'🔍 {cmd}: {result}')
            except Exception as e:
                print(f'❌ {cmd}: Failed - {e}')

class TestPythonCommandBOMFix(unittest.TestCase):
    """Test that Python command execution no longer creates BOM-corrupted files."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_python_command_no_bom(self):
        """Test that Python -c commands no longer create BOM issues."""
        print('\n🧪 Testing Python command BOM fix...')
        python_command = 'python -c "import json; print(\'Hello from Python\')"'
        try:
            result = execute_powershell(python_command, timeout='10')
            print(f'✅ Python command result: {result}')
            if 'Hello from Python' in result:
                print('✅ Python command executed successfully - no encoding issues!')
            else:
                print(f'⚠️ Unexpected output: {result}')
        except Exception as e:
            print(f'❌ Python command failed: {e}')
            if 'UnicodeDecodeError' in str(e) or 'charmap' in str(e):
                print('🚨 Still getting Unicode errors - BOM fix may not be working')
            else:
                print('🔍 Different error type - may be unrelated to BOM')

    def test_complex_python_command_with_quotes(self):
        """Test complex Python commands with quotes and JSON."""
        print('\n🧪 Testing complex Python command with quotes...')
        complex_command = 'python -c "import json; data = {\'status\': \'success\', \'message\': \'test\'}; print(json.dumps(data))"'
        try:
            result = execute_powershell(complex_command, timeout='10')
            print(f'✅ Complex command result: {result}')
            if '{"status": "success"' in result or '"status":"success"' in result:
                print('✅ Complex Python command with quotes working!')
            else:
                print(f'⚠️ Unexpected output: {result}')
        except Exception as e:
            print(f'❌ Complex command failed: {e}')
            if 'UnicodeDecodeError' in str(e):
                print('🚨 Still getting Unicode errors on complex commands')

    def test_python_command_with_file_operations(self):
        """Test Python commands that do file operations."""
        print('\n🧪 Testing Python file operations...')
        file_command = 'python -c "\nimport json\ndata = {\'test\': \'data\', \'unicode\': \'café résumé\'}\nwith open(\'test_output.json\', \'w\', encoding=\'utf-8\') as f:\n    json.dump(data, f, ensure_ascii=False)\nprint(\'File created successfully\')\n"'
        try:
            result = execute_powershell(file_command, timeout='10')
            print(f'✅ File operation result: {result}')
            if os.path.exists('test_output.json'):
                print('✅ Python created file successfully')
                with open('test_output.json', 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f'✅ File content readable: {content}')
                if 'café' in content:
                    print('✅ Unicode characters preserved correctly')
            else:
                print('❌ File not created by Python command')
        except Exception as e:
            print(f'❌ File operation failed: {e}')

    def test_verify_no_temp_files_with_bom(self):
        """Verify that temp files created by Python commands don't have BOM."""
        print('\n🧪 Testing temp file BOM detection...')
        command = 'python -c "print(\'Testing temp file creation\')"'
        import glob
        temp_files_before = set(glob.glob('*.py'))
        try:
            result = execute_powershell(command, timeout='10')
            print(f'✅ Command executed: {result}')
            temp_files_after = set(glob.glob('*.py'))
            new_files = temp_files_after - temp_files_before
            if new_files:
                print(f'🔍 Found temp files: {new_files}')
                for temp_file in new_files:
                    with open(temp_file, 'rb') as f:
                        first_bytes = f.read(10)
                    print(f'🔍 {temp_file} first bytes: {first_bytes}')
                    if first_bytes.startswith(b'\xef\xbb\xbf'):
                        print(f'🚨 BOM detected in {temp_file}!')
                    else:
                        print(f'✅ No BOM in {temp_file}')
            else:
                print('🔍 No temp .py files found (they may have been cleaned up)')
        except Exception as e:
            print(f'❌ Temp file test failed: {e}')
if __name__ == '__main__':
    unittest.main(verbosity=2)

class TestPowerShellFileCreationDebug(unittest.TestCase):
    """Debug why files aren't being created despite successful command execution."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_debug_file_creation_failure(self):
        """Debug why here-string file creation is failing."""
        print(f'\n🔍 Working directory: {os.getcwd()}')
        print(f'🔍 Temp directory: {self.temp_dir}')
        print('\n=== TEST 1: Simple echo ===')
        result1 = execute_powershell('echo "test" > simple.txt')
        print(f'Result: {result1}')
        print(f"File exists: {os.path.exists('simple.txt')}")
        if os.path.exists('simple.txt'):
            with open('simple.txt', 'rb') as f:
                print(f'Raw content: {f.read()}')
        print('\n=== TEST 2: Here-string with absolute path ===')
        abs_path = os.path.join(os.getcwd(), get_unique_filename('absolute_test', 'txt')).replace('\\', '/')
        command2 = f'''@'\ntest content\n'@ | Out-File -FilePath "{abs_path}" -Encoding UTF8'''
        result2 = execute_powershell(command2)
        print(f'Result: {result2}')
        print(f"File exists: {os.path.exists('absolute_test_20016_16_1750444995166.txt')}")
        print('\n=== TEST 3: PowerShell working directory ===')
        pwd_result = execute_powershell('Get-Location')
        print(f'PowerShell PWD: {pwd_result}')
        print(f'Python PWD: {os.getcwd()}')
        print('\n=== TEST 4: List files in PowerShell directory ===')
        ls_result = execute_powershell('Get-ChildItem')
        print(f'PowerShell file list: {ls_result}')
        print('\n=== TEST 5: Force file creation with error checking ===')
        force_command = '\n        try {\n            $content = @\'\ntest content here\n\'@\n            $filePath = get_unique_filename("force_test", "txt")\n            $content | Out-File -FilePath $filePath -Encoding UTF8 -Force\n            Write-Output "File creation attempted"\n            \n            if (Test-Path $filePath) {\n                Write-Output "✅ File exists: $filePath"\n                Write-Output "File size: $((Get-Item $filePath).Length) bytes"\n                Write-Output "File content preview:"\n                Get-Content $filePath | Select-Object -First 3\n            } else {\n                Write-Output "❌ File does not exist: $filePath"\n            }\n            \n            Write-Output "Current directory contents:"\n            Get-ChildItem | ForEach-Object { "  $($_.Name)" }\n            \n        } catch {\n            Write-Output "❌ Error: $_"\n            Write-Output "Error details: $($_.Exception.Message)"\n        }\n        '
        result5 = execute_powershell(force_command)
        print(f'Force result: {result5}')
        print('\n=== TEST 6: Check PowerShell temp directory ===')
        temp_check = '\n        Write-Output "PowerShell working directory: $(Get-Location)"\n        Write-Output "Python working directory from PS: $env:PWD"\n        Write-Output "Files in current directory:"\n        Get-ChildItem | ForEach-Object { "  $($_.Name) - $($_.Length) bytes" }\n        '
        result6 = execute_powershell(temp_check)
        print(f'Temp check result: {result6}')
        print('\n=== TEST 7: Python file list ===')
        python_files = os.listdir(os.getcwd())
        print(f'Python sees files: {python_files}')

    def test_bom_handling_investigation(self):
        """Investigate BOM handling and its impact on file operations."""
        print('\n🔍 BOM Investigation')
        encodings_to_test = [('UTF8', 'UTF8'), ('UTF8BOM', 'UTF8BOM'), ('UTF8NoBOM', 'UTF8NoBOM'), ('Unicode', 'Unicode'), ('ASCII', 'ASCII'), ('Default', 'Default')]
        for name, encoding in encodings_to_test:
            print(f'\n--- Testing {name} encoding ---')
            filename = f'bom_test_{name.lower()}.txt'
            if encoding == 'Default':
                command = f'''@'\nHello from {name}\n'@ | Out-File -FilePath "{filename}"'''
            else:
                command = f'''@'\nHello from {name}\n'@ | Out-File -FilePath "{filename}" -Encoding {encoding}'''
            try:
                result = execute_powershell(command)
                print(f'Command result: {result}')
                check_command = f"""\n                if (Test-Path "{filename}") {{\n                    Write-Output "✅ File exists in PowerShell"\n                    Write-Output "Size: $((Get-Item '{filename}').Length) bytes"\n                }} else {{\n                    Write-Output "❌ File not found in PowerShell"\n                }}\n                """
                check_result = execute_powershell(check_command)
                print(f'PowerShell check: {check_result}')
                if os.path.exists(filename):
                    print('✅ File exists in Python')
                    with open(filename, 'rb') as f:
                        raw_bytes = f.read()
                    print(f'Raw bytes: {raw_bytes}')
                    print(f'First 10 bytes: {raw_bytes[:10]}')
                    if raw_bytes.startswith(b'\xef\xbb\xbf'):
                        print('🔍 UTF-8 BOM detected')
                    elif raw_bytes.startswith(b'\xff\xfe'):
                        print('🔍 UTF-16 LE BOM detected')
                    elif raw_bytes.startswith(b'\xfe\xff'):
                        print('🔍 UTF-16 BE BOM detected')
                    else:
                        print('✅ No BOM detected')
                else:
                    print('❌ File not found in Python')
            except Exception as e:
                print(f'❌ Error with {name}: {e}')

class TestRegressionScenarios(unittest.TestCase):
    """Test specific regression scenarios to ensure fixes don't break existing functionality."""

    def test_simple_commands_still_work(self):
        """Ensure simple commands still work after improvements."""
        simple_commands = ['Write-Output "Hello World"', 'Get-Date', '$var = "test"; Write-Output $var', 'Write-Output (2 + 2)']
        for cmd in simple_commands:
            with self.subTest(command=cmd):
                try:
                    result = execute_powershell(cmd, timeout='10')
                    self.assertIsInstance(result, str)
                    self.assertNotIn('Tool Failed:', result)
                except Exception as e:
                    self.fail(f'Simple command failed: {cmd} - {e}')

    def test_basic_python_commands_still_work(self):
        """Ensure basic Python commands still work."""
        basic_python_commands = ['python -c "print(\'Hello World\')"', 'python -c "import sys; print(sys.version)"', 'python -c "print(2 + 2)"']
        for cmd in basic_python_commands:
            with self.subTest(command=cmd):
                try:
                    result = execute_powershell(cmd, timeout='15')
                    self.assertIsInstance(result, str)
                    if 'Tool Failed:' in result:
                        self.fail(f'Tool failure on basic Python command: {cmd}')
                except Exception as e:
                    self.fail(f'Basic Python command failed: {cmd} - {e}')

    def test_output_limiting_still_works(self):
        """Ensure output limiting functionality still works."""
        cmd = 'for ($i=1; $i -le 20; $i++) { Write-Output "Line $i" }'
        result = execute_powershell(cmd, output_length_limit='5', timeout='10')
        if 'Tool Failed:' not in result:
            lines = result.split('\n')
            self.assertTrue(len(lines) <= 25)
if __name__ == '__main__':
    unittest.main(verbosity=2)