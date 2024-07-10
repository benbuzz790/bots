import gitignore
import bots
import os
from bots import Engines
import textwrap
import subprocess
import os

def execute_python_code(code, timeout=300):
    # Create a temporary file in the current working directory
    temp_file_name = os.path.join(os.getcwd(), 'temp_script.py')
    
    with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file.flush()
    
    try:
        # Execute the Python code in a separate process
        process = subprocess.Popen(['python', temp_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        try:
            # Wait for the process to complete with a timeout
            stdout, stderr = process.communicate(timeout=timeout)
            return stdout + stderr
        except subprocess.TimeoutExpired:
            # Terminate the process if it exceeds the timeout
            process.terminate()
            return f"Error: Code execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # Clean up the temporary file
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
    B1 = bots.AnthropicBot(name='Claude', model_engine=Engines.CLAUDE35)
    B1 = B1.load("Claude@2024.07.10-13.54.12.bot")
    pretty(B1.conversation.to_string())
    turn = 'user'
    auto = 0

    while(True):
        initial_message = 'No code to execute'
        output = initial_message
    
        if(turn=='assistant'):
            if auto > 1:
                auto = auto - 1
            else:
                turn = 'user'
            response = B1.respond(msg)
            pretty(response, B1.name)
            code_blocks, labels = bots.remove_code_blocks(response)
            if code_blocks:
                for code, label in zip(code_blocks, labels):

                    if label.lower() == "epowershell":
                        try:
                            if output == initial_message: output = 'Executed Code Result:\n'
                            result = subprocess.run(["powershell", "-Command", code], capture_output=True, text=True, timeout=30)
                            output += result.stdout + result.stderr
                        except subprocess.TimeoutExpired:
                            output += "Error: Command execution timed out after 30 seconds."
                        except Exception as e:
                            output += f"Error: {str(e)}"
        
                    elif label.lower() == 'epython':
                        try:
                            if output == initial_message: output = 'Executed Code Result:\n'
                            result = execute_python_code(code)
                            output += result + '\n'
                        except Exception as e:
                            output += f"Error: {str(e)}"
                            
                    output = output + '\n---\n'

        pretty(output, 'System')
        
        if(turn=='user'):
            # get human response
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
                    B1 = bots.load(filename)
                    pretty(f"Conversation loaded from {filename}", 'System')
                else:
                    pretty(f"File {filename} not found.", 'System')
                turn = 'user'
            elif uinput.lower().startswith('/auto'):
                auto = input("Number of automatic cycles:")
                turn = 'user'
            else:   
                msg = 'System:\n' + output + "\n---\n" + "\nBen's Reply:\n" + uinput 
                pretty('')
                turn = 'assistant'
    
if __name__ == '__main__':
    main()
