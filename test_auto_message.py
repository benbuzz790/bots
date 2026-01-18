import os
import sys

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines

sys.path.insert(0, os.path.abspath("."))
# Create a simple bot
bot = AnthropicBot(model_engine=Engines.CLAUDE37_SONNET_20250219)
# Simulate what /auto does - run prompt_while
print("\n=== Testing prompt_while return values ===\n")
# Mock a simple scenario
