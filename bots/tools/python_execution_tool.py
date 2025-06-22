import ast
import os
import subprocess
import tempfile
import textwrap
import time

from bots.dev.decorators import handle_errors
from bots.utils.helpers import _clean, _py_ast_to_source


def _get_unique_filename(base_name, extension=""):
    """Generate a unique filename using process ID and timestamp."""
    timestamp = int(time.time() * 1000)
    pid = os.getpid()
    if extension and (not extension.startswith(".")):
        extension = "." + extension
    return f"{base_name}_{pid}_{timestamp}{extension}"


@handle_errors
def _execute_python_code(code: str, timeout: int = 300) -> str:
    """
    Executes python code in a stateless environment with cross-platform
    timeout handling.
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
            sys.path.append(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))
            if sys.platform == 'win32':
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(
                    sys.stdout.buffer, 'strict')
                sys.stderr = codecs.getwriter('utf-8')(
                    sys.stderr.buffer, 'strict')
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
        # Find the main function in the wrapper AST

        def is_main_func(node):
            return isinstance(node, ast.FunctionDef) and node.name == "main"

        nodes = wrapper_ast.body
        main_func = next((node for node in nodes if is_main_func(node)))
        main_func.body = code_ast.body
        return wrapper_ast

    if not isinstance(timeout, int) or timeout <= 0:
        raise ValueError("Timeout must be a positive integer")
    code_ast = ast.parse(_clean(code))
    wrapper_ast = create_wrapper_ast()
    combined_ast = insert_code_into_wrapper(wrapper_ast, code_ast, timeout)
    final_code = _py_ast_to_source(combined_ast)
    # Use system temp directory instead of creating our own scripts directory
    temp_file_name = os.path.join(tempfile.gettempdir(), _get_unique_filename("temp_script", "py"))
    with open(temp_file_name, "w", encoding="utf-8") as temp_file:
        temp_file.write(final_code)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        ["python", temp_file_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        env=env,
    )
    stdout, stderr = process.communicate(timeout=timeout)
    # Clean up temp file
    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)
    if process.returncode != 0:
        return stderr or "Process failed with no error message"
    return stdout + stderr
