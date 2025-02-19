from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
import sys
import bots.tools.python_editing_tools
import bots.tools.terminal_tools
import bots.tools.code_tools
import textwrap
from datetime import datetime as datetime
from typing import Optional, List, Dict, Any
import json
from tkinter import filedialog
import os
import re

import platform
# Import platform-specific modules
if platform.system() == 'Windows':
    import msvcrt
else:
    import select
    import termios
    import tty




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
/up: "rewind" the conversation by one turn by moving up the conversation tree
/down: Move down the conversation tree. Requests index of reply if there are multiple.
/left: Move to this conversation node's left sibling
/right: Move to this conversation node's right sibling
/auto: Let the bot work autonomously until it sends a response without using any tools
/root: Move to the root node of the conversation tree
/label: Save current node with a label for later reference
/goto: Move to a previously labeled node
/exit: Exit the program

Type your messages normally to chat.
"""

def check_for_interrupt() -> bool:
    """
    Check if user pressed Escape without blocking execution.
    Returns True if Escape was pressed, False otherwise.
    """
    if platform.system() == 'Windows':
        # Windows implementation using msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch()
            return key == b'\x1b'  # ESC key
        return False
    else:
        # Unix implementation using select
        if select.select([sys.stdin], [], [], 0.0)[0]:
            key = sys.stdin.read(1)
            # Clear the input buffer
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)
            return key == '\x1b'  # ESC key
        return False

def setup_raw_mode():
    """Set up terminal for raw input mode on Unix systems"""
    if platform.system() != 'Windows':
        # Save the terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            # Set the terminal to raw mode
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            # If setting raw mode fails, restore old settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return old_settings
    return None

def restore_terminal(old_settings):
    """Restore terminal settings on Unix systems"""
    if platform.system() != 'Windows' and old_settings is not None:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def pretty(string: str, name: Optional[str] = None, width: int = 1000, indent: int = 4) -> None:
    """Prints a string nicely"""
    prefix: str = f"{name}: " if name is not None else ""
    
    if not isinstance(string, str):
        string = str(string)

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

def initialize_bot() -> Optional[ChatGPT_Bot | AnthropicBot]:
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            bot = AnthropicBot(name='Claude', 
                               model_engine=bots.foundation.base.Engines.CLAUDE35_SONNET_20241022)
        except Exception as e:
            pretty(f"Failed to initialize Anthropic bot: {e}", "System")
    elif openai_key:
        try:
            bot = ChatGPT_Bot(name='ChatGPT')
        except Exception as e:
            pretty(f"Failed to initialize ChatGPT bot: {e}", "System")
    else:
        raise ValueError('No OpenAI or Anthropic API keys found. Set up your key')
    
    bot.add_tools(bots.tools.python_editing_tools)
    bot.add_tools(bots.tools.code_tools)
    bot.add_tools(bots.tools.github_tools)
    bot.add_tools(bots.tools.terminal_tools)

    return bot

def clean_dict(d:dict, indent:int=4, level:int=1):
    """
    Clean a dict containing recursive json dumped strings for printing
    Returns: clean string representation of the dict
    """
    for k, v in d.items():
        if isinstance(v, dict):
            clean_dict(v, indent, level+1)
        if isinstance(v, str) and '\n' in v:
            lines = v.splitlines()
            for i, line in enumerate(lines):
                line = ' '*indent*(level+1) + line
                if i == 0: line = '\n' + line
                lines[i] = line
            d[k] = '\n'.join(lines)
    cleaned_dict = json.dumps(d, indent=indent*level)
    cleaned_dict = re.sub(r'(?<!\\)\\n', '\n', cleaned_dict)
    cleaned_dict = cleaned_dict.replace('\\"', '"')
    cleaned_dict = cleaned_dict.replace('\\\\', '\\')
    return cleaned_dict

from bots.dev.decorators import make_issue_upon_error, debug_on_error
#@create_issues(repo = 'benbuzz790/bots')
@debug_on_error
def main() -> None:
    # Check for filename argument
    if len(sys.argv) > 1:
        bot_file = sys.argv[1]
        try:
            at_bot = initialize_bot().load(bot_file)
            pretty(f'Loaded bot from {bot_file}', 'System')
            pretty("\n"+str(at_bot), 'System')
        except Exception as e:
            pretty(f'Failed to load {bot_file}: {e}', 'System')
            at_bot = initialize_bot()
    else:
        at_bot = initialize_bot()
        pretty('Bot initialized', 'System')
    
    verbose: bool = True
    turn: str = 'user'
    auto_mode: bool = False
    old_settings = None
    labeled_nodes = {}

    try:
        while True:
            if turn == 'assistant':
                # Print response and grab tool info
                response: str = at_bot.respond(msg)
                requests: List[Dict[str, Any]] = at_bot.tool_handler.requests
                results: List[Dict[str, Any]] = at_bot.tool_handler.results
                pretty(response, at_bot.name)

                request_str = ''.join(clean_dict(r) for r in requests)
                result_str = ''.join(clean_dict(r) for r in results)

                if requests:
                    if verbose:
                        pretty(f'Tool Requests\n\n{request_str}', "System")
                        pretty(f'Tool Results\n\n{result_str}', "System")  
                    else:
                        for request in requests:
                            tool_name, _ = at_bot.tool_handler.tool_name_and_input(request)
                            pretty(f'{at_bot.name} used {tool_name}', "System")
                            
                    if auto_mode:
                        pretty("Tools were used, continuing auto...", "System")
                else:
                    if auto_mode:
                        pretty("No tools used, exiting auto", "System")
                        auto_mode = False
                        turn = 'user'
            
                if auto_mode:
                    print("Auto mode active (press ESC to interrupt)... ", end='', flush=True)
                    
                    # Set up raw mode for Unix systems
                    if not old_settings:
                        old_settings = setup_raw_mode()
                    
                    # Check for interrupt
                    if check_for_interrupt():
                        pretty("Auto mode interrupted", "System")
                        auto_mode = False
                        turn = 'user'
                        continue
                    
                    if auto_mode:  # Only continue if not interrupted
                        msg: str = 'ok'
                        pretty(msg, 'You')
                else:
                    turn = 'user'

            else:  # user turn
                # Restore terminal settings before getting user input
                restore_terminal(old_settings)
                old_settings = None
                
                uinput: str = input("You: ")
                print('\n---\n')

                if uinput is None or uinput == '':
                    uinput = '~'
                
                # Split input into words
                words = uinput.strip().split()
                if not words:
                    continue
                    
                # Check for command at start or end
                command = None
                msg = None
                if words[0].startswith('/'):
                    command = words[0]
                    msg = ' '.join(words[1:]) if len(words) > 1 else None
                elif words[-1].startswith('/'):
                    command = words[-1]
                    msg = ' '.join(words[:-1]) if len(words) > 1 else None
                else:
                    msg = uinput

                # Handle turn order
                # Default to assistant turn but
                # allow commands to swap to user
                if msg is not None:
                    turn = 'assistant'
                
                # Handle commands
                match command:
                    case "/exit":
                        pretty('')  # separator
                        pretty("exiting...", "System")
                        return
                    case "/auto":
                        auto_mode = True
                        pretty("Auto active", "System")
                        if msg is None or msg == '':
                            msg = 'ok'
                        turn = 'assistant'
                    case "/load": 

                        filename = input("Filename: ")
                        if filename == '':
                            filename: str = filedialog.askopenfilename(
                                filetypes=[("Bot files", "*.bot"),
                                        ("All files", "*.*")])
                        try:
                            at_bot = at_bot.load(filename)
                            print(at_bot)
                        except:
                            pretty(f"Error loading {filename}", "System")
                    case "/save": 
                        name: str = input("Filename (leave blank for automatic filename): ")
                        if name:
                            at_bot.save(name)
                        else:
                            at_bot.save()
                    case "/quiet":
                        verbose = False
                    case "/verbose":
                        verbose = True
                        pretty('Tool output on', 'System')
                    case "/up":
                        if at_bot.conversation.parent and at_bot.conversation.parent.parent:
                            pretty('Moving up conversation tree', 'System')
                            at_bot.conversation = at_bot.conversation.parent.parent
                            pretty(at_bot.conversation.content, at_bot.name)
                        else:
                            pretty("At root - can't go up", 'System')
                    case "/down":
                        if at_bot.conversation.replies:
                            max_index = len(at_bot.conversation.replies)-1
                            idx = 0
                            if max_index > 0:
                                idx = int(input(f"Reply index (max {max_index}):"))
                            pretty('Moving down conversation tree','System')
                            next_node = at_bot.conversation.replies[idx]
                            if next_node.replies:
                                at_bot.conversation = next_node.replies[0]
                                pretty(at_bot.conversation.content, at_bot.name)
                            else:
                                at_bot.conversation = next_node
                                pretty(next_node.content, at_bot.name)
                        else:
                            pretty('At leaf - can\'t go down', 'System')
                    case "/left":
                        if not at_bot.conversation.parent:
                            pretty('At root - can\'t go left', 'System')
                        elif not at_bot.conversation.parent.replies or len(at_bot.conversation.parent.replies) <= 1:
                            pretty('Conversation has no siblings at this point', 'System')
                        else:
                            current_index = next(i for i, reply in enumerate(at_bot.conversation.parent.replies) 
                                              if reply is at_bot.conversation)
                            next_index = (current_index - 1) % len(at_bot.conversation.parent.replies)
                            pretty('Moving left in conversation tree', 'System')
                            at_bot.conversation = at_bot.conversation.parent.replies[next_index]
                            pretty(at_bot.conversation.content, at_bot.name)
                    case "/right":
                        if not at_bot.conversation.parent:
                            pretty('At root - can\'t go right', 'System')
                        elif not at_bot.conversation.parent.replies or len(at_bot.conversation.parent.replies) <= 1:
                            pretty('Conversation has no siblings at this point', 'System')
                        else:
                            current_index = next(i for i, reply in enumerate(at_bot.conversation.parent.replies) 
                                              if reply is at_bot.conversation)
                            next_index = (current_index + 1) % len(at_bot.conversation.parent.replies)
                            pretty('Moving right in conversation tree', 'System')
                            at_bot.conversation = at_bot.conversation.parent.replies[next_index]
                            pretty(at_bot.conversation.content, at_bot.name)
                    case "/root":
                        while at_bot.conversation.parent:
                            at_bot.conversation = at_bot.conversation.parent
                        pretty('Moved to root of conversation tree', 'System')
                        pretty(at_bot.conversation.content, at_bot.name)
                    case "/label":
                        label = input("Label:")
                        labeled_nodes[label] = at_bot.conversation
                        pretty(f'Saved current node with label: {label}', 'System')
                        turn = 'user'
                    case "/goto":
                        label = input("Label:")
                        if label in labeled_nodes:
                            at_bot.conversation = labeled_nodes[label]
                            pretty(f'Moved to node labeled: {label}', 'System')
                            pretty(at_bot.conversation.content, at_bot.name)
                        else:
                            pretty(f'No node found with label: {label}', 'System')
                        turn = 'user'
                    case "/help":
                        pretty('')  # separator
                        pretty(help_msg, "System")
                    case None:
                        continue
                    case _:
                        pretty("Unrecognized command. Try /help.", "System")
                        turn = 'user'

                if turn == 'assistant':
                    pretty('')  # separator

    finally:
        # Ensure terminal settings are restored when exiting
        restore_terminal(old_settings)


if __name__ == '__main__':
    main()
