import ast
import importlib
import json
import os
import sys

import bots.tools.self_tools as self_tools
from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines

# Reload the module to pick up changes
importlib.reload(self_tools)
bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE35_SONNET_20240620)
bot.add_tools(self_tools)
# Test the fixed branch_self
print("Testing fixed branch_self:")
response = bot.respond('Call branch_self with self_prompts=["Hello world", "Goodbye world"] and allow_work="False"')
print("BOT RESPONSE:", repr(response))
# Check what the tool actually returned
print("\nChecking tool results:")
if hasattr(bot, "tool_handler") and bot.tool_handler.results:
    latest_result = bot.tool_handler.results[-1]
    print("LATEST TOOL RESULT:", latest_result)
    if hasattr(latest_result, "content"):
        print("TOOL RESULT CONTENT:", latest_result.content)
# Follow up to see the tool result
response2 = bot.respond("What did the branch_self tool return?")
print("RESPONSE2:", repr(response2))
