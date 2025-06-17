"""Project initialization and cleanup utility with project tree analysis.
This module serves two main purposes:
1. Directory Cleanup: Provides utilities for cleaning up project directories by
   removing files with specific extensions while preserving critical scripts.
   Includes safety features like dry-run and confirmation prompts.
2. Project Analysis: Initializes project tree analysis using a specification
   file, which defines the structure and requirements for project analysis.
Typical usage:
    # Basic cleanup with default extensions
    $ python start.py
    # Cleanup and analyze project with spec file
    $ python start.py analysis_spec.md
The module preserves certain critical files by default:
- The script itself
Note: When no spec file is provided, only cleanup operations will be performed.
"""

# Standard library imports
import os
import sys
from typing import List, Tuple

# Local imports
from bots.dev import project_tree


def cleanup_directory(
    script_path: str,
    extensions: Tuple[str, ...] = (".md", ".txt", ".bot", ".py"),
    dry_run: bool = True,
) -> List[str]:
    """Clean up a directory by removing files with specific extensions while
    preserving critical files.
    Use when you need to clean a project directory of generated files or
    temporary outputs while ensuring critical scripts are preserved. The
    function provides a safe way to delete files through its dry-run capability
    and preservation rules.
    Parameters:
    - script_path (str): Absolute or relative path to the script. Used to
                        determine the directory to clean and which script to
                        preserve
    - extensions (Tuple[str, ...]): Tuple of file extensions to delete
                                   (including the dot).
                                   Default: (".md", ".txt", ".bot", ".py")
    - dry_run (bool): If True, only simulates deletion and prints affected
                     files. If False, performs actual deletion. Default: True
    Returns:
    List[str]: Names of files that were deleted (or would be deleted in
              dry-run mode). Empty list if no files match criteria or if
              errors occur during deletion.
    Error Handling:
    - Silently skips directories and preserved files
    - Catches and logs file deletion errors without stopping execution
    - Preserved files include the script itself and "process_bots.py"
    Example:
        >>> # Simulate deletion of text and bot files
        >>> deleted = cleanup_directory("path/to/script.py",
        ...                           extensions=(".txt", ".bot"),
        ...                           dry_run=True)
        >>> print(f"Would delete: {deleted}")
        >>> # Perform actual deletion
        >>> deleted = cleanup_directory("path/to/script.py", dry_run=False)
    """
    directory = os.path.dirname(os.path.abspath(script_path))
    script_name = os.path.basename(script_path)
    preserve = [script_name]
    deleted_files = []
    print(f"Cleaning directory: {directory}")
    print(f"Looking for files with extensions: {', '.join(extensions)}")
    print(f"Preserving scripts: {', '.join(preserve)}")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isdir(file_path) or filename in preserve:
            continue
        if not filename.lower().endswith(extensions):
            continue
        if dry_run:
            print(f"Would delete: {filename}")
        else:
            try:
                os.remove(file_path)
                deleted_files.append(filename)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
    return deleted_files


def main():
    """Execute the cleanup and analysis operations.
    This script performs two operations:
    1. Cleanup: Removes specified file types after a dry run and user
       confirmation
    2. Analysis: If a spec file is provided as an argument, runs project tree
       analysis
    Command-line usage:
        python start.py [spec_file.md]
    """
    # Perform cleanup operation
    print("DRY RUN - No files will be deleted:")
    exts = (".txt", ".bot", ".py")
    cleanup_directory(__file__, extensions=exts, dry_run=True)
    response = input("\nDo you want to proceed with deletion? (yes/no): ")
    if response.lower() == "yes":
        print("\nDeleting files:")
        deleted = cleanup_directory(__file__, extensions=exts, dry_run=False)
        print(f"\nSuccessfully deleted {len(deleted)} files")
        print("Operation cancelled")
    # Perform analysis if spec file provided
    if len(sys.argv) > 1:
        spec_file = sys.argv[1]
        project_tree.main(spec_file)
    else:
        print("\nNo spec file provided. Usage: python start.py <spec_file.md>")


if __name__ == "__main__":
    main()
