import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.bots as bots
import src.bot_tools as bot_tools
import textwrap
import subprocess
import ast
import astor
from datetime import datetime as datetime

def pretty(string, name=None, width=100, indent=4):
    # Prepare the initial line
    if name is None:
        prefix = ""
    else:
        prefix = f"{name}: "
    
    if not isinstance(string, str):
        string = str(string)

    # Split the input string into lines
    lines = string.split('\n')
    
    # Process each line
    formatted_lines = []
    for i, line in enumerate(lines):
        # For the first line, include the prefix
        if i == 0:
            initial_line = prefix + line
            wrapped = textwrap.wrap(initial_line, width=width, subsequent_indent=' ' * indent)
        else:
            # For subsequent lines, apply indentation to all parts
            wrapped = textwrap.wrap(line, width=width, initial_indent=' ' * indent, subsequent_indent=' ' * indent)
        formatted_lines.extend(wrapped)
    
    # Print the formatted text
    print('\n'.join(formatted_lines))
    print("\n---\n")

def execute_code_blocks(response):
    output = '\n\n'
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

def handle_user_command(command, bot: bots.BaseBot):
    if command.lower().startswith('/exit'):
        exit()
    elif command.lower().startswith('/save'):
        filename = bot.save()
        return f"Conversation saved to {filename}"
    elif command.lower().startswith('/load'):
        filename = input("Filename:")
        if os.path.exists(filename):
            bot = bot.load(filename)
            return bot
        else:
            return f"File {filename} not found."
    elif command.lower().startswith('/auto'):
        auto = int(input("Number of automatic cycles:"))
        return auto
    return None

def main():
    bot_file = r'Codey@2024.07.23-16.44.10.bot'
    #codey = bots.BaseBot.load(bot_file)
    codey = bots.AnthropicBot()
    #pretty(codey.conversation.to_string(), "Previous Conversation")
    #pretty(f"{bot_file} loaded successfully\nName:{codey.name}\nEngine:{codey.model_engine}", "System")
    codey.add_tools(r'src\bot_tools.py')
    pretty('Bot tools added', 'System')
    turn = 'user'
    auto = 0
    output = ''  

    while True:
        if turn == 'assistant':
            if auto > 1:
                auto = auto - 1
                output = f'{codey.name}, continue working autonomously for {auto} more prompts\n\n'
            else:
                turn = 'user'
            response = codey.respond(msg)
            pretty(response, codey.name)
            output = execute_code_blocks(response)
            pretty(output, 'Executed Code Result')
        else: # user turn
            uinput = input("You: ")
            command_result = handle_user_command(uinput, codey)
            if command_result is not None:
                if isinstance(command_result, int):
                    auto = command_result
                if isinstance(command_result, bots.BaseBot):
                    codey = command_result
                else:
                    pretty(command_result, 'System')
                turn = 'user'
                continue
            msg = f"System:\n{output}\n---\n\nBen's Reply:\n{uinput}"
            pretty('')
            turn = 'assistant'

if __name__ == '__main__':
    main()