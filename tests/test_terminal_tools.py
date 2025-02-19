import unittest


class TestTerminalTools(unittest.TestCase):

    def test_powershell_utf8_output(self):
        """Test that PowerShell commands return proper UTF-8 encoded output"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Write-Output "Hello 世界 🌍"'
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('Hello 世界 🌍', result)
        ps_script = '[System.Console]::Error.WriteLine("エラー 🚫")'
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('エラー 🚫', result)
        ps_script = """
            Write-Output "Standard: こんにちは"
            [System.Console]::Error.WriteLine("Error: システムエラー")
        """
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('Standard: こんにちは', result)
        self.assertIn('Error: システムエラー', result)

    def test_powershell_no_output(self):
        """Test that commands with no output work correctly"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '$null'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(result.strip(), '')
        ps_script = 'Write-Output ""'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(result.strip(), '')

    @unittest.skip('takes too long')
    def test_powershell_timeout(self):
        """Test that long-running commands timeout correctly"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Start-Sleep -Seconds 308'
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('Error: Command execution timed out after 300 seconds',
            result)

    def test_powershell_truncated_output(self):
        """Test that long output is truncated and saved to file"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = _execute_powershell_stateless(ps_script,
            output_length_limit='50')
        self.assertEqual(len(result.splitlines()), 54)
        self.assertIn('50 lines omitted', result)
        self.assertIn('Full output saved to', result)

    def test_powershell_command_chain_success(self):
        """Test that && chains work correctly when all commands succeed"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = (
            'Write-Output "First" && Write-Output "Second" && Write-Output "Third"'
            )
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('First', result)
        self.assertIn('Second', result)
        self.assertIn('Third', result)

    def test_powershell_command_chain_failure(self):
        """Test that && chains stop executing after a command fails"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'nonexistentcommand && Write-Output "Should Not See This"'
        result = _execute_powershell_stateless(ps_script)
        self.assertNotIn('Should Not See This', result)
        self.assertIn('nonexistentcommand', result.lower())

    def test_powershell_complex_command_chain(self):
        """Test complex command chains with mixed success/failure conditions"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = (
            'New-Item -Path "test.txt" -ItemType "file" -Force && Write-Output "success" > test.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
            )
        result = _execute_powershell_stateless(ps_script)
        self.assertNotIn('Should Not See This', result)
        cleanup = _execute_powershell_stateless(
            'Remove-Item -Path "test.txt" -Force')

    def test_powershell_special_characters(self):
        """Test handling of special characters and box drawing symbols"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = 'Write-Output "Box chars: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼"'
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('Box chars:', result)
        self.assertTrue(any(char in result for char in '─│┌┐└┘├┤┬┴┼'))
        ps_script = 'Write-Output "Extended ASCII: ° ± ² ³ µ ¶ · ¹ º"'
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('Extended ASCII:', result)
        self.assertTrue(any(char in result for char in '°±²³µ¶·¹º'))

    def test_powershell_invalid_encoding_handling(self):
        """Test handling of potentially problematic encoding scenarios"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = """
        Write-Output "Mixed scripts: Latin-ASCII-한글-עברית-العربية"
        Write-Output "More mixed: Русский-日本語-🌟-‱-√"
    """
        result = _execute_powershell_stateless(ps_script)
        self.assertIn('Mixed scripts:', result)
        self.assertIn('More mixed:', result)
        ps_script = """
        [byte[]]$bytes = 0xC4,0x80,0xE2,0x98,0x83
        [System.Text.Encoding]::UTF8.GetString($bytes)
    """
        result = _execute_powershell_stateless(ps_script)
        self.assertTrue(len(result.strip()) > 0)

    def test_powershell_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured"""
        from bots.tools.terminal_tools import _execute_powershell_stateless
        ps_script = '[Console]::OutputEncoding.WebName'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual('utf-8', result.strip().lower())
        ps_script = '[Console]::InputEncoding.WebName'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual('utf-8', result.strip().lower())
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual('utf8', result.strip().lower())
        test_string = 'Test UTF8 String: ★ → ♠ ±'
        ps_script = f'Write-Output "{test_string}"'
        result = _execute_powershell_stateless(ps_script)
        self.assertEqual(test_string, result.strip())


class TestTerminalToolsStateful(unittest.TestCase):

    def _collect_generator_output(self, generator):
        """Helper method to collect all output from the generator"""
        return '\n'.join(list(generator))

    def test_stateful_basic_use(self):
        """Test basic command execution and output capture"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Hello, World!"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual('Hello, World!', result.strip())

    def test_stateful_utf8_output(self):
        """Test that PowerShell commands return proper UTF-8 encoded output in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Hello 世界 🌍"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('Hello 世界 🌍', result)
        ps_script = '[System.Console]::Error.WriteLine("エラー 🚫")'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('エラー 🚫', result)
        ps_script = """
            Write-Output "Standard: こんにちは"
            [System.Console]::Error.WriteLine("Error: システムエラー")
        """
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('Standard: こんにちは', result)
        self.assertIn('Error: システムエラー', result)

    def test_stateful_no_output(self):
        """Test that commands with no output work correctly in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '$null'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(result.strip(), '')
        ps_script = 'Write-Output ""'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(result.strip(), '')

    def test_stateful_truncated_output(self):
        """Test that long output is truncated and saved to file in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = self._collect_generator_output(execute_powershell(
            ps_script, output_length_limit='50'))
        lines = result.splitlines()
        content_lines = sum(1 for line in lines if line.startswith('Line'))
        self.assertEqual(content_lines, 50,
            'Should have exactly 50 content lines')
        self.assertTrue(any('lines omitted' in line for line in lines),
            'Should have truncation message')
        self.assertTrue(any('Full output saved to' in line for line in
            lines), 'Should have file save message')

    def test_stateful_command_chain_success(self):
        """Test that && chains work correctly when all commands succeed in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = (
            'Write-Output "First" && Write-Output "Second" && Write-Output "Third"'
            )
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('First', result)
        self.assertIn('Second', result)
        self.assertIn('Third', result)

    def test_stateful_command_chain_failure(self):
        """Test that && chains stop executing after a command fails in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'nonexistentcommand && Write-Output "Should Not See This"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertNotIn('Should Not See This', result)
        self.assertIn('nonexistentcommand', result.lower())

    def test_stateful_complex_command_chain(self):
        """Test complex command chains with mixed success/failure conditions in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = (
            'New-Item -Path "test.txt" -ItemType "file" -Force && Write-Output "success" > test.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
            )
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertNotIn('Should Not See This', result)
        cleanup = self._collect_generator_output(execute_powershell(
            'Remove-Item -Path "test.txt" -Force'))

    def test_stateful_special_characters(self):
        """Test handling of special characters and box drawing symbols in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Box chars: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('Box chars:', result)
        self.assertTrue(any(char in result for char in '─│┌┐└┘├┤┬┴┼'))
        ps_script = 'Write-Output "Extended ASCII: ° ± ² ³ µ ¶ · ¹ º"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('Extended ASCII:', result)
        self.assertTrue(any(char in result for char in '°±²³µ¶·¹º'))

    def test_stateful_invalid_encoding_handling(self):
        """Test handling of potentially problematic encoding scenarios in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = """
        Write-Output "Mixed scripts: Latin-ASCII-한글-עברית-العربية"
        Write-Output "More mixed: Русский-日本語-🌟-‱-√"
        """
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertIn('Mixed scripts:', result)
        self.assertIn('More mixed:', result)
        ps_script = """
        [byte[]]$bytes = 0xC4,0x80,0xE2,0x98,0x83
        [System.Text.Encoding]::UTF8.GetString($bytes)
        """
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertTrue(len(result.strip()) > 0)

    def test_stateful_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured in generator form"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '[Console]::OutputEncoding.WebName'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual('utf-8', result.strip().lower())
        ps_script = '[Console]::InputEncoding.WebName'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual('utf-8', result.strip().lower())
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual('utf8', result.strip().lower())
        test_string = 'Test UTF8 String: ★ → ♠ ±'
        ps_script = f'Write-Output "{test_string}"'
        result = self._collect_generator_output(execute_powershell(ps_script))
        self.assertEqual(test_string, result.strip())

    def test_stateful_line_by_line_output(self):
        """Test that output comes as a complete block"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = """
    1..5 | ForEach-Object {
        Write-Output "Line $_"
        Start-Sleep -Milliseconds 100
    }
    """
        outputs = list(execute_powershell(ps_script))
        self.assertEqual(1, len(outputs), 'Should yield output exactly once')
        lines = outputs[0].splitlines()
        expected_lines = [f'Line {i}' for i in range(1, 6)]
        actual_lines = [l.strip() for l in lines if l.strip().startswith(
            'Line')]
        self.assertEqual(expected_lines, actual_lines)

    def test_stateful_exact_limit_output(self):
        """Test behavior when output is exactly at the limit"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..50 | ForEach-Object { Write-Output "Line $_" }'
        result = self._collect_generator_output(execute_powershell(
            ps_script, output_length_limit='50'))
        lines = result.splitlines()
        content_lines = sum(1 for line in lines if line.startswith('Line'))
        self.assertEqual(content_lines, 50,
            'Should have exactly 50 content lines')
        self.assertFalse(any('lines omitted' in line for line in lines),
            'Should not have truncation message')
        self.assertFalse(any('Full output saved to' in line for line in
            lines), 'Should not have file save message')

    def test_true_statefulness_between_calls(self):
        """Test that PowerShell state persists between function calls"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script1 = '$global:test_var = "Hello from previous call"'
        list(execute_powershell(ps_script1))
        ps_script2 = 'Write-Output $global:test_var'
        result = self._collect_generator_output(execute_powershell(ps_script2))
        self.assertIn('Hello from previous call', result)
        ps_script3 = (
            'New-Item -ItemType Directory -Path "test_state_dir" -Force; Set-Location "test_state_dir"'
            )
        list(execute_powershell(ps_script3))
        ps_script4 = '(Get-Location).Path'
        result = self._collect_generator_output(execute_powershell(ps_script4))
        self.assertTrue(result.strip().endswith('test_state_dir'))
        ps_script5 = (
            'Set-Location ..; Remove-Item -Path "test_state_dir" -Force -Recurse'
            )
        list(execute_powershell(ps_script5))

    def test_basic_input_handling(self):
        """Test that basic Read-Host input requests work correctly"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('input_test')
        ps_script1 = '$name = Read-Host "Enter your name"'
        result1 = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(result1))
        self.assertIn('Enter your name', result1[0])
        ps_script2 = 'TestUser'
        result2 = list(execute_powershell(ps_script2))
        ps_script3 = 'Write-Output $name'
        result3 = list(execute_powershell(ps_script3))
        self.assertEqual(1, len(result3))
        self.assertEqual('TestUser', result3[0].strip())
        manager.cleanup()

    def test_multiple_input_requests(self):
        """Test handling multiple input requests in sequence"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('multi_input_test')
        ps_script1 = """
    $first = Read-Host "Enter first value"
    $second = Read-Host "Enter second value"
    """
        result1 = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(result1))
        self.assertIn('Enter first value', result1[0])
        result2 = list(execute_powershell('Value1'))
        self.assertEqual(1, len(result2))
        self.assertIn('Enter second value', result2[0])
        list(execute_powershell('Value2'))
        ps_script4 = 'Write-Output "$first and $second"'
        result4 = list(execute_powershell(ps_script4))
        self.assertEqual(1, len(result4))
        self.assertEqual('Value1 and Value2', result4[0].strip())
        manager.cleanup()

    def test_input_error_handling(self):
        """Test error handling when providing input incorrectly"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('error_input_test')
        ps_script1 = 'Write-Output "No input needed"'
        result1 = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(result1))
        self.assertEqual('No input needed', result1[0].strip())
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
        list(execute_powershell('$global:counter = 0'))
        ps_script1 = """
    $global:counter++
    $response = Read-Host "Counter is $global:counter, continue?"
    $global:counter++
    Write-Output "Counter is now $global:counter"
    """
        result1 = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(result1))
        self.assertIn('Counter is 1, continue?', result1[0])
        result2 = list(execute_powershell('yes'))
        self.assertEqual(1, len(result2))
        self.assertIn('Counter is now 2', result2[0])
        result3 = list(execute_powershell('Write-Output $global:counter'))
        self.assertEqual(1, len(result3))
        self.assertEqual('2', result3[0].strip())
        manager.cleanup()

    def test_alternative_input_methods(self):
        """Test different PowerShell input request methods"""
        from bots.tools.terminal_tools import execute_powershell, PowerShellManager
        manager = PowerShellManager.get_instance('alt_input_test')
        ps_script1 = """
    Write-Output "Please enter something:"
    $input = [Console]::ReadLine()
    Write-Output "You entered: $input"
    """
        result1 = list(execute_powershell(ps_script1))
        self.assertEqual(1, len(result1))
        self.assertIn('Please enter something:', result1[0])
        result2 = list(execute_powershell('Console input test'))
        self.assertEqual(1, len(result2))
        self.assertEqual('You entered: Console input test', result2[0].strip())
        ps_script2 = """
    $input = $Host.UI.ReadLine()
    Write-Output "Host UI input: $input"
    """
        result3 = list(execute_powershell(ps_script2))
        self.assertEqual(1, len(result3))
        result4 = list(execute_powershell('Host UI input test'))
        self.assertEqual(1, len(result4))
        self.assertEqual('Host UI input: Host UI input test', result4[0].
            strip())
        manager.cleanup()
