import unittest


class TestTerminalTools(unittest.TestCase):

    def test_powershell_utf8_output(self):
        """Test that PowerShell commands return proper UTF-8 encoded output"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Hello 世界 🌍"'
        result = execute_powershell(ps_script)
        self.assertIn('Hello 世界 🌍', result)
        ps_script = '[System.Console]::Error.WriteLine("エラー 🚫")'
        result = execute_powershell(ps_script)
        self.assertIn('エラー 🚫', result)
        ps_script = """
            Write-Output "Standard: こんにちは"
            [System.Console]::Error.WriteLine("Error: システムエラー")
        """
        result = execute_powershell(ps_script)
        self.assertIn('Standard: こんにちは', result)
        self.assertIn('Error: システムエラー', result)

    def test_powershell_no_output(self):
        """Test that commands with no output work correctly"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '$null'
        result = execute_powershell(ps_script)
        self.assertEqual(result.strip(), '')
        ps_script = 'Write-Output ""'
        result = execute_powershell(ps_script)
        self.assertEqual(result.strip(), '')

    def test_powershell_timeout(self):
        """Test that long-running commands timeout correctly"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Start-Sleep -Seconds 308'
        result = execute_powershell(ps_script)
        self.assertIn('Error: Command execution timed out after 300 seconds',
            result)

    def test_powershell_truncated_output(self):
        """Test that long output is truncated and saved to file"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = execute_powershell(ps_script, output_length_limit='50')
        self.assertEqual(len(result.splitlines()), 54)
        self.assertIn('50 lines omitted', result)
        self.assertIn('Full output saved to', result)

    def test_powershell_command_chain_success(self):
        """Test that && chains work correctly when all commands succeed"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = (
            'Write-Output "First" && Write-Output "Second" && Write-Output "Third"'
            )
        result = execute_powershell(ps_script)
        self.assertIn('First', result)
        self.assertIn('Second', result)
        self.assertIn('Third', result)

    def test_powershell_command_chain_failure(self):
        """Test that && chains stop executing after a command fails"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'nonexistentcommand && Write-Output "Should Not See This"'
        result = execute_powershell(ps_script)
        self.assertNotIn('Should Not See This', result)
        self.assertIn('nonexistentcommand', result.lower())

    def test_powershell_complex_command_chain(self):
        """Test complex command chains with mixed success/failure conditions"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = (
            'New-Item -Path "test.txt" -ItemType "file" -Force && Write-Output "success" > test.txt && Write-Output "fail" > /nonexistent/path/file.txt && Write-Output "Should Not See This"'
            )
        result = execute_powershell(ps_script)
        self.assertNotIn('Should Not See This', result)
        cleanup = execute_powershell('Remove-Item -Path "test.txt" -Force')

    def test_powershell_special_characters(self):
        """Test handling of special characters and box drawing symbols"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = 'Write-Output "Box chars: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼"'
        result = execute_powershell(ps_script)
        self.assertIn('Box chars:', result)
        self.assertTrue(any(char in result for char in '─│┌┐└┘├┤┬┴┼'))
        ps_script = 'Write-Output "Extended ASCII: ° ± ² ³ µ ¶ · ¹ º"'
        result = execute_powershell(ps_script)
        self.assertIn('Extended ASCII:', result)
        self.assertTrue(any(char in result for char in '°±²³µ¶·¹º'))

    def test_powershell_invalid_encoding_handling(self):
        """Test handling of potentially problematic encoding scenarios"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = """
        Write-Output "Mixed scripts: Latin-ASCII-한글-עברית-العربية"
        Write-Output "More mixed: Русский-日本語-🌟-‱-√"
    """
        result = execute_powershell(ps_script)
        self.assertIn('Mixed scripts:', result)
        self.assertIn('More mixed:', result)
        ps_script = """
        [byte[]]$bytes = 0xC4,0x80,0xE2,0x98,0x83
        [System.Text.Encoding]::UTF8.GetString($bytes)
    """
        result = execute_powershell(ps_script)
        self.assertTrue(len(result.strip()) > 0)

    def test_powershell_encoding_environment(self):
        """Test that PowerShell encoding environment is properly configured"""
        from bots.tools.terminal_tools import execute_powershell
                    
        # Test Console Output Encoding
        ps_script = "[Console]::OutputEncoding.WebName"
        result = execute_powershell(ps_script)
        self.assertEqual('utf-8', result.strip().lower())
                    
        # Test Console Input Encoding
        ps_script = "[Console]::InputEncoding.WebName"
        result = execute_powershell(ps_script)
        self.assertEqual('utf-8', result.strip().lower())
                    
        # Verify PowerShell default encoding parameter
        ps_script = "$PSDefaultParameterValues['*:Encoding']"
        result = execute_powershell(ps_script)
        self.assertEqual('utf8', result.strip().lower())
                    
        # Test that encoding works with actual output
        test_string = "Test UTF8 String: ★ → ♠ ±"
        ps_script = f'Write-Output "{test_string}"'
        result = execute_powershell(ps_script)
        self.assertEqual(test_string, result.strip())
