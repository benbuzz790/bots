from typing import Dict, Any, Callable
import time
import bots
from bots.foundation.base import Bot
from bots.tools.github_tools import create_issue, list_issues, get_issue
from bots.tools.code_tools import view_dir, view
from bots.tools import python_tools, terminal_tools
import bots.flows.functional_prompts as fp
import json
import textwrap
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
    bot.add_tool(list_issues)
    bot.autosave = False
    repo = kwargs.get('repo', None)
    if repo is None:
        raise ValueError('kwargs must include repo name')
    sysp = (
        'You are responsible for creating a thoroughly researched github issue.'
        )
    chain = [
        f'We are going to follow a five task process. Always focus on the current task.'
        , f'Task 1: You are in {repo}. Use view_dir to take a look around.',
        textwrap.dedent(
        f"""Task 2: Please identify the potentially involved files based on this error:
            {json.dumps(kwargs)}
            """
        ),
        f'Task 3: Read all the potentially involved files and send a text block report with your diagnosis'
        ,
        f"Task 4: use list_issues and investigate whether this is/would be a duplicate issue,Task 5: Finally, if this would not be a duplicate, use create_issue to submit the issue, otherwise just reply with 'done'. Thanks!"
        ]
    bot.set_system_message(sysp)
    _, _ = fp.chain_while(bot, chain, fp.conditions.tool_not_used, 'ok')


def resolve_issue_flow(bot: Bot, **kwargs: Dict[str, Any]):
    """Flow that systematically resolves a GitHub issue with human oversight at each step"""
    bot.add_tool(view_dir)
    bot.add_tool(view)
    bot.add_tools(python_tools)
    bot.add_tools(terminal_tools)
    repo = kwargs.get('repo', None)
    issue_number = kwargs.get('issue_number', None)
    print(f'repo: {repo}')
    print(f'issue_number: {issue_number}')
    if repo is None or issue_number is None:
        raise ValueError('kwargs must include repo name and issue number')
    sysp = (
        'You are a methodical developer responsible for resolving issues. Always view files before making changes.'
        )
    chain = [
        f"Task 1: Let's examine the issue in {repo}. Use view to read ISSUE.md."
        , f'Task 2: Use view_dir to understand the codebase structure.',
        f'Task 3: Create scratch.py and attempt to replicate the issue. Use execute_python_code to test.'
        ,
        f"Task 4: Now that we've replicated the issue, propose a fix approach for review."
        , f'Task 5: Implement and test the fix in scratch.py first.',
        f'Task 6: After confirmation, implement the fix in the actual codebase.'
        ,
        f'Task 7: Verify the fix works by running the test case from the issue.'
        ]
    bot.set_system_message(sysp)

    def stop_cond(bot):
        print(bot.conversation.content)
        return fp.conditions.tool_not_used(bot)
    return fp.chain_while(bot, chain, stop_cond, 'ok')
