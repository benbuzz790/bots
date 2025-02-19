import traceback
import textwrap
import os
import time
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
        bot_file_list = _get_new_files(start_time, '.bot')


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
        os.makedirs('clones', exist_ok=True)


        bot_list = []
        for bot_file in bot_file_list:
            bot_list.append(load(bot_file))


        debug_results= fp.par_dispatch(
            bot_list = bot_list, 
            functional_prompt = fp.prompt_while,
            first_prompt = prompts.file_debug,
            continue_prompt = "ok",
            stop_condition = fp.conditions.tool_not_used_debug)


        for bot in bot_list:
            bot = load(bot_file)
            _, _ = fp.prompt_while(
                bot = bot, 
                first_prompt='Use powershell and ghapi to commit and merge your changes. Be methodical.'
                )


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
