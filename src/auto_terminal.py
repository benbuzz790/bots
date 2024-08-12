import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.anthropic_bots as bots
import src.bot_tools as bot_tools
import textwrap
from datetime import datetime as datetime
import src.base as base
from dataclasses import dataclass
from typing import Optional, List, Tuple
import json


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


def execute_code_blocks(response: str) -> str:
    output: str = '\n\n'
    code_blocks: List[str]
    labels: List[str]
    code_blocks, labels = bots.remove_code_blocks(response)
    if code_blocks:
        for code, label in zip(code_blocks, labels):
            if label.lower() == "epowershell":
                output += bot_tools.execute_powershell(code)
                output += '\n---\n'
            elif label.lower() == 'epython':
                output += bot_tools.execute_python_code(code)
                output += '\n---\n'
    return output


@dataclass
class CommandResult:
    message: Optional[str] = None
    auto_cycles: int = 0
    should_exit: bool = False
    new_bot: Optional[bots.Bot] = None


def handle_user_command(command: str, bot: bots.Bot) -> CommandResult:
    match command.lower().split(maxsplit=1):
        case ["/exit", *_]:
            return CommandResult(should_exit=True)
        
        case ["/save", *_]:
            filename: str = bot.save()
            return CommandResult(message=f"Conversation saved to {filename}")
        
        case ["/load", *args]:
            filename: str = args[0] if args else input("Filename: ")
            if os.path.exists(filename):
                new_bot: bots.Bot = bot.load(filename)
                return CommandResult(message="Bot loaded successfully", new_bot=new_bot)
            else:
                return CommandResult(message=f"File {filename} not found.")
        
        case ["/auto", *args]:
            cycles: int = int(args[0] if args else input("Number of automatic cycles: "))
            return CommandResult(auto_cycles=cycles)
        
        case _:
            return CommandResult()


def main() -> None:
    bot_file: str = r'Codey@2024.07.23-16.44.10.bot'
    codey: bots.AnthropicBot = bots.AnthropicBot(name='Claude')
    codey.add_tools(r'src\bot_tools.py')
    pretty('Bot tools added', 'System')
    verbose: bool = True
    
    turn: str = 'user'
    auto: int = 0

    while True:
        if turn == 'assistant':
            if auto > 0:
                auto -= 1
                msg: str = f'please continue working autonomously for {auto} more prompts\n\n'
                pretty(msg, "You")
            else:
                turn = 'user'
            response: str = codey.respond(msg)
            tool_use_requests: List[dict] = codey.tool_handler.get_requests()
            tool_use_results: List[dict] = codey.tool_handler.get_results()

            pretty(response, codey.name)

            if verbose:
                pretty(f'Tool Requests\n\n{json.dumps(tool_use_requests, indent=1)}', "System")
                pretty(f'Tool Results\n\n{json.dumps(tool_use_results, indent=1)}', "System")       
        
        else:  # user turn
            uinput: str = input("You: ")
            result: CommandResult = handle_user_command(uinput, codey)
            
            if result.should_exit:
                exit(0)
            if result.message:
                pretty(result.message, 'System')
            if result.new_bot:
                codey = result.new_bot
            if result.auto_cycles > 0:
                auto = result.auto_cycles
                turn = 'assistant'
            else:
                turn = 'assistant'
            
            if turn == 'assistant':
                pretty('')  # separator
                msg: str = uinput


if __name__ == '__main__':
    main()