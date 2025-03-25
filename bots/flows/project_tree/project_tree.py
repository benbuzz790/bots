import traceback
import textwrap
import os
import time
import shutil
import bots.tools.code_tools as code_tools
import bots.tools.terminal_tools as terminal_tools
import bots.tools.python_editing_tools as python_editing_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import load
from bots.foundation.base import Bot
import bots.flows.functional_prompts as fp
from importlib import resources
from bots.flows.project_tree.project_tree_prompts import prompts
from bots.utils.helpers import _get_new_files
from bots.flows.project_tree import project_tree_tools as ptt

# Should perhaps be multi-threaded
# TODO fix hardcoded location
def _initialize_root_bot():
    root_bot = AnthropicBot(name="project_Claude")
    root_bot.add_tools(ptt)
    root_bot.add_tools(terminal_tools)
    root_bot.save(root_bot.name)
    root_bot.set_system_message(prompts.root_initialization)
    return root_bot

def _merge_bot_changes(bot_name, branch_name, clone_dir, original_dir):
    """
    Merge changes from a bot's branch back into the main branch.
    
    Parameters:
    - bot_name (str): Name of the bot
    - branch_name (str): Name of the branch containing the bot's changes
    - clone_dir (str): Directory containing the bot's clone
    - original_dir (str): Original project directory
    
    Returns:
    - bool: True if merge successful, False otherwise
    """
    # Commit changes in the bot's directory
    os.chdir(clone_dir)
    os.system('git add .')
    os.system(f'git commit -m "Changes from {bot_name}"')
    os.chdir(original_dir)
    
    # Pull changes from bot's branch
    os.system(f'git fetch {clone_dir} {branch_name}')
    
    # Merge changes
    merge_result = os.system(f'git merge FETCH_HEAD --no-ff -m "Merge changes from {bot_name}"')
    
    if merge_result != 0:
        print(f"⚠️ Merge conflict detected with {bot_name}'s changes")
        # Handle merge conflicts as needed
        os.system('git merge --abort')
        print(f"Changes from {bot_name} were not merged automatically")
        return False
    
    return True

### Project Creation ###

def generate_project(spec: str):
    """
    Executes the standard process for project generation:
   
    Parameters:
    - spec (str): Project specification text
   
    Returns success or error message string.
    """
    
    try:
        # Decide on structure
        print("----- Making Spec -----")
        root_bot = _initialize_root_bot()
        response = root_bot.respond(prompts.root_breakdown_spec(spec))
        print("root: " + response)

        # Make other bots
        print("----- Making Bots -----")
        start_time = time.time()
        responses, _ = fp.prompt_while(
            bot = root_bot, 
            first_prompt = prompts.root_make_bots(), 
            continue_prompt = prompts.root_continue, 
            stop_condition = fp.conditions.tool_not_used
            )
        print("root: "+ '\n'.join(responses))
        
        # get all new file bots
        bot_file_list = _get_new_files(start_time, extension='.bot')

        # Create requirements for each bot
        print("----- Making requirements -----")
        _, nodes = fp.prompt_for(
            bot = root_bot, 
            items = bot_file_list, 
            dynamic_prompt = prompts.root_make_req, 
            should_branch = False
            )
        
        # Create files by instructing each bot to make them in parallel
        branch_point = root_bot.conversation.parent.parent
        print("----- Making Files -----")
        _, nodes = fp.par_branch(
            bot = root_bot,
            prompts = [prompts.root_make_files(item) for item in bot_file_list]
        )
        # return to branch point
        root_bot.conversation = branch_point

        # Clone and debug
        print("----- Setting up Git and Clones -----")
        os.makedirs('clones', exist_ok=True)
        
        # Ensure we're in a git repo and have an initial commit
        if not os.path.exists('.git'):
            os.system('git init')
            os.system('git add .')
            os.system('git commit -m "Initial project structure"')
        
        bot_list = []
        bot_branches = {}
        original_dir = os.getcwd()
        
        for bot_file in bot_file_list:
            # Extract bot name from file path
            bot_name = os.path.basename(bot_file).replace('.bot', '')
            branch_name = f"bot-{bot_name}-{int(time.time())}"
            bot_branches[bot_name] = branch_name
            
            print(f"Creating clone for {bot_name}...")
            
            # Create a dedicated clone directory
            clone_dir = os.path.join('clones', bot_name)
            os.makedirs(clone_dir, exist_ok=True)
            
            # Create a new branch for this bot
            os.system(f'git checkout -b {branch_name}')
            
            # Clone the repo to the dedicated directory
            os.system(f'git clone --branch {branch_name} . {clone_dir}')
            
            # Copy the bot file to the cloned directory
            bot_file_name = os.path.basename(bot_file)
            shutil.copy(bot_file, os.path.join(clone_dir, bot_file_name))
            
            # Return to main branch
            os.system('git checkout main || git checkout master')
            
            # Load the bot from the cloned directory
            cloned_bot_path = os.path.join(clone_dir, bot_file_name)
            bot = load(cloned_bot_path)  # This will set the working directory correctly
            bot_list.append(bot)
        
        # Run debugging with all bots
        print("----- Debugging -----")
        debug_results = fp.par_dispatch(
            bot_list=bot_list, 
            functional_prompt=fp.prompt_while,
            first_prompt=prompts.file_debug(),
            continue_prompt="ok",
            stop_condition=fp.conditions.tool_not_used_debug
        )
        
        # After debugging, merge changes from each bot
        print("----- Merging Changes -----")
        os.chdir(original_dir)  # Return to the original directory
        
        for bot in bot_list:
            bot_name = bot.name
            branch_name = bot_branches.get(bot_name)
            clone_dir = os.path.join('clones', bot_name)
            
            print(f"Merging changes from {bot_name}...")
            merge_successful = _merge_bot_changes(bot_name, branch_name, clone_dir, original_dir)
            if not merge_successful:
                print(f"Manual intervention may be required for {bot_name}'s changes")

        # Optional: Uncomment the following sections as needed

        # # return to branch
        # root_bot.conversation = branch_point
        
        # print("----- Running Tests -----")
        # _, nodes = fp.par_branch_while(
        #     bot = root_bot,
        #     prompt_list=[prompts.root_run_tests(item) for item in bot_file_list],
        #     continue_prompt = "ok",
        #     stop_condition = fp.conditions.tool_not_used
        # )      

        # print("----- Making Repo -----")
        # _, _ = fp.prompt_while(
        #     bot = root_bot,
        #     first_prompt="INSTRUCTION: Please use powershell to commit all files and all changes except venvs. You may use the gh cli. If a repo hasn't been made, please make one (private) with the appropriate name.",
        #     continue_prompt = prompts.root_continue,
        #     stop_condition = fp.conditions.said_DONE_debug
        # )

        # # prepare test environment
        # print("----- Cleaning Directory -----")
        # _, nodes = fp.prompt_while(
        #     bot = root_bot,
        #     first_prompt= "Use powershell to view files and ensure they're in the correct locations. DO NOT DELETE FILES. You may use powershell to move them.",
        #     continue_prompt = prompts.root_continue,
        #     stop_condition = fp.conditions.said_DONE_debug
        # )

        # input("press any key to continue to prepping tests")

        # # prepare test environment
        # print("----- Prepping Tests -----")
        # _, nodes = fp.prompt_while(
        #     bot = root_bot,
        #     first_prompt= prompts.root_prep_tests(''),
        #     continue_prompt = prompts.root_continue,
        #     stop_condition = fp.conditions.said_DONE_debug
        # )

        # input("press any key to continue to running tests and remaining items")

        # # run tests via parallel branching
        # branch_point = root_bot.conversation.parent.parent
        # print("----- Running Tests -----")
        # _, nodes = fp.par_branch_while(
        #     bot = root_bot,
        #     prompt_list = [prompts.root_run_tests(item) for item in bot_file_list],
        #     continue_prompt = prompts.root_continue,
        #     stop_condition = fp.conditions.said_DONE_debug
        # )
        # # return to branch
        # root_bot.conversation = branch_point

        # print("----- Cleanup -----")
        # fp.prompt_while(
        #     bot = root_bot,
        #     first_prompt = prompts.root_cleanup(),
        #     continue_prompt = prompts.root_continue,
        #     stop_condition = fp.conditions.said_DONE_debug
        # )

        # # Commit
        # _, _ = fp.prompt_while(
        #     bot = root_bot,
        #     first_prompt="INSTRUCTION: Please use powershell to commit all files except venvs and all changes.",
        #     continue_prompt = prompts.root_continue,
        #     stop_condition = fp.conditions.said_DONE_debug
        # )
        
        # print("----- Wrapping Up -----")
        # print(root_bot.respond(prompts.root_wrap_up()))

    except Exception as error:
       raise error
   
    return "success"


### Main ###
import sys
import argparse
from bots.dev.decorators import debug_on_error

@debug_on_error
def main(prompt_file=None):
    """
    Run the project generator with either a file input or default prompts.
    
    Args:
        prompt_file (str, optional): Path to the prompt file to load.
                                   If None, uses default prompts.
    """
    if prompt_file:
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        generate_project(prompt_content)
    else:
        generate_project(prompts.fastener_analysis)

def run_from_command_line():
    """Parse command line arguments and run the generator."""
    parser = argparse.ArgumentParser(description='Generate project from prompt file')
    parser.add_argument('--file', '-f', type=str, help='Path to prompt file')
    args = parser.parse_args()
    main(args.file)

if __name__ == '__main__':
    run_from_command_line()
