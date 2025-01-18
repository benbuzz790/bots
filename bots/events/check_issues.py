from typing import Dict, Any
from bots.foundation.base import Bot
from bots.flows.flows import resolve_issue_flow
from bots.tools.github_tools import list_issues, get_issue
import json


def run_resolve(bot: Bot, **kwargs: Dict[str, Any]):
    """Flow that checks for issues tagged as 'ready' and initiates resolution"""
    print('looking for issues')
    repo = kwargs.get('repo', None)
    issues_response = list_issues(repo_full_name=repo, state='open')
    print(f'repo={repo}')
    print(f'issues={issues_response}')
    issues = json.loads(issues_response)
    count = 0
    for issue in issues:
        count = count + 1
        print(count)
        if any(label['name'].lower() == 'ready' for label in issue.get('labels', [])):
            issue_number = issue['number']
            print('ready found')
            resolve_issue_flow(bot, repo=repo, issue_number=issue_number)

def setup_issue_checker(event_system, bot: Bot):
    """Sets up hourly checking of ready issues"""
    event_system.schedule_bot(
        name='check_ready_issues', 
        bot=bot, 
        flow_name=run_resolve.__name__, 
        cron='* * * * *'
    )

def main():
    from bots import AnthropicBot
    from bots.events import BotEventSystem
    import os
    
    # Initialize bot with appropriate model and settings
    bot = AnthropicBot(
        name="Issue-Resolver",
        temperature=0.5,  # More focused/deterministic
        max_tokens=4096 
    )
    
    # Create event system
    event_system = BotEventSystem()
    
    # Set up the checker with our repo
    setup_issue_checker(event_system, bot)
    
    # Start the event system
    print("Starting issue checker. Press Ctrl+C to stop.")
    event_system.start()
    
    try:
        # Keep the main thread alive
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping issue checker...")
        event_system.stop()

if __name__ == '__main__':
    main()