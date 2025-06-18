import os

import bots.flows.functional_prompts as fp
import bots.tools.code_tools as code_tools
import bots.tools.python_editing_tools as python_editing_tools
import bots.tools.terminal_tools as terminal_tools
from bots.dev.decorators import handle_errors
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot


@handle_errors
def message_bot(bot_path, message):
    """
    Loads a bot, sends it a message, and allows it to work.
    Use to prepare a bot to do a task and to allow it to work. Returns control
    when the bot replies with '/DONE'.
    Parameters:
    - bot_path (str): File path to the saved bot
    - message (str): The message to send to the bot
    Returns the bot's first response, a list of tool-uses in order, and final
    response as a string.
    Does NOT save the bot.
    cost: varies
    """
    bot = Bot.load(bot_path)
    bot.autosave = True
    first_message = "MESSAGE:\n\n" + message
    continue_prompt = "reply '/DONE' to stop when MESSAGE is addressed."

    def stop_condition(bot: Bot):
        tool_name = ""
        tools = ""
        if bot.tool_handler.requests:
            for request in bot.tool_handler.requests:
                tool_name, _ = bot.tool_handler.tool_name_and_input(request)
            tools += "- " + tool_name + "\n"
        response = bot.conversation.content
        print(bot.name + ": " + response + "\n" + tool_name)
        return "/DONE" in response

    _, nodes = fp.prompt_while(
        bot,
        first_message,
        continue_prompt,
        stop_condition,
    )
    tools = ""
    for node in nodes:
        tool_name = ""
        if node.tool_calls:
            for call in node.tool_calls:
                tool_name, _ = bot.tool_handler.tool_name_and_input(call)
                tools += "- " + tool_name + "\n"
    return nodes[0].content + ":\n" + tools + "\n---" + nodes[-1].content


@handle_errors
def initialize_file_bot(file_name: str, system_message: str) -> str:
    """
    Creates and initializes a new file-editing bot, saving it to disk.
    Creates any necessary directories from the file_name path if they don't
    exist.
    Use when you need to create a new bot to handle implementation of a
    specific file.
    The bot will be initialized with appropriate file-level tools and context.
    Parameters:
    - file_name (str): Name of the file this bot will manage (can include
      directory path)
    Returns success message with bot's file path or an error message string.
    cost: low
    """
    directory = os.path.dirname(file_name)
    if directory:
        os.makedirs(directory, exist_ok=True)
    name, _ = os.path.splitext(file_name)
    file_bot = AnthropicBot(name=f"{name}")
    file_bot.set_system_message(system_message)
    file_bot.add_tools(code_tools)
    file_bot.add_tools(terminal_tools)
    file_bot.add_tools(python_editing_tools)
    path = file_bot.save(file_bot.name)
    return f"Success: file bot created at {path}"


@handle_errors
def generate_project(spec: str) -> str:
    """
    Executes the standard process for project generation using a hierarchical
    system of specialized AI assistants.
    Use when you need to create a complete Python project from a specification.
    The system will:
    1. Analyze project specifications and create module requirements
    2. Break down the project into logical modules
    3. Create and coordinate specialized bots for implementation
    4. Implement and test the code
    5. Validate against requirements
    Parameters:
    - spec (str): Project specification text describing the desired system
    Returns:
    str: Success message or error message string
    cost: very high
    """
    import bots.flows.project_tree.project_tree as project_tree

    return project_tree.generate_project(spec)
