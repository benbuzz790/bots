import traceback
import textwrap
import os
import time
import bots.tools.code_tools as code_tools
import bots.tools.terminal_tools as terminal_tools
import bots.tools.python_tools as python_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import load
from bots.foundation.base import Bot
import bots.flows.functional_prompts as fp
from importlib import resources
from bots.dev.project_tree_prompts import prompts

# Should perhaps be multi-threaded

def _initialize_root_bot():
    root_bot = AnthropicBot(name="project_Claude")
    root_bot.add_tools(r"C:\Users\benbu\Code\llm-utilities-git\bots\bots\dev\project_tree_tools.py")
    root_bot.add_tools(terminal_tools)
    root_bot.save(root_bot.name)
    root_bot.set_system_message(prompts.root_initialization)
    return root_bot

def _get_new_files(start_time, directory="."):
    """Get all files created after start_time in directory"""
    new_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if os.path.getctime(path) >= start_time:
                new_files.append(path)
                
    return new_files

### Project Creation ###

def generate_project(spec: str):
    """
    Executes the standard process for project generation:
    1. Root bot processes spec and creates module requirements 
    2. Root bot creates and calls file bots for each module
    3. File bots implement code
    4. Root bot makes and commits to a new gh repo
    5. File bots debug code
    6. Root bot cleans up
    7. Root bot writes tool report
   
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
        bot_file_list = _get_new_files(start_time)

        # Create requirements for each bot
        # Interdependencies mean this is a bad branching task
        print("----- Making requirements -----")
        _, nodes = fp.prompt_for(
            bot = root_bot, 
            items = bot_file_list, 
            dynamic_prompt = prompts.root_make_req, 
            should_branch = False
            )
        
        # Create files by instructing each bot to make them in parallel
        # This is a great parallel branching task
        branch_point = root_bot.conversation.parent.parent
        print("----- Making Files -----")
        _, nodes = fp.par_branch(
            bot = root_bot,
            prompts = [prompts.root_make_files(item) for item in bot_file_list]
        )
        # return to branch point
        root_bot.conversation = branch_point

        # Verify requirements in parallel
        # This is a great parallel branching task
        print("----- Verifying Requirements -----")
        _, nodes = fp.par_branch_while(
            bot = root_bot,
            prompt_list=[prompts.root_verify_req(item) for item in bot_file_list],
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )

        # return to branch
        root_bot.conversation = branch_point
        
        # Making Repo
        _, _ = fp.prompt_while(
            bot = root_bot,
            first_prompt="INSTRUCTION: Please use powershell to commit all files and all changes. You may use the gh cli. If a repo hasn't been made, please make one (private) with the appropriate name.",
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )

        # prepare test environment
        print("----- Cleaning Directory -----")
        _, nodes = fp.prompt_while(
            bot = root_bot,
            first_prompt= "Use powershell to view files and ensure they're in the correct locations. DO NOT DELETE FILES. You may use powershell to move them.",
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )

        # prepare test environment
        print("----- Prepping Tests -----")
        _, nodes = fp.prompt_while(
            bot = root_bot,
            first_prompt= prompts.root_prep_tests(''),
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )

        # run tests via parallel branching
        branch_point = root_bot.conversation.parent.parent
        print("----- Running Tests -----")
        _, nodes = fp.par_branch_while(
            bot = root_bot,
            prompt_list = [prompts.root_run_tests(item) for item in bot_file_list],
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )
        # return to branch
        root_bot.conversation = branch_point

        print("----- Cleanup -----")
        fp.prompt_while(
            bot = root_bot,
            first_prompt = prompts.root_cleanup(),
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )

        # Commit
        _, _ = fp.prompt_while(
            bot = root_bot,
            first_prompt="INSTRUCTION: Please use powershell to commit all files and all changes.",
            continue_prompt = prompts.root_continue,
            stop_condition = fp.conditions.said_DONE
        )


        # Debugging
        # Retry debugging 4 times
        count = 0
        limit = 2
        while count < limit:
            count = count + 1
            print(f"----- Debugging with Deb iteration {count} -----")
            deb_path = r"C:\Users\benbu\Code\llm-utilities-git\bots\botlib\Deb@4Feb2025.bot"
            deb = load(deb_path)
            
            try:
                fp.prompt_while(
                    bot = deb,
                    first_prompt= prompts.deb_init,
                    continue_prompt= 'ok',
                    stop_condition= fp.conditions.tool_not_used_debug
                )
                
                # Commit
                _, _ = fp.prompt_while(
                    bot = deb,
                    first_prompt="INSTRUCTION: Please use powershell to commit all files and all changes. Be sure .gitignore includes any venv you made.",
                )
            except:
                continue

        import sys
        sys.exit(0)

        print("----- Making Demo -----")
        fp.prompt_while(
            bot = root_bot, 
            first_prompt = prompts.root_demo(),
            continue_prompt = "say command 'DONE' when demo bot has run demo successfully", 
            stop_condition = fp.conditions.said_DONE
            )
        
        # Commit
        _, _ = fp.prompt_while(
            bot = root_bot,
            first_prompt="Please use powershell to commit all files and all changes."
        )
        
        print("----- Wrapping Up -----")
        print(root_bot.respond(prompts.root_wrap_up()))

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
