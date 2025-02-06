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
        ps_script = 'Start-Sleep -Seconds 308'  # Just over 5 minute timeout
        result = execute_powershell(ps_script)
        self.assertIn('Error: Command execution timed out after 300 seconds', result)

    def test_powershell_truncated_output(self):
        """Test that long output is truncated and saved to file"""
        from bots.tools.terminal_tools import execute_powershell
        ps_script = '1..100 | ForEach-Object { Write-Output "Line $_" }'
        result = execute_powershell(ps_script, output_length_limit='50')
        self.assertEqual(len(result.splitlines()), 54)  # 50 lines + 4 for truncation message
        self.assertIn('50 lines omitted', result)
        self.assertIn('Full output saved to', result)