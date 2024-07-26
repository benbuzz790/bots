import bots

bot = bots.AnthropicBot()
bot.add_tools(r'src\bot_tools.py')
bot.converse()