"""
Utility script for cleaning up project directories and analyzing project structure.

This script provides functionality to:
- Clean up generated files (*.md, *.txt, *.bot, *.py) from a directory
- Preserve critical files like README.md, LICENSE, setup.py, etc.
- Optionally analyze project structure using a specification file

Usage:
    python start.py [spec_file.md]

The script will:
1. Show files that would be deleted (dry run)
2. Ask for confirmation
3. Delete files if confirmed
4. Analyze project structure if spec file provided

Files preserved:
- README.md, LICENSE, setup.py, __init__.py
- The script itself

Note: When no spec file is provided, only cleanup operations will be performed.
"""

# Standard library imports
import os
import sys
from typing import List, Tuple

# Note: project_tree module has been removed/refactored
# from bots.dev import project_tree


def cleanup_directory(
    script_path: str,
    extensions: Tuple[str, ...] = (".md", ".txt", ".bot", ".py"),
    dry_run: bool = True,
) -> List[str]:
    """Clean up a directory by removing files with specific extensions while
    preserving critical files.

    Use when you need to clean a project directory of generated files or
    temporary artifacts while keeping essential project files intact.

    Parameters:
        script_path (str): Path to the script file (used to determine directory)
        extensions (Tuple[str, ...]): File extensions to target for deletion
        dry_run (bool): If True, only show what would be deleted without
            actually deleting

    Returns:
        List[str]: List of file paths that were (or would be) deleted

    Example:
        >>> # Preview what would be deleted
        >>> files = cleanup_directory(__file__, dry_run=True)
        >>> print(f"Would delete {len(files)} files")
        >>>
        >>> # Actually delete the files
        >>> deleted = cleanup_directory(__file__, dry_run=False)
    """
    script_dir = os.path.dirname(os.path.abspath(script_path))
    script_name = os.path.basename(script_path)

    # Files to preserve
    preserve_files = {
        "README.md",
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "setup.py",
        "__init__.py",
        script_name,
    }

    deleted_files = []

    for root, dirs, files in os.walk(script_dir):
        for file in files:
            if file.endswith(extensions) and file not in preserve_files:
                file_path = os.path.join(root, file)
                if dry_run:
                    print(f"Would delete: {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                        continue
                deleted_files.append(file_path)

    return deleted_files


def main():
    """Main entry point for the cleanup script."""
    print("Project Cleanup Utility")
    print("=" * 50)

    # Define extensions to clean
    exts = (".md", ".txt", ".bot")

    # Dry run first
    print("\nFiles that would be deleted:")
    cleanup_directory(__file__, extensions=exts, dry_run=True)

    response = input("\nDo you want to proceed with deletion? (yes/no): ")
    if response.lower() == "yes":
        print("\nDeleting files:")
        deleted = cleanup_directory(__file__, extensions=exts, dry_run=False)
        print(f"\nSuccessfully deleted {len(deleted)} files")
    else:
        print("Operation cancelled")

    # Note: Project tree analysis has been removed/refactored
    # If you need project analysis, use the appropriate tool from bots.dev.cli
    if len(sys.argv) > 1:
        print("\nNote: Project tree analysis is no longer available in this script.")
        print("Please use the CLI tools for project analysis.")
    else:
        print("\nCleanup complete.")


if __name__ == "__main__":
    main()
