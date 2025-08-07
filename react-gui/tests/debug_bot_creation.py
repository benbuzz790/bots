#!/usr/bin/env python3
"""
Debug bot creation issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def test_bot_creation():
    """Test bot creation directly."""
    print("Testing bot creation...")

    try:
        from bots.foundation.anthropic_bots import AnthropicBot
        import bots.tools.code_tools as code_tools
        print("✅ Imports successful")

        bot = AnthropicBot()
        print("✅ AnthropicBot created")

        bot.add_tools(code_tools)
        print("✅ Tools added")

        # Test a simple response
        response = bot.respond("Hello, just say hi back")
        print(f"✅ Bot response: {response[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_creation()
    if success:
        print("\n🎉 Bot creation test passed!")
    else:
        print("\n❌ Bot creation test failed!")