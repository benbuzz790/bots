import bots
import textwrap
from datetime import datetime as datetime
from typing import Optional, List, Dict, Any
import json
from tkinter import filedialog

help_msg: str = """
This program is an interactive terminal that uses Anthropic's Claude Sonnet 3.5.
It allows you to chat with the LLM, save and load bot states, and execute various commands.
The bot has the ability to read and write files and can execute powershell and python code directly.
The bot also has tools to help edit python files in an accurate and token-efficient way.

Available commands:
/help: Show this help message
/verbose: Show tool requests and results (default on)
/quiet: Hide tool requests and results
/save: Save the current bot
/load: Load a previously saved bot
/auto: Prompt the bot to work autonomously for a preset number of prompts
/exit: Exit the program

Type your messages normally to chat with the AI assistant.
"""


def pretty(string: str, name: Optional[str] = None, width: int = 100, indent: int = 4) -> None:
    # Prepare the initial line
    prefix: str = f"{name}: " if name is not None else ""
    
    if not isinstance(string, str):
        string = str(string)

    # Split the input string into lines
    lines: List[str] = string.split('\n')
    
    # Process each line
    formatted_lines: List[str] = []
    for i, line in enumerate(lines):
        # For the first line, include the prefix
        if i == 0:
            initial_line: str = prefix + line
            wrapped: List[str] = textwrap.wrap(initial_line, width=width, subsequent_indent=' ' * indent)
        else:
            # For subsequent lines, apply indentation to all parts
            wrapped: List[str] = textwrap.wrap(
                line, width=width, initial_indent=' ' * indent, subsequent_indent=' ' * indent
            )
        formatted_lines.extend(wrapped)
    
    # Print the formatted text
    print('\n'.join(formatted_lines))
    print("\n---\n")


def main() -> None:
    codey = bots.AnthropicBot(name='Claude')
    #codey: openai_bots.GPTBot = openai_bots.GPTBot(name='ChatGPT')
    codey.add_tools(bots.python_tools)
    pretty('Bot initialized', 'System')
    
    verbose: bool = True
    turn: str = 'user'
    auto: int = 0

    while True:
        if turn == 'assistant':
            if auto > 0:
                msg: str = f'Work autonomously for {auto} more prompts'
                pretty(msg, 'You')
                auto -= 1
            else:
                turn = 'user'
            response: str = codey.respond(msg)
            tool_use_requests: List[Dict[str, Any]] = codey.tool_handler.get_requests()
            tool_use_results: List[Dict[str, Any]] = codey.tool_handler.get_results()

            pretty(response, codey.name)

            if verbose:
                pretty(f'Tool Requests\n\n{json.dumps(tool_use_requests, indent=1)}', "System")
                pretty(f'Tool Results\n\n{json.dumps(tool_use_results, indent=1)}', "System")       
        
        else:  # user turn
            uinput: str = input("You: ")
            
            match uinput:
                case "/exit":
                    pretty('')  # separator
                    pretty("exiting...", "System")
                    exit(0)
                case "/auto":
                    auto = int(input("Automatic prompt limit:"))
                    pretty(f"Starting automatic work for {auto} prompts", "System")
                    turn = 'assistant'
                case "/load": 
                    filename: str = filedialog.askopenfilename(
                        filetypes=[("Bot files", "*.bot"),
                                   ("All files", "*.*")])
                    try:
                        codey = codey.load(filename)
                    except:
                        pretty(f"Error loading {filename}", "System")
                case "/save": 
                    name: str = input("Filename (leave blank for automatic filename):")
                    if name:
                        codey.save(f'{name}.bot')
                    else:
                        codey.save()
                    pass
                case "/quiet":
                    verbose = False
                case "/verbose":
                    verbose = True
                case "/help":
                    pretty('')  # separator
                    pretty(help_msg, "System")
                case _: 
                    msg: str = uinput
                    turn = 'assistant'

            if turn == 'assistant':
                pretty('')  # separator
                msg: str = uinput


# import sys
# import traceback

# def debug_on_error(type: Any, value: Any, tb: Any) -> None:
#     traceback.print_exception(type, value, tb)
#     print("\n--- Entering post-mortem debugging ---")
#     import pdb
#     pdb.post_mortem(tb)


if __name__ == "__main__":
    #sys.excepthook = debug_on_error
    main()
