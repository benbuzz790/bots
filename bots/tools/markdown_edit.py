import os
import re
from typing import List, Optional, Tuple

from bots.dev.decorators import toolify
from bots.utils.helpers import _process_error


def _remove_bom(content: str) -> str:
    """Remove UTF-8 BOM if present, otherwise return string unchanged."""
    if content.startswith("\ufeff"):
        return content[1:]
    return content


def _read_file_bom_safe(file_path: str) -> str:
    """Read a file with BOM protection."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return _remove_bom(content)


def _write_file_bom_safe(file_path: str, content: str) -> None:
    """Write a file with BOM protection."""
    # Remove BOM if present
    clean_content = _remove_bom(content)
    # Check if original content ended with newline
    ends_with_newline = content.endswith("\n")
    # Restore newline if it was there originally
    if ends_with_newline and not clean_content.endswith("\n"):
        clean_content += "\n"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(clean_content)


def _join_lines_preserve_trailing_newline(lines: List[str], original_content: str) -> str:
    """
    Join lines with newlines, preserving the original file's trailing newline.

    Parameters:
    -----------
    lines : List[str]
        Lines to join
    original_content : str
        Original file content to check for trailing newline

    Returns:
    --------
    str
        Joined content with trailing newline preserved if original had one
    """
    joined = "\n".join(lines)
    if original_content.endswith("\n") and not joined.endswith("\n"):
        joined += "\n"
    return joined


def _re_resolve_heading(lines: List[str], path_elements: List[str]) -> Optional["HeadingNode"]:
    """
    Re-resolve a heading after lines have been modified.

    Parameters:
    -----------
    lines : List[str]
        Modified lines to parse
    path_elements : List[str]
        Path elements to find the heading

    Returns:
    --------
    Optional[HeadingNode]
        The re-resolved heading node, or None if not found
    """
    content = "\n".join(lines)
    headings = _parse_markdown_structure(content)
    target_heading, _ = _find_heading_by_path(headings, path_elements)
    return target_heading


def _make_file(file_path: str) -> str:
    """
    Create a file and its parent directories if they don't exist.

    Parameters:
    -----------
    file_path : str
        Path to the file to create

    Returns:
    --------
    str
        Absolute path to the created/existing file

    Raises:
    -------
    ValueError
        If there's an error creating the file or directories
    """
    if not file_path:
        raise ValueError("File path cannot be empty")
    abs_path = os.path.abspath(file_path)
    dir_path = os.path.dirname(abs_path)
    if dir_path:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Error creating directories {dir_path}: {str(e)}")
    if not os.path.exists(abs_path):
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            raise ValueError(f"Error creating file {abs_path}: {str(e)}")
    return abs_path


def _count_lines_to_be_deleted(original_content: str, new_content: str) -> int:
    """
    Count how many lines would be deleted by comparing original vs new content.

    Parameters:
    -----------
    original_content : str
        The original file content
    new_content : str
        The new content that would replace it

    Returns:
    --------
    int
        Number of lines that would be deleted
    """
    original_lines = len(original_content.splitlines()) if original_content.strip() else 0
    new_lines = len(new_content.splitlines()) if new_content.strip() else 0
    return max(0, original_lines - new_lines)


class HeadingNode:
    """Represents a heading in a markdown document."""

    def __init__(self, level: int, title: str, start_line: int, end_line: int = -1):
        self.level = level
        self.title = title
        self.start_line = start_line
        self.end_line = end_line
        self.children: List[HeadingNode] = []
        self.content_start = start_line + 1  # Content starts after heading line

    def __repr__(self):
        return f"HeadingNode(level={self.level}, title='{self.title}', lines={self.start_line}-{self.end_line})"


def _parse_markdown_structure(content: str) -> List[HeadingNode]:
    """
    Parse markdown content and extract heading structure.

    Returns a flat list of HeadingNode objects with proper start/end lines.
    """
    lines = content.splitlines()
    headings = []
    in_fence = False
    fence_marker = ""

    for i, line in enumerate(lines):
        # Check for fenced code block markers
        fence_match = re.match(r"^(`{3,}|~{3,})", line)
        if fence_match:
            if not in_fence:
                # Starting a fence
                in_fence = True
                fence_marker = fence_match.group(1)[0]  # '`' or '~'
            elif line.startswith(fence_marker * 3):
                # Ending a fence (must match the opening marker type)
                in_fence = False
                fence_marker = ""
            continue

        # Skip heading detection if we're inside a fence
        if in_fence:
            continue

        # Match ATX-style headings (# Heading)
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            # Remove trailing hashes (ATX-style closing)
            title = re.sub(r"\s*#+\s*$", "", title)
            headings.append(HeadingNode(level, title, i))

    # Set end_line for each heading (up to the next same-or-higher level heading)
    for i, heading in enumerate(headings):
        # Find the next heading at the same or higher level
        next_line = len(lines)
        for j in range(i + 1, len(headings)):
            if headings[j].level <= heading.level:
                next_line = headings[j].start_line
                break
        heading.end_line = next_line - 1

    # If there are headings, set the last one's end_line to the last line
    if headings:
        headings[-1].end_line = len(lines) - 1

    return headings


def _find_heading_by_path(headings: List[HeadingNode], path_elements: List[str]) -> Tuple[Optional[HeadingNode], List[str]]:
    """
    Find a heading node by following a path of heading titles.

    Parameters:
    -----------
    headings : List[HeadingNode]
        Flat list of all headings
    path_elements : List[str]
        Path elements like ["Section", "Subsection"]

    Returns:
    --------
    Tuple[Optional[HeadingNode], List[str]]
        A tuple of (matching heading node or None, list of ambiguous match paths)
        If multiple matches found, returns (None, list of full paths)
        If single match found, returns (node, [])
        If no match found, returns (None, [])
    """
    if not path_elements:
        return None, []

    # Build a separate children map instead of mutating heading objects
    children_map = {heading: [] for heading in headings}

    # Build a hierarchy using the children map
    root_headings = []
    stack = []

    for heading in headings:
        # Pop stack until we find a parent (heading with lower level)
        while stack and stack[-1].level >= heading.level:
            stack.pop()

        # Add as child to parent, or as root
        if stack:
            children_map[stack[-1]].append(heading)
        else:
            root_headings.append(heading)

        stack.append(heading)

    # Helper function to get children without mutating the heading
    def get_children(node: HeadingNode) -> List[HeadingNode]:
        """Get children from the children map."""
        return children_map.get(node, [])

    # Helper function to build full path for a heading
    def get_full_path(target_heading: HeadingNode) -> List[str]:
        """Build the full path from root to this heading."""
        path = []

        def find_path_recursive(nodes: List[HeadingNode], target: HeadingNode, current_path: List[str]) -> bool:
            for node in nodes:
                new_path = current_path + [node.title]
                if node is target:
                    path.extend(new_path)
                    return True
                if find_path_recursive(get_children(node), target, new_path):
                    return True
            return False

        find_path_recursive(root_headings, target_heading, [])
        return path

    # Helper function to follow a path from a starting node
    def follow_path_from_node(start_node: HeadingNode, remaining_path: List[str]) -> Optional[HeadingNode]:
        """Follow a path starting from a given node."""
        current_node = start_node
        for element in remaining_path:
            found = False
            for child in get_children(current_node):
                if child.title == element:
                    current_node = child
                    found = True
                    break
            if not found:
                return None
        return current_node

    # Search all levels for the first element
    first_element = path_elements[0]
    first_matches = []

    def find_all_first_matches(nodes: List[HeadingNode]):
        for node in nodes:
            if node.title == first_element:
                first_matches.append(node)
            find_all_first_matches(get_children(node))

    find_all_first_matches(root_headings)

    if len(first_matches) == 0:
        return None, []

    # If single element path, return the match(es)
    if len(path_elements) == 1:
        if len(first_matches) == 1:
            return first_matches[0], []
        else:
            # Multiple matches - return ambiguous paths
            ambiguous_paths = [get_full_path(match) for match in first_matches]
            return None, ambiguous_paths

    # Multi-element path - try to follow remaining path from each first match
    remaining_path = path_elements[1:]
    successful_matches = []

    for first_match in first_matches:
        result = follow_path_from_node(first_match, remaining_path)
        if result is not None:
            successful_matches.append(result)

    if len(successful_matches) == 0:
        return None, []
    elif len(successful_matches) == 1:
        return successful_matches[0], []
    else:
        # Multiple complete paths found - return ambiguous
        ambiguous_paths = [get_full_path(match) for match in successful_matches]
        return None, ambiguous_paths


def _get_section_content(lines: List[str], heading: HeadingNode) -> str:
    """
    Extract the content of a section (heading + content until next same-level heading).
    """
    if heading.start_line < 0 or heading.end_line < 0:
        return ""

    section_lines = lines[heading.start_line : heading.end_line + 1]
    return "\n".join(section_lines)


def _replace_section(lines: List[str], heading: HeadingNode, new_content: str) -> List[str]:
    """
    Replace a section with new content.

    Parameters:
    -----------
    lines : List[str]
        Original file lines
    heading : HeadingNode
        The heading to replace
    new_content : str
        New content (should include heading if replacing entire section)

    Returns:
    --------
    List[str]
        Modified lines
    """
    new_lines = new_content.splitlines()

    # Find where the section content ends (before any child headings)
    # We want to replace only the heading and its direct content, not child sections
    content_end_line = heading.end_line

    # Check if there are any child headings (headings with level > current heading level)
    # that appear before the next same-or-higher level heading
    for i in range(heading.start_line + 1, heading.end_line + 1):
        if i < len(lines):
            # Check if this line is a heading
            match = re.match(r"^(#{1,6})\s+(.+)$", lines[i])
            if match:
                child_level = len(match.group(1))
                # If we found a child heading (deeper level), stop before it
                if child_level > heading.level:
                    content_end_line = i - 1
                    break

    # Replace the section: keep lines before, add new content, keep child headings and after
    result = lines[: heading.start_line] + new_lines + lines[content_end_line + 1 :]
    return result


def _delete_section(lines: List[str], heading: HeadingNode) -> List[str]:
    """
    Delete a section entirely.
    """
    return lines[: heading.start_line] + lines[heading.end_line + 1 :]


def _insert_after_heading(lines: List[str], heading: HeadingNode, new_content: str) -> List[str]:
    """
    Insert content after a heading (at the end of its section).
    """
    new_lines = new_content.splitlines()

    # Insert at the end of the section
    insert_pos = heading.end_line + 1
    result = lines[:insert_pos] + new_lines + lines[insert_pos:]
    return result


def _insert_at_file_start(lines: List[str], new_content: str) -> List[str]:
    """Insert content at the beginning of the file."""
    new_lines = new_content.splitlines()
    return new_lines + lines


def _insert_at_file_end(lines: List[str], new_content: str) -> List[str]:
    """Insert content at the end of the file."""
    new_lines = new_content.splitlines()
    return lines + new_lines


def _find_pattern_in_section(lines: List[str], heading: HeadingNode, pattern: str) -> Optional[int]:
    """
    Find a line matching a pattern within a section.

    Returns the line index, or None if not found.
    """
    pattern_lines = pattern.splitlines()
    is_multiline = len(pattern_lines) > 1

    section_lines = lines[heading.start_line : heading.end_line + 1]

    if is_multiline:
        # Multi-line pattern matching
        for i in range(len(section_lines) - len(pattern_lines) + 1):
            match = True
            for j, pattern_line in enumerate(pattern_lines):
                if pattern_line.strip() not in section_lines[i + j]:
                    match = False
                    break
            if match:
                return heading.start_line + i + len(pattern_lines) - 1
    else:
        # Single line pattern
        pattern_stripped = pattern_lines[0].strip()
        for i, line in enumerate(section_lines):
            if pattern_stripped in line or line.strip().startswith(pattern_stripped):
                return heading.start_line + i

    return None


def _insert_after_pattern(lines: List[str], line_index: int, new_content: str) -> List[str]:
    """Insert content after a specific line."""
    new_lines = new_content.splitlines()
    insert_pos = line_index + 1
    return lines[:insert_pos] + new_lines + lines[insert_pos:]


def _check_for_duplicate_headings(lines: List[str], new_content: str, target_heading: Optional[HeadingNode]) -> List[str]:
    """
    Check if new content contains headings that already exist in the target section.
    Remove duplicates from the existing content before insertion.

    Returns modified lines with duplicates removed.
    """
    # Parse headings from new content
    new_headings = _parse_markdown_structure(new_content)
    if not new_headings:
        return lines

    new_titles = {h.title for h in new_headings}

    # Parse existing headings
    existing_headings = _parse_markdown_structure("\n".join(lines))

    # Find headings to remove (within target section if specified)
    headings_to_remove = []
    for heading in existing_headings:
        if heading.title in new_titles:
            # If we have a target section, only remove duplicates within that section
            if target_heading:
                if heading.start_line >= target_heading.start_line and heading.end_line <= target_heading.end_line:
                    headings_to_remove.append(heading)
            else:
                headings_to_remove.append(heading)

    # Remove headings in reverse order to maintain line indices
    for heading in reversed(headings_to_remove):
        lines = _delete_section(lines, heading)

    return lines


@toolify()
def markdown_view(target_scope: str, max_lines: str = "500") -> str:
    """
    View markdown content using file::heading::subheading scope syntax.

    Parameters:
    -----------
    target_scope : str
        Location to view in scope syntax:
        - "file.md" (whole file)
        - "file.md::Heading" (section under heading)
        - "file.md::Heading::Subheading" (nested section)
    max_lines : str, optional
        Maximum number of lines in output. Default "500".

    Returns:
    --------
    str
        The content at the specified scope, or error message
    """
    max_lines_int = int(max_lines)

    try:
        parts = target_scope.split("::")
        file_path = parts[0]
        path_elements = parts[1:] if len(parts) > 1 else []

        if not file_path.endswith(".md"):
            return _process_error(ValueError(f"File path must end with .md: {file_path}"))

        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return _process_error(FileNotFoundError(f"File not found: {abs_path}"))

        try:
            content = _read_file_bom_safe(abs_path)
            if not content.strip():
                return f"File '{abs_path}' is empty."
        except Exception as e:
            return _process_error(ValueError(f"Error reading file {abs_path}: {str(e)}"))

        # If no path elements, return whole file
        if not path_elements:
            lines = content.splitlines()
            if max_lines_int > 0 and len(lines) > max_lines_int:
                truncated = lines[:max_lines_int]
                truncated.append(f"\n... ({len(lines) - max_lines_int} more lines) ...")
                return "\n".join(truncated)
            return content

        # Parse structure and find target heading
        headings = _parse_markdown_structure(content)
        target_heading, ambiguous_paths = _find_heading_by_path(headings, path_elements)

        if ambiguous_paths:
            # Multiple matches found
            formatted_paths = [f"{file_path}::{('::'.join(path))}" for path in ambiguous_paths]
            return _process_error(
                ValueError(
                    "Ambiguous heading reference. Multiple matches found:\n"
                    + "\n".join(f"  - {p}" for p in formatted_paths)
                    + "\nPlease be more specific."
                )
            )

        if not target_heading:
            return _process_error(ValueError(f"Target scope not found: {target_scope}"))

        lines = content.splitlines()
        section_content = _get_section_content(lines, target_heading)

        # Apply max_lines if specified
        if max_lines_int > 0:
            section_lines = section_content.splitlines()
            if len(section_lines) > max_lines_int:
                truncated = section_lines[:max_lines_int]
                truncated.append(f"\n... ({len(section_lines) - max_lines_int} more lines) ...")
                return "\n".join(truncated)

        return section_content

    except Exception as e:
        return _process_error(e)


@toolify()
def markdown_edit(target_scope: str, content: str, *, coscope_with: str | None = None, delete_a_lot: bool = False) -> str:
    """
    Edit markdown files using file::heading::subheading scope syntax.

    Parameters:
    -----------
    target_scope : str
        Location to edit in scope syntax:
        - "file.md" (whole file)
        - "file.md::Heading" (section)
        - "file.md::Heading::Subheading" (nested section)

    content : str
        Markdown content. This will replace the entire target scope by default,
        or insert after (if coscope_with is specified).

    coscope_with : str, optional
        If specified, content is inserted after this point:
        - "__FILE_START__" (beginning of file)
        - "__FILE_END__" (end of file)
        - "Heading" or "Heading::Subheading" (after this heading)
        - '"text pattern"' (after line matching this pattern)

    delete_a_lot : bool, optional
        Safety parameter. Must be True to allow operations that delete more than 100 lines.
        Default False.

    Returns:
    --------
    str
        Description of what was modified or error message
    """
    try:
        parts = target_scope.split("::")
        file_path = parts[0]
        path_elements = parts[1:] if len(parts) > 1 else []

        # Handle non-.md files as a courtesy
        if not file_path.endswith(".md"):
            if not os.path.exists(file_path):
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                    except Exception as e:
                        return _process_error(ValueError(f"Error creating directories {dir_path}: {str(e)}"))
                try:
                    _write_file_bom_safe(file_path, content)
                    return (
                        f"WARNING: markdown_edit is for markdown files. As a courtesy, this new file has been written verbatim, "
                        f"but markdown_edit will not be able to edit the file.\n"
                        f"File created: '{file_path}'"
                    )
                except Exception as e:
                    return _process_error(ValueError(f"Error writing file {file_path}: {str(e)}"))
            else:
                return _process_error(ValueError(f"File path must end with .md: {file_path}"))

        # Create file if it doesn't exist
        abs_path = _make_file(file_path)

        try:
            original_content = _read_file_bom_safe(abs_path)
            was_originally_empty = not original_content.strip()
        except Exception as e:
            return _process_error(ValueError(f"Error reading file {abs_path}: {str(e)}"))

        # Handle empty content (deletion)
        if not content.strip():
            if coscope_with:
                return _process_error(ValueError("Cannot use empty content with coscope_with - nothing to insert"))

            # Safety check for large deletions
            lines_to_delete = _count_lines_to_be_deleted(original_content, "")
            if lines_to_delete > 100 and not delete_a_lot:
                return _process_error(
                    ValueError(
                        f"Safety check: this operation would delete {lines_to_delete} lines. "
                        + "If intentional, set delete_a_lot=True."
                    )
                )

            if not path_elements:
                # Delete entire file
                _write_file_bom_safe(abs_path, "")
                return f"File '{abs_path}' cleared (deleted all content)."
            else:
                # Delete specific section
                lines = original_content.splitlines()
                headings = _parse_markdown_structure(original_content)
                target_heading, ambiguous_paths = _find_heading_by_path(headings, path_elements)

                if ambiguous_paths:
                    formatted_paths = [f"{file_path}::{('::'.join(path))}" for path in ambiguous_paths]
                    return _process_error(
                        ValueError(
                            "Ambiguous heading reference. Multiple matches found:\n"
                            + "\n".join(f"  - {p}" for p in formatted_paths)
                            + "\nPlease be more specific."
                        )
                    )

                if not target_heading:
                    return _process_error(ValueError(f"Target scope not found: {target_scope}"))

                modified_lines = _delete_section(lines, target_heading)
                _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
                return f"Deleted scope '{target_scope}' from '{abs_path}'."

        # Handle empty file with content
        if was_originally_empty and not path_elements:
            _write_file_bom_safe(abs_path, content)
            return f"Content added to '{abs_path}'."

        lines = original_content.splitlines() if original_content else []

        # Check for invalid combination of file-level tokens with scoped targets
        if coscope_with in ("__FILE_START__", "__FILE_END__") and path_elements:
            return _process_error(
                ValueError(
                    f"Cannot use {coscope_with} with scoped target '{target_scope}'. "
                    f"File-level tokens (__FILE_START__, __FILE_END__) can only be used "
                    f"with file-level targets (e.g., 'file.md')."
                )
            )

        # Handle __FILE_START__
        if coscope_with == "__FILE_START__":
            # Check for duplicates and remove them
            lines = _check_for_duplicate_headings(lines, content, None)
            modified_lines = _insert_at_file_start(lines, content)
            _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
            return f"Content inserted at start of '{abs_path}'."

        # Handle __FILE_END__
        if coscope_with == "__FILE_END__":
            # Check for duplicates and remove them
            lines = _check_for_duplicate_headings(lines, content, None)
            modified_lines = _insert_at_file_end(lines, content)
            _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
            return f"Content inserted at end of '{abs_path}'."

        # Handle file-level operations (no path_elements)
        if not path_elements:
            if coscope_with:
                # File-level insertion after a pattern or heading
                headings = _parse_markdown_structure(original_content)

                # Check if it's a quoted pattern
                if (coscope_with.startswith('"') and coscope_with.endswith('"')) or (
                    coscope_with.startswith("'") and coscope_with.endswith("'")
                ):
                    pattern = coscope_with[1:-1]
                    # Search for pattern at file level
                    pattern_lines = pattern.splitlines()
                    is_multiline = len(pattern_lines) > 1

                    found_line = None
                    if is_multiline:
                        for i in range(len(lines) - len(pattern_lines) + 1):
                            match = True
                            for j, pattern_line in enumerate(pattern_lines):
                                if pattern_line.strip() not in lines[i + j]:
                                    match = False
                                    break
                            if match:
                                found_line = i + len(pattern_lines) - 1
                                break
                    else:
                        pattern_stripped = pattern_lines[0].strip()
                        for i, line in enumerate(lines):
                            if pattern_stripped in line or line.strip().startswith(pattern_stripped):
                                found_line = i
                                break

                    if found_line is None:
                        return _process_error(ValueError(f"Pattern not found: {coscope_with}"))

                    modified_lines = _insert_after_pattern(lines, found_line, content)
                    _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
                    return f"Content inserted after pattern in '{abs_path}'."
                else:
                    # It's a heading name - search for it with ambiguity detection
                    insert_after_elements = [coscope_with]
                    target_heading, ambiguous_paths = _find_heading_by_path(headings, insert_after_elements)

                    if ambiguous_paths:
                        formatted_paths = [f"{file_path}::{('::'.join(path))}" for path in ambiguous_paths]
                        return _process_error(
                            ValueError(
                                "Ambiguous heading reference. Multiple matches found:\n"
                                + "\n".join(f"  - {p}" for p in formatted_paths)
                                + "\nPlease be more specific."
                            )
                        )

                    if not target_heading:
                        return _process_error(ValueError(f"Heading not found: {coscope_with}"))

                    # Check for duplicates and remove them
                    lines = _check_for_duplicate_headings(lines, content, target_heading)

                    # Re-resolve target_heading after lines have been modified
                    target_heading = _re_resolve_heading(lines, insert_after_elements)
                    if not target_heading:
                        return _process_error(ValueError(f"Heading not found after duplicate removal: {coscope_with}"))

                    modified_lines = _insert_after_heading(lines, target_heading, content)
                    _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
                    return f"Content inserted after '{coscope_with}' in '{abs_path}'."
            else:
                # File-level replacement
                lines_to_delete = _count_lines_to_be_deleted(original_content, content)
                if lines_to_delete > 100 and not delete_a_lot:
                    return _process_error(
                        ValueError(
                            f"Safety check: this operation would delete {lines_to_delete} lines. "
                            + "If intentional, set delete_a_lot=True."
                        )
                    )
                _write_file_bom_safe(abs_path, content)
                return f"Content replaced at file level in '{abs_path}'."

        # Handle scoped operations (with path_elements)
        headings = _parse_markdown_structure(original_content)
        target_heading, ambiguous_paths = _find_heading_by_path(headings, path_elements)

        if ambiguous_paths:
            formatted_paths = [f"{file_path}::{('::'.join(path))}" for path in ambiguous_paths]
            return _process_error(
                ValueError(
                    "Ambiguous heading reference. Multiple matches found:\n"
                    + "\n".join(f"  - {p}" for p in formatted_paths)
                    + "\nPlease be more specific."
                )
            )

        if not target_heading:
            return _process_error(ValueError(f"Target scope not found: {target_scope}"))

        if coscope_with:
            # Insertion within scope
            if (coscope_with.startswith('"') and coscope_with.endswith('"')) or (
                coscope_with.startswith("'") and coscope_with.endswith("'")
            ):
                # Pattern-based insertion
                pattern = coscope_with[1:-1]
                found_line = _find_pattern_in_section(lines, target_heading, pattern)

                if found_line is None:
                    return _process_error(ValueError(f"Pattern not found in section: {coscope_with}"))

                # Check for duplicates
                lines = _check_for_duplicate_headings(lines, content, target_heading)

                # Re-resolve target_heading after lines have been modified
                target_heading = _re_resolve_heading(lines, path_elements)
                if not target_heading:
                    return _process_error(ValueError(f"Target scope not found after duplicate removal: {target_scope}"))

                # Re-find the pattern line in the modified lines
                found_line = _find_pattern_in_section(lines, target_heading, pattern)
                if found_line is None:
                    return _process_error(ValueError(f"Pattern not found in section after duplicate removal: {coscope_with}"))

                modified_lines = _insert_after_pattern(lines, found_line, content)
                _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
                return f"Content inserted after pattern in '{abs_path}'."
            else:
                # Heading-based insertion (insert after a subheading)
                # Parse the coscope_with as a heading path
                insert_after_elements = coscope_with.split("::")
                insert_after_heading, ambiguous_paths = _find_heading_by_path(headings, insert_after_elements)

                if ambiguous_paths:
                    formatted_paths = [f"{file_path}::{('::'.join(path))}" for path in ambiguous_paths]
                    return _process_error(
                        ValueError(
                            "Ambiguous heading reference. Multiple matches found:\n"
                            + "\n".join(f"  - {p}" for p in formatted_paths)
                            + "\nPlease be more specific."
                        )
                    )

                if not insert_after_heading:
                    return _process_error(ValueError(f"Insert point not found: {coscope_with}"))

                # Verify it's within the target scope
                if not (
                    insert_after_heading.start_line >= target_heading.start_line
                    and insert_after_heading.end_line <= target_heading.end_line
                ):
                    return _process_error(
                        ValueError(f"Insert point '{coscope_with}' is not within target scope '{target_scope}'")
                    )

                # Check for duplicates
                lines = _check_for_duplicate_headings(lines, content, target_heading)

                # Re-resolve both headings after lines have been modified
                target_heading = _re_resolve_heading(lines, path_elements)
                if not target_heading:
                    return _process_error(ValueError(f"Target scope not found after duplicate removal: {target_scope}"))

                insert_after_heading = _re_resolve_heading(lines, insert_after_elements)
                if not insert_after_heading:
                    return _process_error(ValueError(f"Insert point not found after duplicate removal: {coscope_with}"))

                modified_lines = _insert_after_heading(lines, insert_after_heading, content)
                _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
                return f"Content inserted after '{coscope_with}' in '{abs_path}'."
        else:
            # Replacement within scope
            modified_lines = _replace_section(lines, target_heading, content)

            # Safety check for large deletions in scoped replacements
            lines_deleted = len(lines) - len(modified_lines)
            if lines_deleted > 100 and not delete_a_lot:
                return _process_error(
                    ValueError(
                        f"Safety check: this operation would delete {lines_deleted} lines in scope '{target_scope}'. "
                        + "If intentional, set delete_a_lot=True."
                    )
                )

            _write_file_bom_safe(abs_path, _join_lines_preserve_trailing_newline(modified_lines, original_content))
            return f"Content replaced at '{target_scope}'."

    except Exception as e:
        return _process_error(e)
