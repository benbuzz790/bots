# A simple example giving the bot the ability to read files on your computer
import bots

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

bot = bots.AnthropicBot()
bot.add_tool(read_file)
bot.chat()


