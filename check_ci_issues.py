import os
import sys
from examples.style_fixer import check_file_cicd
#!/usr/bin/env python3
"""Quick script to check CI/CD issues using the style_fixer function."""
sys.path.append('.')

def main():
    project_root = os.getcwd()
    # Check a few key files that might be causing issues
    test_files = ["bots/__init__.py", "bots/foundation/base.py", "setup.py"]
    for file_path in test_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"\n{'='*60}")
            print(f"Checking: {file_path}")
            print('=' * 60)
            result = check_file_cicd(full_path, project_root)
            print(result)
        else:
            print(f"File not found: {file_path}")
if __name__ == "__main__":
    main()