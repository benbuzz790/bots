import re
import json
import tkinter as tk
from tkinter import filedialog

# Needs a lot of work

def truncate_code_blocks(content):
    def truncate_block(match):
        lines = match.group(2).split('\n')
        truncated_lines = [lines[0]]  # Keep the first line
        truncated_lines.extend([line for line in lines if line.strip().startswith(('class', 'def'))])
        if len(truncated_lines) < len(lines):
            truncated_lines.append('[truncated]')
        return f"{match.group(1)}\n" + '\n'.join(truncated_lines) + "\n```"
    
    return re.sub(r'(```(?:python|epython))\n(.*?)\n```', truncate_block, content, flags=re.DOTALL)

def truncate_errors(content):
    error_pattern = r'(System:\n\nExecuted Code Result:\n).*?(---\n\n---\n\nBen\'s Reply:.*?)$'
    
    def truncate_error(match):
        ben_reply = match.group(2)
        return f"{match.group(1)}Errors [truncated]\n\n{ben_reply}"
    
    return re.sub(error_pattern, truncate_error, content, flags=re.DOTALL)

def process_bot_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    for message in data['conversation']:
        if 'content' in message:
            message['content'] = truncate_code_blocks(message['content'])
            message['content'] = truncate_errors(message['content'])
    
    return json.dumps(data, indent=2)

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    file_path = filedialog.askopenfilename(
        title="Select .bot file to truncate",
        filetypes=[("Bot files", "*.bot"), ("All files", "*.*")]
    )

    if not file_path:
        print("No file selected. Exiting.")
        return

    truncated_content = process_bot_file(file_path)

    output_file_path = filedialog.asksaveasfilename(
        title="Save truncated .bot file",
        defaultextension=".bot",
        filetypes=[("Bot files", "*.bot"), ("All files", "*.*")]
    )

    if not output_file_path:
        print("No output file selected. Exiting.")
        return

    with open(output_file_path, 'w') as file:
        file.write(truncated_content)

    print(f"Truncated .bot file has been created as '{output_file_path}'")

if __name__ == "__main__":
    main()