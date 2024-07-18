import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.bots as bots
import textwrap
import subprocess
import os
import ast
import astor

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

    temp_file_name = os.path.join(os.getcwd(), 'scripts/temp_script.py')
    temp_file_copy = os.path.join(os.getcwd(), 'scripts/last_temp_script.py')
    
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

def main():
    B1 = bots.BaseBot.load(r"data\Codey@2024.07.17-19.20.05.bot")
    #B1 = bots.AnthropicBot(name='Codey')
    pretty(B1.conversation.to_string())
    turn = 'user'
    auto = 0

    while(True):
        initial_message = '.no code detected.'
        output = initial_message
    
        if(turn=='assistant'):
            if auto > 1:
                auto = auto - 1
                output = f'Auto-mode enabled for {auto} more messages\n\n'
            else:
                turn = 'user'
            response = B1.respond(msg)
            pretty(response, B1.name)
            code_blocks, labels = bots.remove_code_blocks(response)
            if code_blocks:
                for code, label in zip(code_blocks, labels):

                    if label.lower() == "epowershell":
                        try:
                            if output == initial_message: output = '\n\nExecuted Code Result:\n\n'
                            result = subprocess.run(["powershell", "-Command", code], capture_output=True, text=True, timeout=30)
                            output += result.stdout + result.stderr
                        except subprocess.TimeoutExpired:
                            output += "Error: Command execution timed out after 30 seconds."
                        except Exception as e:
                            output += f"Error: {str(e)}"
        
                    elif label.lower() == 'epython':
                        try:
                            if output == initial_message: output = '\n\nExecuted Code Result:\n\n'
                            result = execute_python_code(code)
                            output += result + '\n'
                        except Exception as e:
                            output += f"Error: {str(e)}"
                            
                    output = output + '\n---\n'

        msg = 'System:\n' + output + "\n---\n"
        pretty(output, 'System')
        
        if(turn=='user'):
            uinput = input("You: ")
            if uinput.lower().startswith('/exit'):
                exit()
            elif uinput.lower().startswith('/save'):
                filename = B1.save()
                pretty(f"Conversation saved to {filename}", 'System')
                turn = 'user'
            elif uinput.lower().startswith('/load'):
                filename = input("Filename:")
                if os.path.exists(filename):
                    B1 = B1.load(filename)
                    pretty(f"Conversation loaded from {filename}", 'System')
                else:
                    pretty(f"File {filename} not found.", 'System')
                turn = 'user'
            elif uinput.lower().startswith('/auto'):
                auto = int(input("Number of automatic cycles:"))
                turn = 'user'
            else:   
                msg = msg + "\nBen's Reply:\n" + uinput 
                pretty('')
                turn = 'assistant'
    
if __name__ == '__main__':
    main()