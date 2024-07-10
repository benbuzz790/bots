import re
import subprocess
import bots



def remove_code_blocks(text):
    return bots.remove_code_blocks(text)

def execute_code_blocks(code_blocks, labels):
    output = 'Executed Code Result:\n'
    for code, label in zip(code_blocks, labels):
        if label.lower() == 'powershell':
            try:
                result = subprocess.run(['powershell', '-Command', code], capture_output=True, text=True, timeout=30)
                output += result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                output += 'Error: Command execution timed out after 30 seconds.'
            except Exception as e:
                output += f'Error: {str(e)}'
        else:
            output += f'Skipping code block with label "{label}" as it is not recognized as PowerShell code.\n'
        output = output + '\n---\n'
    return output
# Test the code block extraction and execution
text = '''
This is a sample text with code blocks.
```powershell
Write-Output "Hello, World!"
```
```python
print("This is a Python code block.")
```
```
This is a code block without a label.
```
'''
code_blocks, labels = remove_code_blocks(text)
print("Code Blocks:")
print(code_blocks)
print("Labels:")
print(labels)
output = execute_code_blocks(code_blocks, labels)
print("Execution Output:")
print(output)