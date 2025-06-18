import os

import bots.flows.functional_prompts as fp
from bots.flows.project_tree.project_tree_prompts import prompts
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot
from bots.tools import code_tools, python_editing_tools, terminal_tools
from bots.utils.helpers import _process_error


# Bot tools
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
    """
    try:
        # Set up prompt_while arguments
        bot = Bot.load(bot_path)
        first_message = prompts.message_bot_first_message(message)
        continue_prompt = prompts.message_bot_continue

        def stop_condition(bot: Bot):
            # Side effect: print
            tool_name = ""
            tools = ""
            if bot.tool_handler.requests:
                for request in bot.tool_handler.requests:
                    handler = bot.tool_handler
                    tool_name, _ = handler.tool_name_and_input(request)
                tools += "- " + tool_name + "\n"
            response = bot.conversation.content
            print(bot.name + ": " + response + "\n" + tool_name)
            # Stop when /DONE in response
            return "/DONE" in bot.conversation.content

        # prompt_while bot hasn't said "/DONE"
        _, nodes = fp.prompt_while(
            bot,
            first_message,
            continue_prompt=continue_prompt,
            stop_condition=stop_condition,
        )
        # get desired information from returned conversation nodes
        tools = ""
        for node in nodes:
            tool_name = ""
            if node.tool_calls:
                for call in node.tool_calls:
                    tool_name, _ = bot.tool_handler.tool_name_and_input(call)
                    tools += "- " + tool_name + "\n"
        return nodes[0].content + ":\n" + tools + "\n---" + nodes[-1].content
    except Exception as error:
        return _process_error(error)


def memorialize_requirements(name: str, requirements: str):
    """
    Creates or updates a requirements file for a module.
    Use when you need to document requirements for a new file or update
    existing requirements.
    Parameters:
    - name (str): Name of the file (.md or .txt)
    - requirements (str): The requirements content to write. This must be
        comprehensive and complete. Saying 'everything else stays the same'
        is NOT allowed.
    Returns the filename or an error message string.
    """
    try:
        file_path = f"{name}"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(requirements)
        return f"Created requirements file {file_path} successfully"
    except Exception as error:
        return _process_error(error)


def initialize_file_bot(file_name: str) -> str:
    """
    Creates and initializes a new file-editing bot, saving it to disk.
    Creates any necessary directories from the file_name path if they don't
    exist.
    Use when you need to create a new bot to handle implementation of a
    specific file. The bot will be initialized with appropriate file-level
    tools and context.
    Parameters:
    - file_name (str): Name of the file this bot will manage (can include
        directory path)
    Returns success message with bot's file path or an error message string.
    """
    try:
        # Create directories from the file path if they don't exist
        directory = os.path.dirname(file_name)
        if directory:
            os.makedirs(directory, exist_ok=True)
        name, _ = os.path.splitext(file_name)
        file_bot = AnthropicBot(name=f"{name}")
        file_bot.set_system_message(prompts.file_initialization)
        file_bot.add_tools(code_tools)
        file_bot.add_tools(terminal_tools)
        file_bot.add_tools(python_editing_tools)
        path = file_bot.save(file_bot.name)
        return f"Success: file bot created at {path}"
    except Exception as error:
        return _process_error(error)


def view(file_path: str):
    """
    Display the contents of a file with line numbers.
    Parameters:
    - file_path (str): The path to the file to be viewed.
    Returns:
    A string containing the file contents with line numbers.
    """
    encodings = [
        "utf-8",
        "utf-16",
        "utf-16le",
        "ascii",
        "cp1252",
        "iso-8859-1",
    ]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                lines = file.readlines()
            lines_enum = enumerate(lines)
            numbered_lines = [f"{i+1}:{ln.rstrip()}" for i, ln in lines_enum]
            return "\n".join(numbered_lines)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"Error: {str(e)}"
    return f"Error: Unable to read file with any of the attempted encodings: " f"{', '.join(encodings)}"


def view_dir(
    path: str = ".",
    output_file=None,
    target_extensions: str = "['py', 'txt', '.md']",
):
    """
    Creates a summary of the directory structure starting from the given path,
    writing only files with specified extensions. The output is written to a
    file if specified.

    Returns:
    str: A formatted string containing the directory structure, with each
    directory and file properly indented.
    Example output:
    project/
        module1/
            script.py
            README.md
        module2/
            utils.py
    """
    extensions_list = [ext.strip().strip("'\"") for ext in target_extensions.strip("[]").split(",")]
    extensions_list = [("." + ext if not ext.startswith(".") else ext) for ext in extensions_list]
    output_text = []
    for root, dirs, files in os.walk(path):
        has_py = False
        for _, _, fs in os.walk(root):
            if any(f.endswith(tuple(extensions_list)) for f in fs):
                has_py = True
                break
        if has_py:
            level = root.replace(path, "").count(os.sep)
            indent = "    " * level
            line = f"{indent}{os.path.basename(root)}/"
            output_text.append(line)
            subindent = "    " * (level + 1)
            for file in files:
                if file.endswith(tuple(extensions_list)):
                    line = f"{subindent}{file}"
                    output_text.append(line)
    if output_file is not None:
        with open(output_file, "w") as file:
            file.write(output_text)
    return "\n".join(output_text)
