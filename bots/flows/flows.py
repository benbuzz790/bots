from typing import Dict, Any, Callable
from bots.foundation.base import Bot
from bots.tools.code_tools import view_dir, view
import bots.flows.functional_prompts as fp
import json

"""Type for clarity"""
Flow = Callable[[Bot, Dict[str, Any]], None]


class BotFlow:

    def __init__(self, bot: Bot, flow_func: Callable):
        self.bot = bot
        self.flow = flow_func

    def handle(self, data: Any):
        return self.flow(self.bot, **data)


def make_issue_upon_error(bot: Bot, **kwargs: Dict[str, Any]):
    """Flow that creates a GitHub issue from error context"""
    bot.add_tools(view_dir)
    bot.add_tools(view)
    bot.autosave = False
    repo = kwargs.get('repo', None)
    if repo is None:
        raise ValueError('kwargs must include repo name')
    sysp = ('You are responsible for creating a thoroughly researched github issue.')
    chain = [
        f'We are going to follow a six INSTRUCTION process. Always focus on the current INSTRUCTION. Creating an issue is the final instruction, so do not make one until then.',
        f'INSTRUCTION 1: You are in {repo}. Use view_dir to take a look around.',
        f'INSTRUCTION 2: Use your the ghcli and your powershell tool to identify the exact repo being worked on'
        f'INSTRUCTION 3: Please identify the potentially involved files based on this error:{json.dumps(kwargs)}',
        f'INSTRUCTION 4: Read all the potentially involved files and send a text block report with your diagnosis',
        f"INSTRUCTION 5: list issues using ghcli and powershell, and investigate whether this is/would be a duplicate issue",
        f"INSTRUCTION 6: Finally, if this would not be a duplicate, use create_issue to submit the issue, otherwise just reply with 'done'. Thanks!"
        ]
    bot.set_system_message(sysp)
    _, _ = fp.chain_while(bot, chain, fp.conditions.tool_not_used, 'ok')

def make_doc_flow(bot: Bot, **kwargs: Dict[str, Any]):
    import bots.tools.meta_tools as mt
    import bots.tools.code_tools as ct
    import bots.tools.terminal_tools as tt
    raise NotImplementedError
    bot.add_tools(ct)
    bot.add_tools(tt)
    bot.add_tools(mt)
    prompts = [
        'We are going to document this repo in a multi-step process. always focus on the current STEP.',
        'STEP 1: View the directory',
        'STEP 2: For each python file in the directory, initialize a file bot. Do this in batches of about 10 parallel tool calls, and continue until all files have a bot.'
        'STEP 3: View the directory for .py and .bot files and create the remaining bots if you haveve missed some.'
        'STEP 4: '
    ]
