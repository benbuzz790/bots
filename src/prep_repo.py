import os
import sys
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.anthropic_bots import AnthropicBot
from src.bot_tools import rewrite


def get_modified_files(directory: str, reference_file: str) -> list[str]:
    """
    Get a list of Python files in the directory that have been modified more recently than the reference file.

    Args:
        directory (str): The directory to search for modified files.
        reference_file (str): The reference file to compare modification times against.

    Returns:
        list[str]: A list of paths to modified Python files.
    """
    reference_time: float = os.path.getmtime(reference_file)
    modified_files: list[str] = []
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            file_path: str = os.path.join(directory, filename)
            if os.path.getmtime(file_path) > reference_time and "__" not in filename:
                modified_files.append(file_path)
    return modified_files


def read_file_content(file_path: str) -> str:
    """
    Read and return the content of a file.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def update_readme_for_file(readme_content: str, file_path: str) -> None:
    """
    Update the README.md content for a single file using the bot.

    Args:
        readme_content (str): The current content of the README.md file.
        file_path (str): The path to the Python file to be included in the README.
    """
    bot: AnthropicBot = AnthropicBot(
        name='READMEUpdaterBot',
        role='assistant',
        role_description='A helpful AI assistant for updating README.md files.'
    )
    bot.add_tool(rewrite)
    file_content: str = read_file_content(file_path)
    prompt: str = f"""Please update the README.md file to incorporate changes from the 
following Python file:

File: {file_path}
Content:
```python
{file_content}
```

Current README.md content:
```markdown
{readme_content}
```

Use the rewrite tool to write an updated version of the entire README.md file that includes 
information about this file. If a section for this file already exists, update it. If not, 
add a new section for this file. Maintain the overall structure and any existing information 
from the current README. If the README already looks accurate, you may simply respond with,
"already done".
"""
    bot.respond(prompt)


def update_file_formatting(file_path: str) -> None:
    """
    Update a single Python file to ensure it has type hints, PEP8 formatting, and consistent line width.
    
    Args:
        file_path (str): The path to the Python file to be updated.
    """
    bot: AnthropicBot = AnthropicBot(
        name="CodeFormatterBot",
        role="assistant",
        role_description="A helpful AI assistant for formatting Python code."
    )
    bot.add_tool(rewrite)

    file_content: str = read_file_content(file_path)
    
    prompt: str = f"""Please update the following Python file to ensure it has:
1. Type hints on all variables
2. PEP8 formatting
3. Consistent total line width (maximum of 100 characters per line)

File: {file_path}
Content:
```python
{file_content}
```

Please use the rewrite tool to rewrite the entire updated file. Make sure to preserve the 
functionality and docstrings. This is a formatting task ONLY. Use the rewrite tool to 
replace the entire content of the file with the updated version. DO NOT change the code.
DO NOT change how imports are written.
"""
    bot.respond(prompt)


def find_python_files(project_root: str) -> list[str]:
    """
    Find all Python files in the src directory.

    Args:
        project_root (str): The root directory of the project.

    Returns:
        list[str]: A list of paths to Python files.
    """
    python_files: list[str] = []
    for directory in ['src']:
        dir_path: str = os.path.join(project_root, directory)
        python_files.extend([os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.py')])
    return python_files


def main() -> None:
    src_directory: str = os.path.dirname(os.path.abspath(__file__))
    project_root: str = os.path.dirname(src_directory)
    readme_path: str = os.path.join(project_root, 'README.md')
    
    # Find all Python files
    python_files: list[str] = find_python_files(project_root)

    # Ensure all Python files have type hints, PEP8 formatting, and consistent line width
    for file_path in python_files:
        print(f"Updating {os.path.basename(file_path)} for type hints, PEP8, and line width...")
        update_file_formatting(file_path)

    # Update README for modified files
    modified_files: list[str] = get_modified_files(src_directory, readme_path)
    readme_content: str = read_file_content(readme_path)
    for file_path in modified_files:
        print(f"Updating README for {os.path.basename(file_path)}...")
        update_readme_for_file(readme_content, file_path)



    print("All files have been processed successfully.")


if __name__ == '__main__':
    main()