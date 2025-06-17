"""Basic bot usage example with file reading capabilities.

This example demonstrates the fundamental concepts of the bots framework
through a simple file reading implementation. It serves as a starting
point for new users to understand:

1. How to create a basic tool function with proper documentation
2. How to initialize an Anthropic-based bot
3. How to add custom tools to a bot
4. How to start an interactive chat session

This is part of the examples package which provides various demonstrations
of the bots framework capabilities.
"""

import bots


def read_file(file_path: str) -> str:
    """Read and return the contents of a text file using UTF-8 encoding.

    Use when you need to read the contents of a text file from the filesystem.
    The function handles common file operations errors and uses UTF-8 encoding
    by default.

    Parameters:
    - file_path (str): The path to the file to be read. Can be relative or
        absolute.

    Returns:
    str: Either:
        - The contents of the file as a string if successful
        - An error message starting with 'Error: ' if the operation fails
            (e.g., file not found, permission denied, encoding issues)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error: {str(e)}"


# Initialize an Anthropic-based bot
bot = bots.AnthropicBot()

# Add our file reading tool to the bot's capabilities
bot.add_tools(read_file)

# Start an interactive chat session where you can ask the bot to read files
bot.chat()
