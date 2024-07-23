# Bot File Manipulation Tools

This document outlines the tools available for bots to manipulate Python files programmatically.

## Available Tools

1. rewrite(file_path, content):
   Overwrites a file with new content.

2. replace_string(file_path, old_string, new_string):
   Replaces the instances of a string in a file.

3. replace_class(file_path, new_class_def, old_class_name=None):
   Replaces old_class_name with a new class definition. If old_class_name is None, tries to replace using new_class_def's name.

4. replace_function(file_path, new_function_def):
   Replaces an existing function definition.

5. add_function_to_class(file_path, class_name, new_method_def):
   Adds a new method to an existing class.

6. add_class_to_file(file_path, class_def):
   Adds a new class definition to a file.

7. append(file_path, content_to_append):
   Appends content to a file.

8. prepend(file_path, content_to_prepend):
   Prepends content to a file.

9. delete_match(file_path, pattern):
   Deletes lines containing a specified pattern.

## Usage

Import the tools:
import src.bot_tools as bt

Example usage:
bt.rewrite('example.py', 'print("Hello, World!")')
bt.append('example.py', '\n# This is a comment')
bt.replace_function('example.py', 'def greet():\n    print("Hello, user!")')

Note: These tools modify files directly. Use with caution.
