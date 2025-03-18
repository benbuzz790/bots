import traceback
import os
from typing import List, Tuple
import datetime as DT
import re
import textwrap
import ast

def _process_error(error):
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message

def _get_new_files(start_time, directory=".", extension=None):
    """Get all files created after start_time in directory that have a certain extension"""
    new_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if os.path.getctime(path) >= start_time:
                if extension is None or os.path.splitext(path)[1] == extension:
                    new_files.append(path)
                
    return new_files
 
def _clean(code: str) ->str:
    """Clean and dedent code before parsing.
    
    Args:
        code (str): The code to clean
        
    Returns:
        str: The cleaned and dedented code
    """
    return textwrap.dedent(code).strip()

def _py_ast_to_source(node):
    """Convert a python AST node to source code."""
    return ast.unparse(node)

def remove_code_blocks(text: str) ->Tuple[List[str], List[str]]:
    """Extracts code blocks from responses"""
    pattern = '```(\\w*)\\s*([\\s\\S]*?)```'
    matches = re.findall(pattern, text)
    code_blocks = [match[1].strip() for match in matches]
    labels = [match[0].strip() for match in matches]
    text = re.sub(pattern, '', text)
    return code_blocks, labels

def formatted_datetime() ->str:
    """Returns 'now' as a formatted string"""
    now = DT.datetime.now()
    return now.strftime('%Y-%m-%d_%H-%M-%S')
