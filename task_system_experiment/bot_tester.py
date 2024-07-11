
import os
import json
import importlib
from typing import Any, Dict

# Dynamically import bots module
bots = importlib.import_module('bots')

def load_bot(file_path: str) -> Any:
    with open(file_path, 'r') as f:
        bot_data = json.load(f)
    
    bot_class = getattr(bots, bot_data['bot_class'])
    
    # Remove 'bot_class' and 'conversation' from bot_data
    bot_data.pop('bot_class', None)
    conversation_data = bot_data.pop('conversation', None)
    
    # Handle model_engine conversion
    if 'model_engine' in bot_data:
        engine_value = bot_data['model_engine']
        for engine in bots.Engines:
            if engine.value == engine_value:
                bot_data['model_engine'] = engine
                break
        else:
            raise ValueError(f"Invalid model_engine value: {engine_value}")
    
    # Create bot instance
    bot = bot_class(**bot_data)
    
    # Set conversation if it exists
    if conversation_data:
        bot.conversation = bots.CN.ConversationNode.from_dict(conversation_data[0])
    
    return bot

def test_bot_format(file_path: str) -> bool:
    print(f"Testing bot file: {file_path}")
    try:
        bot = load_bot(file_path)
        print("Bot loaded successfully.")
        
        # Check for required fields
        required_fields = ['name', 'model_engine', 'max_tokens', 'temperature', 'role', 'role_description']
        for field in required_fields:
            if not hasattr(bot, field):
                print(f"Missing required field: {field}")
                return False
        
        # Check conversation format
        if hasattr(bot, 'conversation') and bot.conversation and not isinstance(bot.conversation, bots.CN.ConversationNode):
            print("Conversation is not a ConversationNode object.")
            return False
        
        print("All required fields present and conversation format is correct.")
        return True
    
    except Exception as e:
        print(f"Error loading bot: {str(e)}")
        return False

def run_tests() -> None:
    bot_files = [f for f in os.listdir('.') if f.endswith('.bot')]
    
    if not bot_files:
        print("No .bot files found in the current directory.")
        return
    
    for bot_file in bot_files:
        print("" + "="*50)
        test_bot_format(bot_file)
        print("="*50 + "")

# Run the tests
if __name__ == "__main__":
    run_tests()
