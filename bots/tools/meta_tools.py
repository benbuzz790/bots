import os

import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
import bots.tools.terminal_tools as terminal_tools
from bots.dev.decorators import toolify
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines


@toolify()
def message_bot(bot_path, message):
    """
    Loads a bot, sends it a message, and allows it to work.
    Use to prepare a bot to do a task and to allow it to work. 
    Returns control when the bot replies without using a tool.
    
    Parameters:
    - bot_path (str): File path to a saved bot
    - message (str): Message to send to the bot
    
    Returns:
    - (str): A brief summary of the bot's work and success or
        failure detail in the bot's own words
    """

    bot = Bot.load(bot_path)
    bot.autosave = False
    fp.prompt_while(
        bot,
        message,
        callback = bot.save(bot_path)
    )
    final_response = bot.respond("Please send a brief summary of your work and success or failure detail.")
    return final_response


@toolify()
def initialize_file_bot(file_name: str, system_message: str, model: str) -> str:
    """
    Requires Anthropic API key
    Creates and initializes a new file-editing bot, saving it to disk.
    Creates any necessary directories from the file_name path if they don't
    exist.
    Use when you need to create a new bot to handle implementation of a
    specific file.
    The bot will be initialized with appropriate file-level tools and context.
    Parameters:
    - file_name (str): Name of the file this bot will manage (can include
      directory path)
    - system_message (str): System message sent to bot. Recommendation: brief and 
        similar to your own system message
    - model: (str): Either "haiku", "sonnet", or "opus" depending on required intellect.
        Prefer less expensive models at first.
    Returns success message with bot's file path or an error message string.
    """
    directory = os.path.dirname(file_name)
    if directory:
        os.makedirs(directory, exist_ok=True)
    name, _ = os.path.splitext(file_name)

    if model =="haiku":
        model_engine = Engines.CLAUDE45_HAIKU
    elif model == "sonnet":
        model_engine = Engines.CLAUDE46_SONNET
    elif model == "opus":
        model_engine = Engines.CLAUDE46_OPUS
    else:
        raise("Model string not found. Must be exactly haiku, sonnet, or opus")

    file_bot = AnthropicBot(name=f"{name}", model_engine=model_engine)
    file_bot.set_system_message(system_message)
    file_bot.add_tools(code_tools)
    file_bot.add_tools(terminal_tools)
    path = file_bot.save(file_bot.name)
    return f"Success: file bot created at {path}"