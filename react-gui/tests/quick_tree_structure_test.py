#!/usr/bin/env python3
"""
Quick test to check conversation tree structure from backend.
"""

import requests
import json

BACKEND_URL = "http://127.0.0.1:8000"

def test_bot_state_structure():
    """Test bot state structure from REST API."""
    print("🔍 Testing Bot State Structure")
    print("=" * 40)

    # Create a bot
    print("1. Creating bot...")
    response = requests.post(f"{BACKEND_URL}/api/bots/create", json={"name": "Structure Test Bot"})

    if response.status_code != 200:
        print(f"❌ Failed to create bot: {response.status_code}")
        return False

    bot_data = response.json()
    bot_id = bot_data.get("bot_id")
    print(f"✅ Bot created: {bot_id}")

    # Get bot state
    print("2. Getting bot state...")
    state_response = requests.get(f"{BACKEND_URL}/api/bots/{bot_id}")

    if state_response.status_code != 200:
        print(f"❌ Failed to get bot state: {state_response.status_code}")
        return False

    bot_state = state_response.json()
    print("✅ Bot state retrieved")

    # Analyze the structure
    print("3. Analyzing conversation tree structure...")
    print(f"Bot state keys: {list(bot_state.keys())}")

    if "conversation_tree" in bot_state:
        tree = bot_state["conversation_tree"]
        print(f"conversation_tree type: {type(tree)}")
        print(f"conversation_tree value: {tree}")

        if not isinstance(tree, dict):
            print(f"❌ ISSUE FOUND: conversation_tree should be dict, got {type(tree)}")
            print(f"   This would cause 'conversationTree must be an object' error in frontend")
            return False
        else:
            print(f"✅ conversation_tree is a valid dict with {len(tree)} entries")
    else:
        print("❌ No conversation_tree field in bot state")
        return False

    # Check other fields
    expected_fields = ["id", "name", "conversation_tree", "current_node_id", "is_connected", "is_thinking"]
    for field in expected_fields:
        if field in bot_state:
            print(f"✅ {field}: {type(bot_state[field])} = {bot_state[field]}")
        else:
            print(f"❌ Missing field: {field}")

    return True

if __name__ == "__main__":
    success = test_bot_state_structure()
    if success:
        print("\n🎉 Bot state structure is valid!")
    else:
        print("\n❌ Found issues with bot state structure!")
    exit(0 if success else 1)