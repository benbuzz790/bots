import argparse
import os
import time

import bots.flows.functional_prompts as fp
import bots.tools.terminal_tools as terminal_tools
from bots.dev.decorators import debug_on_error
from bots.flows.project_tree import project_tree_tools as ptt
from bots.flows.project_tree.project_tree_prompts import prompts
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import load
from bots.utils.helpers import _get_new_files


def _initialize_root_bot():
    """Initialize the project root bot with necessary tools."""
    root_bot = AnthropicBot(name="project_Claude")
    root_bot.add_tools(ptt)
    root_bot.add_tools(terminal_tools)
    root_bot.set_system_message(prompts.root_initialization)
    root_bot.save(root_bot.name)
    return root_bot


def generate_project(spec: str):
    """
    Executes the simplified process for project generation:
    1. Root bot analyzes spec and designs architecture
    2. Root bot creates requirements for each file
    3. File bots are created and implement their files
    4. File bots debug their implementations
    Parameters:
    - spec (str): Project specification text
    Returns success or error message string.
    """
    try:
        # Step 1: Analyze specification and design architecture
        print("----- Analyzing Specification -----")
        root_bot = _initialize_root_bot()
        response = root_bot.respond(prompts.root_breakdown_spec(spec))
        print("root: " + response)
        # Step 2: Create file bots for each component
        print("----- Creating File Bots -----")
        start_time = time.time()
        responses, _ = fp.prompt_while(
            bot=root_bot,
            first_prompt=prompts.root_make_bots(),
            continue_prompt=prompts.root_continue,
            stop_condition=fp.conditions.tool_not_used,
        )
        print("root: " + "\n".join(responses))
        # Get all newly created bot files
        bot_file_list = _get_new_files(start_time, extension=".bot")
        # Step 3: Create requirements for each file bot
        print("----- Creating Requirements -----")
        _, nodes = fp.prompt_for(
            bot=root_bot,
            items=bot_file_list,
            dynamic_prompt=prompts.root_make_req,
            should_branch=False,
        )
        # Step 4: Have each file bot create their files in parallel
        print("----- File Bots Creating Files -----")
        bot_list = [AnthropicBot.load(f) for f in bot_file_list]
        bot_names = []
        for f in bot_file_list:
            name = os.path.basename(f).replace(".bot", "")
            bot_names.append(name)
        prompt_list = [prompts.file_create_files(n) for n in bot_names]
        for bot, prompt in zip(bot_list, prompt_list):
            msg_part1 = prompt + "\n Do not act until after the next prompt."
            message = msg_part1 + " I'll say 'go'."
            bot.respond(message)
        fp.par_dispatch(
            bot_list,
            fp.prompt_while,
            first_prompt="go",
            continue_prompt="ok",
            stop_condition=fp.conditions.tool_not_used_debug,
        )
        # Step 5: Have each file bot debug their implementations serially
        print("----- File Bots Debugging -----")
        for bot_file in bot_file_list:
            bot_name = os.path.basename(bot_file).replace(".bot", "")
            print(f"Instructing {bot_name} to debug...")
            # Load the bot and instruct it to debug
            bot = load(bot_file)
            responses, _ = fp.prompt_while(
                bot=bot,
                first_prompt=prompts.file_debug(),
                continue_prompt=prompts.file_continue,
                stop_condition=fp.conditions.tool_not_used_debug,
            )
            print(f"{bot_name}: " + "\n".join(responses))
        print("----- Project Generation Complete -----")
        return "success"
    except Exception as error:
        raise error


# Main
@debug_on_error
def main(prompt_file=None):
    """
    Run the project generator with either a file input or default prompts.
    Args:
        prompt_file (str, optional): Path to the prompt file to load.
                                   If None, uses default prompts.
    """
    if prompt_file:
        with open(prompt_file, "r") as f:
            prompt_content = f.read()
        generate_project(prompt_content)
    else:
        generate_project(prompts.fastener_analysis)


def run_from_command_line():
    """Parse command line arguments and run the generator."""
    description = "Generate project from prompt file"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--file", "-f", type=str, help="Path to prompt file")
    args = parser.parse_args()
    main(args.file)


if __name__ == "__main__":
    run_from_command_line()
