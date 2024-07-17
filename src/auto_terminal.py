import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from src.bot_tools import rewrite
import src.bots as bots
import textwrap
import subprocess
import ast
import astor
from tkinter import filedialog

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

class PythonExecutor():

    class IndentVisitor(ast.NodeTransformer):
        def __init__(self, indent='    '):
            self.indent = indent
            self.level = 0

        def visit(self, node):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.If, ast.For, ast.While, ast.With)):
                self.level += 1
                node = self.generic_visit(node)
                self.level -= 1
            else:
                node = self.generic_visit(node)
            
            if hasattr(node, 'body') and isinstance(node.body, list):
                for item in node.body:
                    if hasattr(item, 'col_offset'):
                        if not (isinstance(item, ast.Expr) and isinstance(item.value, ast.Str)):
                            item.col_offset = len(self.indent) * self.level
            return node
        
    def __init__(self):
        pass

    def error_filter(self, code_blocks, labels):
        """
        Filters out common errors that bots make
        Returns corrected code blocks.        
        """
        corrected_blocks = []
        corrected_labels = []
        for i, (block, label) in enumerate(zip(code_blocks, labels)):
            true_false_bot = bots.BaseBot.load(r'data\TrueFalse@2024.07.16-18.27.57.bot')
            query = "Does the following code contain any shortcuts such as '# (Remaining code is unchanged) or anything along similar lines?"
            response = true_false_bot.respond(content = query + '\n\n' + block)
            
            if not label == 'epython': continue # code is not intended to run

            if 'True' in response:
                # good enough for now
                # in the future perhaps we can merge using AST
                raise SyntaxError("Shortcuts like '# Rest of code' are not allowed, you must reply with comprehensive code or use bot_tools")
        
            # Check for the file writing format
            file_match = re.match(r'# ([\w.]+)\n', block)
            if file_match:
                filename = file_match.group(1)
                code = re.sub(r'# [\w.]+\n', '', block, count=1)
                rewrite(filename, code)
                # Process the block further
                block = code

            # Attempt to compile the code
            try:
                compile(block, '<string>', 'exec')
                corrected_blocks.append(block)
                corrected_labels.append(label)
            except (SyntaxError, NameError):
                # If there's an error, try merging with the previous block
                if i > 0 and labels[i-1] == label:
                    merged_block = corrected_blocks[-1] + "\n" + block
                    try:
                        compile(merged_block, '<string>', 'exec')
                        corrected_blocks[-1] = merged_block
                    except:
                        # If merging doesn't resolve the issue, keep the original block
                        corrected_blocks.append(block)
                        corrected_labels.append(label)
                else:
                    # If it's the first block or labels don't match, keep the original
                    corrected_blocks.append(block)
                    corrected_labels.append(label)

        return corrected_blocks, corrected_labels

    def custom_string_formatter(self, string, embedded=False, current_line=None, uni_lit=False):
        return repr(string)

    def indent_code(self, code, indent='    '):
        tree = ast.parse(code)
        self.IndentVisitor(indent).visit(tree)
        return astor.to_source(tree, indent_with=indent, pretty_string=self.custom_string_formatter).strip()

    def custom_indent(self, code, indent='    '):
        lines = code.split('\n')
        in_string = False
        string_delimiter = None
        indented_lines = []

        for line in lines:
            stripped = line.strip()
            
            # Check for the start or end of a multi-line string
            if not in_string and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_string = True
                string_delimiter = stripped[:3]
            elif in_string and stripped.endswith(string_delimiter):
                in_string = False
                string_delimiter = None

            # Apply indentation only if not in a multi-line string
            if in_string:
                indented_lines.append(line)
            else:
                indented_lines.append(indent + line if line.strip() else line)

        return '\n'.join(indented_lines)

    def execute(self, code, timeout=300):
        # Indent the original code
        indented_code = self.indent_code(code)
        # Wrap the indented code in a function
        wrapped_code = f"""
    import os
    import sys
    import traceback
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    def main():
    {self.custom_indent(indented_code)}
    if __name__ == '__main__':
        try:
            import os
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            main()
        except Exception as error_error:
            print(f"An error occurred: {{str(error_error)}}", file=sys.stderr)
            print("Local variables at the time of the error:", file=sys.stderr)
            tb = sys.exc_info()[2]
            while tb:
                frame = tb.tb_frame
                tb = tb.tb_next
                print(f"Frame {{frame.f_code.co_name}} in {{frame.f_code.co_filename}}:{{frame.f_lineno}}", file=sys.stderr)
                local_vars = dict(frame.f_locals)
                for key, value in local_vars.items():
                    if not key.startswith('__') and key not in ['sys', 'traceback', 'error_error', 'main', 'tb', 'frame', 'Frame']:
                        print(f"    {{key}} = {{value}}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    """
        # Then, use AST to fix indentation of the entire wrapped code
        indented_code = self.indent_code(wrapped_code)

        # The rest of the function remains the same...
        temp_file_name = os.path.join(os.getcwd(), r'scripts\temp_script.py')
        temp_file_copy = os.path.join(os.getcwd(), r'scripts\last_temp_script.py')
        
        with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
            temp_file.write(indented_code)
            temp_file.flush()
        
        with open(temp_file_copy, 'w', encoding='utf-8') as temp_file:
            temp_file.write(indented_code)
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

class AutoTerminalSession:
    
    def __init__(self, file_path=None):
        if file_path is None:
            file_path = ("data\Claude@2024.07.12-07.52.47.bot")
        self.bot = bots.BaseBot.load(file_path)
        self.py = PythonExecutor()
        self.turn = 'user'

    def handle_code(self, code_blocks, labels, initial_message=''):
        output = initial_message
        for code, label in zip(code_blocks, labels):
            if output == initial_message: output = '\n\nExecuted Code Result:\n\n'
            if label.lower() == "epowershell":
                try:
                    result = subprocess.run(["powershell", "-Command", code], capture_output=True, text=True, timeout=30)
                    output += result.stdout + result.stderr
                except subprocess.TimeoutExpired:
                    output += "Error: Command execution timed out after 30 seconds."
                except Exception as e:
                    output += f"Error: {str(e)}"

            elif label.lower() == 'epython':
                result = self.py.execute(code)
                output += result + '\n'

            output = output + '\n---\n'
        return output
    
    def handle_user(self, uinput):
        if uinput.lower().startswith('/exit'):
            exit()
        elif uinput.lower().startswith('/save'):
            filename = self.bot.save()
            pretty(f"Conversation saved to {filename}", 'System')
            self.turn = 'user'
        elif uinput.lower().startswith('/load'):
            file_path = filedialog.askopenfilename(
                title="Select .bot file to open in terminal",
                filetypes=[("Bot files", "*.bot"), ("All files", "*.*")]
            )
            self.bot = self.bot.load(file_path)
            pretty(f"Conversation loaded from {file_path}", 'System')
            self.turn = 'user'
        elif uinput.lower().startswith('/auto'):
            auto = int(input("Number of automatic cycles:"))
            self.turn = 'user'
        else:  
            self.turn = 'assistant' 
            return "\nUser Reply:\n" + uinput
        return ''

    def run(self):
        pretty(self.bot.conversation.to_string())
        auto = 0

        while(True):
            initial_message = '.no code detected.'
            output = ''    
            if(self.turn == 'assistant'):
                if auto > 1:
                    auto = auto - 1
                    output = f'Auto-mode enabled for {auto} more messages\n\n'
                else:
                    self.turn = 'user'
                response = self.bot.respond(msg)
                pretty(response, self.bot.name)
                code_blocks, labels = bots.remove_code_blocks(response)
                output += self.handle_code(code_blocks, labels, initial_message)

            msg = 'System:\n' + output + "\n---\n"
            pretty(output, 'System')
            
            if(self.turn == 'user'):
                uinput = input("You: ")
                msg += self.handle_user(uinput)
                pretty('')
                
def main():
    AutoTerminalSession().run()

if __name__ == '__main__':
    main()
