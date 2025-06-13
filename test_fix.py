import sys
sys.path.append('.')
from bots.foundation.base import Bot
from bots.tools.code_tools import view_dir
# Create a bot and add the view_dir tool to test the dynamic execution
bot = Bot()
bot.add_tool(view_dir)
# Try to call the tool through the bot system
try:
    result = bot.tools[0]['function']('.', None, "['py', 'txt']")
    print("SUCCESS: Tool executed without error")
    print(f"Result length: {len(result)}")
except Exception as e:
    print(f"ERROR: {e}")
