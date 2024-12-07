import os

def save_py_structure(start_path='.', output_file='structure.txt'):
    with open(output_file, 'w') as f:
        for root, dirs, files in os.walk(start_path):
            # Only include directories that have .py files somewhere in their tree
            has_py = False
            for _, _, fs in os.walk(root):
                if any(f.endswith('.py') for f in fs):
                    has_py = True
                    break
            
            if has_py:
                level = root.replace(start_path, '').count(os.sep)
                indent = '    ' * level
                f.write(f'{indent}{os.path.basename(root)}/\n')
                
                # List python files in this directory
                subindent = '    ' * (level + 1)
                for file in files:
                    if file.endswith('.py'):
                        f.write(f'{subindent}{file}\n')

# Use it
save_py_structure()