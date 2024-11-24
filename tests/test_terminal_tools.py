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
