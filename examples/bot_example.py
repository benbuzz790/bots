import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.anthropic_bots import AnthropicBot
AnthropicBot().chat()