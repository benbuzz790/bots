import os
from typing import List, Tuple
from bots.foundation.base import Bot, Engines
from bots.foundation.anthropic_bots import AnthropicBot
from bots.flows import functional_prompts as fp
from bots.tools import code_tools

def find_python_files(start_path: str) -> List[str]:
    """
    Recursively find all Python files in a directory, excluding tools and files with 'tool' in the name.

    Args:
        start_path (str): Root directory to start search from

    Returns:
        List[str]: List of paths to Python files
    """
    python_files = []
    for root, _, files in os.walk(start_path):
        if 'tool' in root.lower():
            continue
        for file in files:
            if file.endswith('.py') and 'tool' not in file.lower():
                python_files.append(os.path.join(root, file))
    return python_files

def create_doc_review_bot() -> Bot:
    """
    Create and configure a bot for documentation review.

    Returns:
        Bot: Configured bot with necessary tools and context
    """
    bot = AnthropicBot(model_engine=Engines.CLAUDE3_SONNET, temperature=0.7, name='DocReviewer', role='Documentation Specialist', role_description='You are an expert in Python documentation standards and best practices.')
    bot.add_tools(code_tools)
    return bot

def review_file_documentation(bot: Bot, file_path: str) -> Tuple[List[str], List[Bot.ConversationNode]]:
    """
    Review documentation for a single file using chain_while pattern.

    Args:
        bot (Bot): Configured documentation review bot
        file_path (str): Path to the Python file to review

    Returns:
        Tuple[List[str], List[Bot.ConversationNode]]: Responses and conversation nodes
    """
    prompts = ["First, let's read the project context. Please read bot_context.txt and README.md to understand the project.", f"Now, let's examine {file_path}. Please read this file and analyze its documentation.", "Review the file's documentation. Check for:\n" + '1. Module-level docstring\n' + '2. Class docstrings\n' + '3. Method/function docstrings\n' + '4. Type hints\n' + '5. Appropriate inline comments\n' + 'If you find any issues, use the appropriate tools to fix them.', 'Make any final documentation improvements needed.']
    return fp.chain_while(bot, prompts, stop_condition=fp.conditions.tool_not_used, continue_prompt='Continue reviewing and improving the documentation. Are there any other issues to address?')

def main():
    """
    Main function to coordinate documentation review across all Python files.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    python_files = find_python_files(project_root)
    bots = [create_doc_review_bot() for _ in python_files]
    kwargs_list = [{'file_path': file} for file in python_files]
    results = fp.par_dispatch(bot_list=bots, functional_prompt=review_file_documentation, **kwargs_list[0])
    for file_path, (responses, nodes) in zip(python_files, results):
        print(f'\nDocumentation review completed for {file_path}')
        if responses:
            print('Last response:', responses[-1])
'\nScript to automatically review and improve code-level documentation using bots.\n\nThis script:\n1. Finds all Python files in the project\n2. Creates multiple bots to review documentation in parallel\n3. Uses chain_while to ensure thorough documentation review\n4. Provides suggestions for documentation improvements\n'
if __name__ == '__main__':
    main()