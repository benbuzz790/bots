#!/usr/bin/env python3
"""Pre-commit hook to repair mojibake in files.

This hook uses the repair_mojibake function from bots.tools.terminal_tools
to automatically fix mojibake (corrupted UTF-8) characters in staged files.
"""

import sys
from pathlib import Path

from bots.tools.terminal_tools import repair_mojibake


def main():
    """Run mojibake repair on all files passed as arguments."""
    if len(sys.argv) < 2:
        print("No files to check")
        return 0

    files_to_check = sys.argv[1:]
    total_fixed = 0
    files_modified = []

    # Files to exclude from mojibake repair to avoid self-recursion
    excluded_filenames = {
        "repair_mojibake_hook.py",
        "terminal_tools.py",
    }

    for filepath in files_to_check:
        # Only check text files (skip binary files, images, etc.)
        path = Path(filepath)
        if not path.exists():
            continue

        # Skip the mojibake repair tool files themselves to avoid recursion
        if path.name in excluded_filenames:
            continue

        # Skip certain file types that shouldn't be modified
        skip_extensions = {
            ".pyc",
            ".pyo",
            ".so",
            ".dll",
            ".exe",
            ".bin",
            ".jpg",
            ".png",
            ".gif",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
        }
        if path.suffix.lower() in skip_extensions:
            continue

        try:
            # Run repair_mojibake without backup (pre-commit will handle that)
            result = repair_mojibake(filepath, backup="false")

            # Check if any changes were made
            if "Repaired" in result and "0 mojibake" not in result:
                files_modified.append(filepath)
                # Extract count from result message
                if "Repaired" in result:
                    count_str = result.split("Repaired ")[1].split(" mojibake")[0]
                    try:
                        total_fixed += int(count_str)
                    except ValueError:
                        pass
        except Exception as e:
            print(f"Warning: Could not check {filepath}: {e}")
            continue

    if files_modified:
        print(f"\n✨ Mojibake Repair: Fixed {total_fixed} character(s) in {len(files_modified)} file(s)")
        print("Files modified:")
        for f in files_modified:
            print(f"  - {f}")
        print("\nPlease review the changes and re-stage the files.")
        return 1  # Return 1 to indicate files were modified

    return 0


if __name__ == "__main__":
    sys.exit(main())
