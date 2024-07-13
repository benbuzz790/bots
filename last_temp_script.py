
import sys
import traceback

def main():
    import bot_tools
    new_function = """def execute_python_code(code, timeout=300):
""\"Execute Python code with timeout and error handling.""\"
wrapped_code = f""\"
import sys
import traceback

def main():
{code}

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f"An error occurred: {{str(error)}}", file=sys.stderr)
        print("Local variables at the time of the error:", file=sys.stderr)
        tb = sys.exc_info()[2]
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            print(f"Frame {{frame.f_code.co_name}} in {{frame.f_code.co_filename}}:{{frame.f_lineno}}", file=sys.stderr)
            local_vars = dict(frame.f_locals)
            for key, value in local_vars.items():
                if not key.startswith('__') and key not in ['sys', 'traceback', 'error', 'main', 'tb', 'frame']:
                    print(f"    {{key}} = {{value}}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
""\"

    temp_file_name = os.path.join(os.getcwd(), 'temp_script.py')
    temp_file_copy = os.path.join(os.getcwd(), 'last_temp_script.py')
    
    with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
        temp_file.write(wrapped_code)
        temp_file.flush()
    
    with open(temp_file_copy, 'w', encoding='utf-8') as temp_file:
        temp_file.write(wrapped_code)
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
            os.remove(temp_file_name)"""
    bot_tools.overwrite_function('auto_terminal.py', 'execute_python_code',
    new_function)
    print('The execute_python_code function has been updated in auto_terminal.py')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f"An error occurred: {str(error)}", file=sys.stderr)
        print("Local variables at the time of the error:", file=sys.stderr)
        tb = sys.exc_info()[2]
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            print(f"Frame {frame.f_code.co_name} in {frame.f_code.co_filename}:{frame.f_lineno}", file=sys.stderr)
            local_vars = dict(frame.f_locals)
            for key, value in local_vars.items():
                if not key.startswith('__') and key not in ['sys', 'traceback', 'error', 'main', 'tb', 'frame']:
                    print(f"    {key} = {value}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
