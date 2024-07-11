
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from bots import BaseBot, AnthropicBot

def get_latest_bot_file(prefix='TaskBreakdownBot'):
    return r"C:\Users\Ben Rinauto\Documents\Code\llm-utilities-git\llm-utilities\task_system_experiment\TaskBreakdownBot@2024.07.11-10.32.01.bot"

def test_task_breakdown_bot():
    # Find the latest TaskBreakdownBot file or create a new one
    bot_file = get_latest_bot_file()
    if not bot_file:
        print("No existing TaskBreakdownBot found. Creating a new one.")
        bot = AnthropicBot(
            name='TaskBreakdownBot',
            role_description="a task analysis and breakdown specialist"
        )
        bot_file = bot.save()
    
    try:
        bot = BaseBot.load(bot_file)
        print(f"Successfully loaded {bot_file}")
    except Exception as e:
        print(f"Error loading bot: {str(e)}")
        return

    # Test input
    test_input = """
    Create a simple web application that allows users to create and manage a todo list. 
    The application should have the following features:
    1. User registration and login
    2. ability to add, edit, and delete todo items
    3. mark todo items as complete
    4. filter todo items by status (complete/incomplete)
    5. simple UI using HTML and CSS
    """

    # Get response from the bot
    response = bot.respond(test_input)

    print("\nBot response:")
    print(response)

    # Check if the response is in the correct JSON format
    try:
        tasks = json.loads(response)
        if isinstance(tasks, list) and all(isinstance(task, dict) for task in tasks):
            print("\nResponse is in the correct JSON format.")
            print(f"Number of subtasks generated: {len(tasks)}")
            
            # Check if each task has the required fields
            required_fields = ['id', 'title', 'description', 'status', 'priority', 'assigned_to']
            for i, task in enumerate(tasks, 1):
                missing_fields = [field for field in required_fields if field not in task]
                if missing_fields:
                    print(f"Task {i} is missing fields: {', '.join(missing_fields)}")
                else:
                    print(f"Task {i} has all required fields.")
        else:
            print("Response is not in the correct format. Expected a list of dictionaries.")
    except json.JSONDecodeError:
        print("Response is not valid JSON.")

# Run the test
if __name__ == "__main__":
    test_task_breakdown_bot()
