#!/usr/bin/env python3
"""
Simple Task Manager
A command-line application to manage your daily tasks.
"""

import json
import os
from datetime import datetime

class TaskManager:
    def __init__(self, filename='tasks.json'):
        self.filename = filename
        self.tasks = self.load_tasks()

    def load_tasks(self):
        """Load tasks from JSON file."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return []

    def save_tasks(self):
        """Save tasks to JSON file."""
        with open(self.filename, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    def add_task(self, title, description=''):
        """Add a new task."""
        task = {
            'id': len(self.tasks) + 1,
            'title': title,
            'description': description,
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        self.tasks.append(task)
        self.save_tasks()
        print(f"✓ Task added: {title}")

    def list_tasks(self):
        """Display all tasks."""
        if not self.tasks:
            print("No tasks found!")
            return

        print("
" + "="*50)
        print("YOUR TASKS")
        print("="*50)
        for task in self.tasks:
            status = "✓" if task['completed'] else "○"
            print(f"{status} [{task['id']}] {task['title']}")
            if task['description']:
                print(f"    {task['description']}")
        print("="*50 + "
")

    def complete_task(self, task_id):
        """Mark a task as completed."""
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed'] = True
                self.save_tasks()
                print(f"✓ Task {task_id} marked as complete!")
                return
        print(f"Task {task_id} not found.")

if __name__ == '__main__':
    manager = TaskManager()

    # Example usage
    print("Welcome to Task Manager!")
    manager.add_task("Learn Python", "Complete the Python tutorial")
    manager.add_task("Write documentation", "Document the new features")
    manager.add_task("Review code", "Review pull requests")
    manager.list_tasks()
