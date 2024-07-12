
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from bots import BaseBot, AnthropicBot

def get_latest_bot_file(prefix='TaskBreakdownBot'):
    return r"C:\Users\Ben Rinauto\Documents\Code\llm-utilities-git\llm-utilities\task_system_experiment\TaskBreakdownBot@2024.07.11-10.32.01.bot"

def test_task_breakdown_bot():
    # Find the latest TaskBreakdownBot file or create a new one
    #bot_file = get_latest_bot_file()
    bot_file = None
    if not bot_file:
        print("No existing TaskBreakdownBot found. Creating a new one.")
        bot = AnthropicBot(
            name='TaskBreakdownBot',
            role_description="a task analysis and breakdown specialist"
        )
        bot.set_system_message('''You are TaskBreakdownBot, an AI assistant specialized in analyzing complex tasks and breaking them down into smaller, manageable subtasks. Your job is to take a natural language description of a task and create a series of well-structured tickets that represent the subtasks needed to complete the main task.\n\nWhen given a task description, follow these steps:\n1. Analyze the overall task and identify the main components or stages.\n2. Break down each component into smaller, actionable subtasks.\n3. For each subtask, create a ticket using the following JSON structure:\n   {\n     \"id\": \"Generate a unique ID (e.g., TASK-001)\",\n     \"title\": \"A clear, concise title for the subtask\",\n     \"description\": \"A detailed description of what needs to be done\",\n     \"status\": \"new\",\n     \"priority\": \"Assign a priority (low, medium, high)\",\n     \"assigned_to\": null\n   }\n4. Ensure that the subtasks, when completed in order, will result in the completion of the overall task.\n5. Return the list of ticket JSONs.\n\nRemember to be thorough in your breakdown, but also keep each subtask reasonably sized and actionable."''')
        bot_file = bot.save()
    
    try:
        bot = BaseBot.load(bot_file)
        print(f"Successfully loaded {bot_file}")
    except Exception as e:
        print(f"Error loading bot: {str(e)}")
        return

    # Test input
    test_input = """
    Break this down into tasks:
    Create social network, "Nudge" which sends text messages to users with suggestions about where
    they might like to spend their time that night. That decision should be made based on their 
    interests as well as the interests of other users. When enough overlapping interests are in a
    certain place, "Nudge" will inform their users about the hotspot.
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
