#!/usr/bin/env python3
"""
Debug backend bot creation issue by testing the bot manager directly
"""

import sys
import os

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_backend_bot_creation():
    """Test bot creation through the backend bot manager."""
    print("Testing backend bot creation...")

    try:
        from bot_manager import BotManager
        print("✅ BotManager imported")

        manager = BotManager()
        print("✅ BotManager created")

        bot_id = manager.create_bot("Test Bot")
        print(f"✅ Bot created with ID: {bot_id}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_backend_bot_creation()
    if success:
        print("\n🎉 Backend bot creation test passed!")
    else:
        print("\n❌ Backend bot creation test failed!")