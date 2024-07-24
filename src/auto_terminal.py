import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.bots as bots
import textwrap
import subprocess
import ast
import astor
from datetime import datetime as datetime

def create_wrapper_ast():
    wrapper_code = """
import os
import sys
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    pass  # Placeholder for user code

if __name__ == '__main__':
    try:
        main()
    except Exception as error_error:
        print(f"An error occurred: {str(error_error)}", file=sys.stderr)
        print("Local variables at the time of the error:", file=sys.stderr)
        tb = sys.exc_info()[2]
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            print(f"Frame {frame.f_code.co_name} in {frame.f_code.co_filename}:{frame.f_lineno}", file=sys.stderr)
            local_vars = dict(frame.f_locals)
            for key, value in local_vars.items():
                if not key.startswith('__') and key not in ['sys', 'traceback', 'error_error', 'main', 'tb', 'frame']:
                    print(f"    {key} = {value}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    """
    return ast.parse(wrapper_code)

def insert_code_into_wrapper(wrapper_ast, code_ast):
    main_func = next(node for node in wrapper_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    main_func.body = code_ast.body
    return wrapper_ast

def execute_python_code(code, timeout=300):
    # Parse the input code into an AST
    code_ast = ast.parse(code)
    wrapper_ast = create_wrapper_ast()
    combined_ast = insert_code_into_wrapper(wrapper_ast, code_ast)
    final_code = astor.to_source(combined_ast)
    now = datetime.now()
    formatted_datetime = now.strftime("%Y.%m.%d-%H.%M.%S")
    temp_file_name = os.path.join(os.getcwd(), 'scripts/temp_script.py')
    temp_file_copy = os.path.join(os.getcwd(), f'scripts/last_temp_script@{formatted_datetime}.py')
    
    with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
        temp_file.write(final_code)
        temp_file.flush()
    
    with open(temp_file_copy, 'w', encoding='utf-8') as temp_file:
        temp_file.write(final_code)
        temp_file.flush()

    try:
        process = subprocess.Popen(['python', temp_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return stdout + stderr
        except subprocess.TimeoutExpired:
            process.terminate()
            return f"Error: Code execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if os.path.exists(temp_file_name):
            os.remove(temp_file_name)

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
                try:
                    result = subprocess.run(["powershell", "-Command", code], capture_output=True, text=True, timeout=30)
                    output += result.stdout + result.stderr
                except subprocess.TimeoutExpired:
                    output += "Error: Command execution timed out after 30 seconds."
                except Exception as e:
                    output += f"Error: {str(e)}"
            elif label.lower() == 'epython':
                try:
                    result = execute_python_code(code)
                    output += result + '\n'
                except Exception as e:
                    output += f"Error: {str(e)}"
            output = output + '\n---\n'
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
    bot = bots.AnthropicBot.load(bot_file)
    pretty(bot.conversation.to_string(), "Previous Conversation")
    pretty(f"{bot_file} loaded successfully\nName:{bot.name}\nEngine:{bot.model_engine}", "System")
    turn = 'user'
    auto = 0
    output = ''  

    while True:
        if turn == 'assistant':
            if auto > 1:
                auto = auto - 1
                output = f'{bot.name}, continue working autonomously for {auto} more prompts\n\n'
            else:
                turn = 'user'
            response = bot.respond(msg)
            pretty(response, bot.name)
            output = execute_code_blocks(response)
            pretty(output, 'Executed Code Result')
        else:
            uinput = input("You: ")
            command_result = handle_user_command(uinput, bot)
            if command_result is not None:
                if isinstance(command_result, int):
                    auto = command_result
                if isinstance(command_result, bots.BaseBot):
                    bot = command_result
                else:
                    pretty(command_result, 'System')
                turn = 'user'
                continue
            msg = f"System:\n{output}\n---\n\nBen's Reply:\n{uinput}"
            pretty('')
            turn = 'assistant'

if __name__ == '__main__':
    main()