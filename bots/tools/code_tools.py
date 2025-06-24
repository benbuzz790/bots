import difflib
import os
import textwrap

from bots.dev.decorators import handle_errors
from bots.utils.unicode_utils import clean_unicode_string


def _read_file_bom_safe(file_path: str) -> str:
    """Read a file with BOM protection."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return clean_unicode_string(content)


def _write_file_bom_safe(file_path: str, content: str) -> None:
    """Write a file with BOM protection."""
    # Ensure content is BOM-free
    clean_content = clean_unicode_string(content)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(clean_content)


@handle_errors
def view(
    file_path: str, start_line: str = None, end_line: str = None, around_str_match: str = None, dist_from_match: str = "10"
):
    """
    Display the contents of a file with line numbers.
    Parameters:
    - file_path (str): The path to the file to be viewed.
    - start_line (int, optional): Starting line number (1-indexed). If None, starts from beginning.
    - end_line (int, optional): Ending line number (1-indexed). If None, goes to end of file.
    - around_str_match (str, optional): String to search for. If provided, shows lines around matches.
    - dist_from_match (int, optional): Number of lines to show before and after each match. Defaults to 10.
    Returns:
    A string containing the file contents with line numbers,
    filtered according to the specified parameters.
    """
    encodings = ["utf-8", "utf-16", "utf-16le", "ascii", "cp1252", "iso-8859-1"]
    start_line = int(start_line) if start_line is not None else None
    end_line = int(end_line) if end_line is not None else None
    dist_from_match = int(dist_from_match) if dist_from_match is not None else None
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                lines = file.readlines()
            # If searching for a string match
            if around_str_match:
                matching_line_numbers = []
                for i, line in enumerate(lines):
                    if around_str_match in line:
                        matching_line_numbers.append(i)
                if not matching_line_numbers:
                    return f"No matches found for '{around_str_match}'"
                # Collect line ranges around matches
                line_ranges = set()
                for match_line in matching_line_numbers:
                    start = max(0, match_line - dist_from_match)
                    end = min(len(lines), match_line + dist_from_match + 1)
                    for line_num in range(start, end):
                        line_ranges.add(line_num)
                # Sort and create output
                sorted_lines = sorted(line_ranges)
                numbered_lines = []
                prev_line = None  # To detect gaps
                for line_num in sorted_lines:
                    if prev_line is not None and line_num > prev_line + 1:
                        numbered_lines.append("...")  # Add separator for gaps
                    numbered_lines.append(f"{line_num + 1}:{lines[line_num].rstrip()}")
                    prev_line = line_num
                return "\n".join(numbered_lines)
            # If using start_line and end_line parameters
            else:
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                # Validate line numbers
                start_idx = max(0, start_idx)
                end_idx = min(len(lines), end_idx)
                if start_idx >= len(lines):
                    return f"Error: start_line ({start_line}) exceeds file length ({len(lines)} lines)"
                selected_lines = lines[start_idx:end_idx]
                numbered_lines = [f"{i + start_idx + 1}:{line.rstrip()}" for i, line in enumerate(selected_lines)]
                return "\n".join(numbered_lines)
        except UnicodeDecodeError:
            continue
    return f"Error: Unable to read file with any of the attempted encodings: {', '.join(encodings)}"


@handle_errors
def view_dir(start_path: str = ".", output_file=None, target_extensions: str = "['py', 'txt', 'md']", max_lines: int = 500):
    """
    Creates a summary of the directory structure starting from the given path, writing only files
    with specified extensions and showing venv directories without their contents.
    Parameters:
    - start_path (str): The root directory to start scanning from.
    - output_file (str): The name of the file to optionally write the directory structure to.
    - target_extensions (str): String representation of a list of file extensions (e.g. "['py', 'txt']").
    - max_lines (int): Maximum number of lines in output. If exceeded, deepest levels are truncated. Default 500.
    Returns:
    str: A formatted string containing the directory structure, with each directory and file properly indented.
    Example output:
    my_project/
        venv/
        module1/
            script.py
            README.md
        module2/
            utils.py
    cost: low
    """
    if max_lines:
        max_lines = int(max_lines)
    extensions_list = [ext.strip().strip("'\"") for ext in target_extensions.strip("[]").split(",")]
    extensions_list = ["." + ext if not ext.startswith(".") else ext for ext in extensions_list]
    # First pass: collect all directory entries with their levels
    dir_entries = []
    max_level = 0
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, "").count(os.sep)
        indent = "    " * level
        basename = os.path.basename(root)
        is_venv = basename in ["venv", "env", ".env"] or "pyvenv.cfg" in files
        if is_venv:
            dir_entries.append((level, f"{indent}{basename}/"))
            max_level = max(max_level, level)
            dirs[:] = []
            continue
        has_relevant_files = False
        for _, _, fs in os.walk(root):
            if any((f.endswith(tuple(extensions_list)) for f in fs)):
                has_relevant_files = True
                break
        if has_relevant_files:
            dir_entries.append((level, f"{indent}{basename}/"))
            max_level = max(max_level, level)
            subindent = "    " * (level + 1)
            for file in files:
                if file.endswith(tuple(extensions_list)):
                    dir_entries.append((level + 1, f"{subindent}{file}"))
                    max_level = max(max_level, level + 1)
    # Second pass: apply length limiting by progressively removing deeper levels
    current_level_limit = max_level
    while current_level_limit >= 0:
        # Filter entries up to current level limit
        filtered_entries = [(level, line) for level, line in dir_entries if level <= current_level_limit]
        # Check if we need to add truncation indicators
        truncated_dirs = set()
        for level, line in dir_entries:
            if level > current_level_limit and level == current_level_limit + 1:
                # Find parent directory
                parent_level = level - 1
                for parent_level_check, parent_line in filtered_entries:
                    if parent_level_check == parent_level and parent_line.endswith("/"):
                        truncated_dirs.add(parent_line)
        # Add truncation indicators
        final_entries = []
        for level, line in filtered_entries:
            final_entries.append(line)
            if line in truncated_dirs:
                truncation_indent = "    " * (level + 1)
                final_entries.append(f"{truncation_indent}...")
        if len(final_entries) <= max_lines:
            output_text = final_entries
            break
        current_level_limit -= 1
    else:
        output_text = [
            f"Project too large (>{max_lines} lines). Showing root level only:",
            f"{os.path.basename(start_path) or start_path}/",
            "    ...",
        ]
    if output_file is not None:
        with open(output_file, "w") as file:
            file.write("\n".join(output_text))
    return "\n".join(output_text)


@handle_errors
def patch_edit(file_path: str, patch_content: str):
    """
    Apply a git-style unified diff patch to a file.
    Use when you need to make a precise change to a file
    Tips:
    - Small, focused changes work best
    - Exact content matching is important
    - Including surrounding context helps matching
    - Whitespace in the target lines matters
    Parameters:
    - file_path (str): Path to the file to modify
    - patch_content (str): Unified diff format patch content
    Returns:
    str: Description of changes made or error message
    cost: low
    """
    file_path = _normalize_path(file_path)
    encodings = ["utf-8", "utf-16", "utf-16le", "ascii", "cp1252", "iso-8859-1"]
    content = None
    used_encoding = "utf-8"

    # Create directory if needed
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # Read existing file or start with empty content
    if not os.path.exists(file_path):
        content = ""
    else:
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    content = file.read()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue

    if content is None and os.path.exists(file_path):
        return f"Error: Unable to read existing file with any of the attempted encodings: {', '.join(encodings)}"

    if not patch_content.strip():
        return "Error: patch_content is empty."

    original_lines = content.splitlines() if content else []
    current_lines = original_lines.copy()
    changes_made = []
    line_offset = 0

    # Clean up patch content
    patch_content = textwrap.dedent(patch_content)
    patch_content = "\n" + patch_content
    hunks = patch_content.split("\n@@")[1:]

    if not hunks:
        return 'Error: No valid patch hunks found. (No instances of "\\n@@". Did you accidentally indent the headers?)'

    for hunk in hunks:
        hunk = hunk.strip()
        if not hunk:
            continue

        try:
            header_end = hunk.index("\n")
            header = hunk[:header_end].strip()
            if not header.endswith("@@"):
                header = header + " @@"

            old_range, new_range = header.rstrip(" @").split(" +")
            old_start = int(old_range.split(",")[0].lstrip("- ")) - 1  # Convert to 0-based

            hunk_lines = _normalize_header_lines(hunk[header_end:].splitlines()[1:])
        except (ValueError, IndexError) as e:
            return f"Error parsing hunk header: {str(e)}\nHeader: {header}"

        # Parse hunk into components
        context_before = []
        context_after = []
        removals = []
        additions = []

        for line in hunk_lines:
            if not line:
                continue
            if not (line.startswith("+") or line.startswith("-")):
                if not removals and not additions:
                    context_before.append(line[1:] if line.startswith(" ") else line)  # Remove space character if present
                else:
                    context_after.append(line[1:] if line.startswith(" ") else line)  # Remove space character if present
            elif line.startswith("-"):
                removals.append(line[1:])
            elif line.startswith("+"):
                additions.append(line[1:])

        if not removals and not additions:
            hunk_start = hunk_lines[0][:20] if hunk_lines else "empty hunk"
            return f"Error: No additions or removals found in hunk starting with {hunk_start}"

        # Handle new file creation - must come before hierarchy check
        # Debug: Let's be very explicit about the conditions
        file_is_empty = len(current_lines) == 0
        patch_starts_at_zero = old_start == 0
        no_context = len(context_before) == 0
        no_removals = len(removals) == 0

        if file_is_empty and patch_starts_at_zero and no_context and no_removals:
            current_lines.extend(additions)
            changes_made.append("Applied changes to new file")
            continue

        # Apply new matching hierarchy
        match_result = _find_match_with_hierarchy(current_lines, old_start + line_offset, context_before, removals, additions)

        if not match_result["found"]:
            return match_result["error"]

        # Apply the changes
        match_line = match_result["line"]
        indented_additions = match_result["additions"]
        pos = match_line + len(context_before)

        if removals:
            current_lines[pos : pos + len(removals)] = indented_additions
        else:
            current_lines[pos:pos] = indented_additions

        line_offset += len(additions) - len(removals)
        changes_made.append(match_result["message"])

    if changes_made:
        new_content = "\n".join(current_lines)
        if not new_content.endswith("\n"):
            new_content += "\n"

        with open(file_path, "w", encoding=used_encoding) as file:
            file.write(new_content)

        return "Successfully applied patches:\n" + "\n".join(changes_made)

    return "No changes were applied"


def _find_match_with_hierarchy(current_lines, expected_line, context_before, removals, additions):
    """
    Implement the new 5-step matching hierarchy.
    Returns dict with keys: found, line, additions, message, error
    """

    # Special case: if no context and no removals, this might be a pure insertion
    # that should go at the expected line (common for new file scenarios that slip through)
    if not context_before and not removals:
        if expected_line <= len(current_lines):
            return {
                "found": True,
                "line": expected_line,
                "additions": additions,
                "message": f"Applied pure insertion at line {expected_line + 1}",
                "error": None,
            }

    # Step 1: Check exact match at line numbers (line numbers + context + indentation)
    if _check_exact_match_at_position(current_lines, expected_line, context_before, removals):
        return {
            "found": True,
            "line": expected_line,
            "additions": additions,
            "message": f"Applied hunk with exact match at line {expected_line + 1}",
            "error": None,
        }

    # Step 2: Check exact match ignoring line numbers (context + indentation match anywhere)
    exact_match_line = _find_exact_match_anywhere(current_lines, context_before, removals)
    if exact_match_line is not None:
        return {
            "found": True,
            "line": exact_match_line,
            "additions": additions,
            "message": (
                f"Applied hunk with exact match at line {exact_match_line + 1} "
                f"(different from specified line {expected_line + 1})"
            ),
            "error": None,
        }

    # Step 3: Check match at line numbers ignoring whitespace
    if _check_whitespace_match_at_position(current_lines, expected_line, context_before, removals):
        if not context_before:
            return {
                "found": False,
                "line": None,
                "additions": None,
                "message": None,
                "error": "Error: Need context lines to determine correct indentation when whitespace differs",
            }

        adjusted_additions = _adjust_additions_to_context(current_lines, expected_line, context_before, additions)
        return {
            "found": True,
            "line": expected_line,
            "additions": adjusted_additions,
            "message": f"Applied hunk at line {expected_line + 1} with indentation adjustment",
            "error": None,
        }

    # Step 4: Check match anywhere ignoring whitespace
    whitespace_match_line = _find_whitespace_match_anywhere(current_lines, context_before, removals)
    if whitespace_match_line is not None:
        if not context_before:
            return {
                "found": False,
                "line": None,
                "additions": None,
                "message": None,
                "error": "Error: Need context lines to determine correct indentation when whitespace differs",
            }

        adjusted_additions = _adjust_additions_to_context(current_lines, whitespace_match_line, context_before, additions)
        return {
            "found": True,
            "line": whitespace_match_line,
            "additions": adjusted_additions,
            "message": (
                f"Applied hunk at line {whitespace_match_line + 1} "
                f"(different from specified line {expected_line + 1}) "
                f"with indentation adjustment"
            ),
            "error": None,
        }

    # Step 5: Fuzzy matching - find best partial match
    if context_before:
        _, best_line, match_quality, _ = _find_block_in_content(current_lines, context_before, ignore_whitespace=True)
        if match_quality > 0.05:
            context = _get_context(current_lines, best_line - 1, 2)
            return {
                "found": False,
                "line": None,
                "additions": None,
                "message": None,
                "error": (
                    f"Error: Could not find match. Best potential match at lines "
                    f"{best_line} to {best_line + len(context_before) - 1}\nContext:\n"
                    + "\n".join(context)
                    + f"\nMatch quality: {match_quality:.2f}"
                ),
            }

    return {
        "found": False,
        "line": None,
        "additions": None,
        "message": None,
        "error": "Error: Could not find any suitable match for the patch context",
    }


def _check_exact_match_at_position(current_lines, line_pos, context_before, removals):
    """Check if there's an exact match at the specified position."""
    if line_pos < 0 or line_pos + len(context_before) > len(current_lines):
        return False

    # Check context lines
    for i, ctx_line in enumerate(context_before):
        if current_lines[line_pos + i] != ctx_line:
            return False

    # Check removal lines if present
    if removals:
        removal_pos = line_pos + len(context_before)
        if removal_pos + len(removals) > len(current_lines):
            return False
        for i, rem_line in enumerate(removals):
            if current_lines[removal_pos + i] != rem_line:
                return False

    return True


def _find_exact_match_anywhere(current_lines, context_before, removals):
    """Find exact match anywhere in the file, ignoring line numbers."""
    if not context_before and not removals:
        return None

    search_lines = context_before + removals

    for i in range(len(current_lines) - len(search_lines) + 1):
        match = True
        for j, search_line in enumerate(search_lines):
            if current_lines[i + j] != search_line:
                match = False
                break
        if match:
            return i

    return None


def _check_whitespace_match_at_position(current_lines, line_pos, context_before, removals):
    """Check if there's a whitespace-ignoring match at the specified position."""
    if line_pos < 0 or line_pos + len(context_before) > len(current_lines):
        return False

    # Check context lines ignoring whitespace
    for i, ctx_line in enumerate(context_before):
        if current_lines[line_pos + i].strip() != ctx_line.strip():
            return False

    # Check removal lines if present
    if removals:
        removal_pos = line_pos + len(context_before)
        if removal_pos + len(removals) > len(current_lines):
            return False
        for i, rem_line in enumerate(removals):
            if current_lines[removal_pos + i].strip() != rem_line.strip():
                return False

    return True


def _find_whitespace_match_anywhere(current_lines, context_before, removals):
    """Find whitespace-ignoring match anywhere in the file."""
    if not context_before and not removals:
        return None

    search_lines = context_before + removals

    for i in range(len(current_lines) - len(search_lines) + 1):
        match = True
        for j, search_line in enumerate(search_lines):
            if current_lines[i + j].strip() != search_line.strip():
                match = False
                break
        if match:
            return i

    return None


def _adjust_additions_to_context(current_lines, match_line, context_before, additions):
    """
    Adjust additions indentation based on context line indentation difference.

    The logic:
    1. Find first non-empty context line in patch
    2. Compare its indentation to corresponding line in actual file
    3. Apply that indentation difference to all addition lines
    """
    if not context_before:
        return None  # Error should be handled by caller

    if not additions:
        return additions

    # Find first non-empty context line
    patch_context_line = None
    context_index = None
    for i, ctx_line in enumerate(context_before):
        if ctx_line.strip():  # Skip empty lines
            patch_context_line = ctx_line
            context_index = i
            break

    if patch_context_line is None:
        # All context lines are empty, can't determine baseline
        return additions

    # Get indentation of context line in patch vs actual file
    patch_indent_len = len(_get_line_indentation(patch_context_line))
    actual_file_line = current_lines[match_line + context_index]
    actual_indent_len = len(_get_line_indentation(actual_file_line))

    # Calculate the indentation difference
    indent_diff_spaces = actual_indent_len - patch_indent_len

    # Apply the difference to all addition lines
    adjusted_additions = []
    for addition in additions:
        if not addition.strip():  # Empty line
            adjusted_additions.append(addition)
            continue

        current_addition_indent_len = len(_get_line_indentation(addition))
        new_indent_spaces = current_addition_indent_len + indent_diff_spaces

        # Ensure we don't go negative
        if new_indent_spaces < 0:
            new_indent_spaces = 0

        new_indent = " " * new_indent_spaces
        line_content = addition.lstrip()
        adjusted_line = new_indent + line_content
        adjusted_additions.append(adjusted_line)

    return adjusted_additions


def _get_context(lines, center_idx, context_size):
    """Get context lines around an index with line numbers."""
    start = max(0, center_idx - context_size)
    end = min(len(lines), center_idx + context_size + 1)
    return [f"{i + 1}:{line}" for i, line in enumerate(lines[start:end], start)]


def _find_block_in_content(
    content_lines: list, block_lines: list, ignore_whitespace: bool = False
) -> tuple[bool, int, float, bool]:
    """Helper function to find a block of lines anywhere in the content.
    Returns (found, line_number, match_quality, was_whitespace_match)"""
    if not block_lines:
        return (False, 0, 0.0, False)
    for i in range(len(content_lines) - len(block_lines) + 1):
        current_block = content_lines[i : i + len(block_lines)]
        if current_block == block_lines:
            return (True, i + 1, 1.0, False)
    if ignore_whitespace:
        for i in range(len(content_lines) - len(block_lines) + 1):
            current_block = [lines.strip() for lines in content_lines[i : i + len(block_lines)]]
            if current_block == block_lines:
                return (True, i + 1, 0.9, True)
    best_match = 0.0
    best_line = 0
    for i in range(len(content_lines) - len(block_lines) + 1):
        current_block = content_lines[i : i + len(block_lines)]
        matcher = difflib.SequenceMatcher(None, "\n".join(current_block), "\n".join(block_lines))
        ratio = matcher.ratio()
        if ratio > best_match:
            best_match = ratio
            best_line = i + 1
    return (False, best_line, best_match, False)


def _get_line_indentation(line: str) -> str:
    """Extract the indentation from a line."""
    return line[: len(line) - len(line.lstrip())]


def _normalize_path(file_path: str) -> str:
    """
    Normalize file path to use consistent separators and handle both / and \\.
    Args:
        file_path (str): The file path to normalize
    Returns:
        str: Normalized path using os.path.sep
    """
    return os.path.normpath(file_path.replace("\\", "/").replace("//", "/"))


def _normalize_header_lines(lines):
    """
    Normalize only the hunk headers (@@ lines) in a patch.
    Leaves all other lines unchanged.
    Args:
        lines (list[str]): List of patch lines
    Returns:
        list[str]: Lines with normalized hunk headers
    """
    normalized = []
    for line in lines:
        if not line:
            normalized.append(line)
            continue
        if line.startswith("@@"):
            parts = line.split("@@")
            if len(parts) >= 2:
                ranges = parts[1].strip()
                line = f"@@ {ranges} @@"
        normalized.append(line)
    return normalized
