import sys
import io
from unittest.mock import patch
sys.path.append('.')
from tests.conftest import TestBot
# Create a test bot
bot = TestBot()
print("=== Testing branch_self function ===")
# Capture stdout
captured_output = io.StringIO()
with patch('sys.stdout', captured_output):
    print("About to call bot.respond...")
    response = bot.respond("Use branch_self with prompts ['Test prompt 1', 'Test prompt 2']")
    print("Got response:", response)
# Get captured output
debug_output = captured_output.getvalue()
print("=== Captured Output ===")
print(repr(debug_output))
print("=== End Captured Output ===")
print("=== Tool Handler Info ===")
print(f"Requests: {len(bot.tool_handler.requests)}")
print(f"Results: {len(bot.tool_handler.results)}")
if bot.tool_handler.requests:
    print("Last request:", bot.tool_handler.requests[-1])
if bot.tool_handler.results:
    print("Last result:", bot.tool_handler.results[-1])
