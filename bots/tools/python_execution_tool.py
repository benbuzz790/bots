import textwrap, ast, os, subprocess, traceback
from bots.utils.helpers import _clean
from bots.utils.helpers import _py_ast_to_source



def _execute_python_code(code: str, timeout: int=300) ->str:
    """
    Executes python code in a stateless environment with cross-platform timeout handling.

    Parameters:
    - code (str): Syntactically correct python code
    - timeout (int): Maximum execution time in seconds (default: 300)

    Returns stdout or an error message.

    cost: varies
    """

    def create_wrapper_ast():
        wrapper_code = textwrap.dedent(
            """
            import os
            import sys
            import traceback
            import time
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            if sys.platform == 'win32':
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

            def main():
                pass  # Placeholder for user code

            if __name__ == '__main__':
                try:
                    main()
                except Exception as error:
                    print(f"An error occurred: {str(error)}", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                    sys.exit(1)
            """
            )
        return ast.parse(wrapper_code)

    def insert_code_into_wrapper(wrapper_ast, code_ast, timeout_value):
        main_func = next(node for node in wrapper_ast.body if isinstance(
            node, ast.FunctionDef) and node.name == 'main')
        main_func.body = code_ast.body
        return wrapper_ast
    try:
        if not isinstance(timeout, int) or timeout <= 0:
            return _process_error(ValueError(
                'Timeout must be a positive integer'))
        try:
            code_ast = ast.parse(_clean(code))
        except SyntaxError as e:
            return f'SyntaxError: {str(e)}'
        wrapper_ast = create_wrapper_ast()
        combined_ast = insert_code_into_wrapper(wrapper_ast, code_ast, timeout)
        final_code = _py_ast_to_source(combined_ast)
    except Exception as e:
        return _process_error(e)
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(package_root, 'scripts')
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
    temp_file_name = os.path.join(scripts_dir, f'temp_script_{os.getpid()}.py')
    try:
        with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
            temp_file.write(final_code)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        process = subprocess.Popen(['python', temp_file_name], stdout=
            subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding=
            'utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name ==
            'nt' else 0, env=env)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode != 0:
                return stderr or 'Process failed with no error message'
            return stdout + stderr
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
            return f'Error: Code execution timed out after {timeout} seconds'
    except Exception as e:
        return _process_error(e)
    finally:
        try:
            if os.path.exists(temp_file_name):
                os.remove(temp_file_name)
        except Exception:
            pass



def _process_error(error: Exception) ->str:
    """Format error message with traceback."""
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message
