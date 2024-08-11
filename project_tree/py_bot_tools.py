import logging
from src.bot_tools import execute_python_code as btepc


def execute_python_code(code, timeout=300):
    """
    Executes python code in a safe environment.

    Use this function to help you debug tricky problems by running small tests or verifications.
    Do not use this function when asked to write code.

    Parameters:
    - code (str): Syntactically correct python code.

    Returns:
    - stdout (str): Standard output from running the code
    - error (str): A description of the error if the code ran incorrectly
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info(f"Bot requested code execution: {code}")   
    result = btepc(code, timeout)
    logger.info(f"Bot tool execution result: {result}")
    
    return result