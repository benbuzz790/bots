#!/usr/bin/env python3
"""Remove BOMs (Byte Order Marks) from files.

Can be used as a pre-commit hook or standalone script.
"""
import codecs
import os
import sys


def remove_bom_from_file(file_path):
    """Remove BOM from a single file if present.

    Returns:
        bool: True if BOM was removed, False otherwise
    """
    try:
        with open(file_path, "rb") as file:
            content = file.read()

        # Check for various BOM types
        bom_found = None
        if content.startswith(codecs.BOM_UTF8):
            bom_found = codecs.BOM_UTF8
        elif content.startswith(codecs.BOM_UTF16_LE):
            bom_found = codecs.BOM_UTF16_LE
        elif content.startswith(codecs.BOM_UTF16_BE):
            bom_found = codecs.BOM_UTF16_BE
        elif content.startswith(codecs.BOM_UTF32_LE):
            bom_found = codecs.BOM_UTF32_LE
        elif content.startswith(codecs.BOM_UTF32_BE):
            bom_found = codecs.BOM_UTF32_BE

        if bom_found:
            with open(file_path, "wb") as file:
                file.write(content[len(bom_found) :])
            return True
        return False
    except Exception as e:
        print(f"Warning: Could not process {file_path}: {e}", file=sys.stderr)
        return False


def remove_bom_from_files(file_paths=None):
    """Remove BOMs from files.

    Args:
        file_paths: List of file paths to process. If None, walks current directory.
    """
    nboms = 0
    files_processed = 0

    def is_hidden(path):
        # Check if directory or file is hidden
        return os.path.basename(path).startswith(".")

    if file_paths:
        # Process specific files (pre-commit hook mode)
        for file_path in file_paths:
            if remove_bom_from_file(file_path):
                nboms += 1
                print(f"Removed BOM from: {file_path}")
            files_processed += 1
    else:
        # Walk directory (standalone mode)
        for root, dirs, files in os.walk(os.getcwd()):
            # Remove hidden directories from dirs list (modifies dirs in place)
            dirs[:] = [d for d in dirs if not is_hidden(d)]
            for file in files:
                # Skip hidden files
                if is_hidden(file):
                    continue
                file_path = os.path.join(root, file)
                if remove_bom_from_file(file_path):
                    nboms += 1
                files_processed += 1

    print(f"\nBOM Removal Summary: {files_processed} files processed, {nboms} BOMs removed")


if __name__ == "__main__":
    # Accept file paths from command line (for pre-commit hook)
    if len(sys.argv) > 1:
        remove_bom_from_files(sys.argv[1:])
    else:
        remove_bom_from_files()
