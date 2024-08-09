from src.bot_tools import execute_python_code as btepc

def execute_python_code(code, timeout=300):
    """
    Executes python code in a safe environment.

    Use this function to help you debug tricky problems by running small tests or verifications.

    Parameters:
    - code (str): Syntactically correct python code.

    Returns:
    - stdout (str): Standard output from running the code
    - error (str): A description of the error if the code ran incorrectly
    """
    return btepc(code, timeout)