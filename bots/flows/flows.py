from typing import Dict, Any, Callable
import time
import bots
from bots.foundation.base import Bot
from bots.tools.github_tools import create_issue
from bots.tools.code_tools import view_dir, view
import bots.flows.functional_prompts as fp
import json

# Type definition for clarity
Flow = Callable[[Bot, Dict[str, Any]], None]


class BotFlow:

    def __init__(self, bot: Bot, flow_func: Callable):
        self.bot = bot
        self.flow = flow_func

    def handle(self, data: Any):
        return self.flow(self.bot, **data)


def create_issue_flow(bot: Bot, **kwargs: Dict[str, Any]):
    """Flow that creates a GitHub issue from error context"""

    bot.add_tool(create_issue)
    bot.add_tool(view_dir)
    bot.add_tool(view)
    bot.autosave = False
    repo = kwargs.get('repo', None)
    if repo is None:
        raise ValueError("kwargs must include repo name")

    sysp = "You are responsible for creating a thoroughly researched github issue."
    chain = [
        f"We are going to follow a four task process. Always focus on the current task.",
        f"Task 1: You are in {repo}. Use view_dir to take a look around.",
        f"Task 2: Please identify the potentially involved files based on this error:\n\n{json.dumps(kwargs)}",
        f"Task 3: Read all the potentially involved files and send a text block report with your diagnosis",
        f"Task 4: Thank you. Finally, use create_issue to submit the issue."
    ]

    bot.set_system_message(sysp)
    _ , _ = fp.chain_while(bot, chain, fp.conditions.tool_not_used, 'ok')