import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# A simple example giving the bot the ability to read files on your computer
from src.anthropic_bots import AnthropicBot

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

bot = AnthropicBot()
bot.add_tool(read_file)
bot.chat()