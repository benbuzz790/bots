import os
from textwrap import dedent

import pytest

from bots.tools.markdown_edit import markdown_edit, markdown_view


def setup_test_file(tmp_path, content):
    """Helper to create a test markdown file with given content"""
    from tests.conftest import create_safe_test_file, get_unique_filename

    if isinstance(tmp_path, str):
        # Use safe test file creation for string paths
        return create_safe_test_file(dedent(content), "test_file", "md", tmp_path)
    else:
        # For pytest tmp_path fixture, use the standard approach (it auto-cleans)
        # Ensure the tmp_path directory exists (handle xdist race conditions)
        if not tmp_path.exists():
            try:
                tmp_path.mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                # Another worker created it, that's fine
                pass

        test_file = os.path.join(str(tmp_path), get_unique_filename("test_file", "md"))
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(dedent(content))
        return test_file


@pytest.fixture
def test_file(tmp_path):
    """Create a test markdown file with various heading levels"""
    content = """
    # Main Heading

    This is some content under the main heading.

    ## Section One

    Content in section one.

    ### Subsection A

    Content in subsection A.

    ### Subsection B

    Content in subsection B.

    ## Section Two

    Content in section two.

    ### Subsection C

    Content in subsection C.
    """
    return setup_test_file(tmp_path, content)


def test_basic_file_level_edit(test_file):
    """Test replacing entire file content"""
    result = markdown_edit(test_file, "# New Content\n\nThis is new.")
    assert "file level" in result.lower() or "replaced" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "# New Content" in content
    assert "This is new." in content


def test_file_start_insertion(test_file):
    """Test inserting at file start"""
    result = markdown_edit(test_file, "# Frontmatter\n\nAdded at start.", coscope_with="__FILE_START__")
    assert "start" in result.lower()
    with open(test_file) as f:
        lines = f.readlines()
    assert "# Frontmatter" in lines[0]


def test_file_end_insertion(test_file):
    """Test inserting at file end"""
    result = markdown_edit(test_file, "## Appendix\n\nAdded at end.", coscope_with="__FILE_END__")
    assert "end" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "## Appendix" in content
    assert content.strip().endswith("Added at end.")


def test_heading_replacement(test_file):
    """Test replacing a heading section"""
    new_section = """
    ## Section One

    This is the new content for section one.
    """
    result = markdown_edit(f"{test_file}::Section One", new_section)
    assert "Section One" in result
    with open(test_file) as f:
        content = f.read()
    assert "This is the new content for section one." in content
    assert "Content in section one." not in content


def test_nested_heading_replacement(test_file):
    """Test replacing a nested heading section"""
    new_subsection = """
    ### Subsection A

    New content for subsection A.
    """
    result = markdown_edit(f"{test_file}::Section One::Subsection A", new_subsection)
    assert "Subsection A" in result
    with open(test_file) as f:
        content = f.read()
    assert "New content for subsection A." in content
    assert "Content in subsection A." not in content


def test_insert_after_heading(test_file):
    """Test inserting after a heading using coscope_with"""
    result = markdown_edit(
        f"{test_file}::Section One",
        "### Subsection A2\n\nInserted subsection.",
        coscope_with="Section One::Subsection A",
    )
    assert "inserted after" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "### Subsection A2" in content
    assert "Inserted subsection." in content


def test_insert_after_simple_name(test_file):
    """Test inserting after a heading using simple name"""
    result = markdown_edit(
        f"{test_file}::Section One",
        "### New Subsection\n\nNew content.",
        coscope_with="Subsection A",
    )
    assert "inserted after" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "### New Subsection" in content


def test_insert_after_quoted_expression(test_file):
    """Test inserting after a quoted text pattern"""
    result = markdown_edit(
        f"{test_file}::Section One",
        "New paragraph inserted.",
        coscope_with='"Content in section one."',
    )
    assert "inserted after" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "New paragraph inserted." in content


def test_error_invalid_scope(test_file):
    """Test error handling for invalid scope"""
    result = markdown_edit(f"{test_file}::NonExistent Heading", "Content")
    assert "not found" in result.lower() or "error" in result.lower()


def test_error_invalid_insert_point(test_file):
    """Test error handling for invalid insert point"""
    result = markdown_edit(
        f"{test_file}::Section One",
        "Content",
        coscope_with="NonExistent",
    )
    assert "not found" in result.lower() or "error" in result.lower()


def test_empty_file(tmp_path):
    """Test handling empty target file"""
    empty_file = setup_test_file(tmp_path, "")
    result = markdown_edit(empty_file, "# New Document\n\nContent here.")
    assert "added" in result.lower()
    with open(empty_file) as f:
        content = f.read()
    assert "# New Document" in content


def test_file_creation(tmp_path):
    """Test creating a new file"""
    new_file = os.path.join(str(tmp_path), "new_doc.md")
    result = markdown_edit(new_file, "# New Document\n\nContent.")
    assert "added" in result.lower() or "created" in result.lower()
    assert os.path.exists(new_file)
    with open(new_file) as f:
        content = f.read()
    assert "# New Document" in content


def test_delete_section_with_empty_content(test_file):
    """Test deleting a section by providing empty content"""
    result = markdown_edit(f"{test_file}::Section One", "")
    assert "deleted" in result.lower() or "cleared" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "## Section One" not in content
    assert "## Section Two" in content


def test_delete_nested_section(test_file):
    """Test deleting a nested section"""
    result = markdown_edit(f"{test_file}::Section One::Subsection A", "")
    assert "deleted" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "### Subsection A" not in content
    assert "### Subsection B" in content


def test_delete_safety_check(tmp_path):
    """Test safety check for large deletions"""
    # Create a file with >100 lines
    large_content = "# Large Document\n\n" + "\n".join([f"Line {i}" for i in range(150)])
    test_file = setup_test_file(tmp_path, large_content)

    result = markdown_edit(test_file, "", delete_a_lot=False)
    assert "safety check" in result.lower() or "delete_a_lot" in result.lower()


def test_delete_with_override(tmp_path):
    """Test large deletion with delete_a_lot=True"""
    # Create a file with >100 lines
    large_content = "# Large Document\n\n" + "\n".join([f"Line {i}" for i in range(150)])
    test_file = setup_test_file(tmp_path, large_content)

    result = markdown_edit(test_file, "", delete_a_lot=True)
    assert "cleared" in result.lower() or "deleted" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert content.strip() == ""


def test_heading_with_special_characters(tmp_path):
    """Test headings with special characters"""
    content = """
    # Main Document

    ## Section: Special Characters!

    Content here.

    ## Another Section

    More content.
    """
    test_file = setup_test_file(tmp_path, content)
    result = markdown_edit(
        f"{test_file}::Section: Special Characters!",
        "## Section: Special Characters!\n\nUpdated content.",
    )
    assert "replaced" in result.lower()
    with open(test_file) as f:
        new_content = f.read()
    assert "Updated content." in new_content


def test_multiple_same_level_headings(tmp_path):
    """Test handling multiple headings at the same level"""
    content = """
    # Document

    ## First

    Content 1.

    ## Second

    Content 2.

    ## Third

    Content 3.
    """
    test_file = setup_test_file(tmp_path, content)
    result = markdown_edit(f"{test_file}::Second", "## Second\n\nNew content 2.")
    assert "replaced" in result.lower()
    with open(test_file) as f:
        new_content = f.read()
    assert "New content 2." in new_content
    assert "Content 1." in new_content
    assert "Content 3." in new_content


def test_markdown_view_whole_file(test_file):
    """Test viewing entire markdown file"""
    result = markdown_view(test_file)
    assert "# Main Heading" in result
    assert "## Section One" in result
    assert "## Section Two" in result


def test_markdown_view_section(test_file):
    """Test viewing a specific section"""
    result = markdown_view(f"{test_file}::Section One")
    assert "## Section One" in result
    assert "### Subsection A" in result
    assert "## Section Two" not in result


def test_markdown_view_nested_section(test_file):
    """Test viewing a nested section"""
    result = markdown_view(f"{test_file}::Section One::Subsection A")
    assert "### Subsection A" in result
    assert "Content in subsection A." in result
    assert "### Subsection B" not in result


def test_markdown_view_nonexistent_section(test_file):
    """Test viewing a nonexistent section"""
    result = markdown_view(f"{test_file}::Nonexistent")
    assert "not found" in result.lower() or "error" in result.lower()


def test_markdown_view_max_lines(tmp_path):
    """Test max_lines truncation in markdown_view"""
    # Create a large file
    large_content = "# Large Document\n\n" + "\n".join([f"Line {i}" for i in range(100)])
    test_file = setup_test_file(tmp_path, large_content)

    result = markdown_view(test_file, max_lines="20")
    lines = result.split("\n")
    assert len(lines) <= 25  # Allow some buffer for truncation message


def test_file_start_insertion_empty(tmp_path):
    """Test inserting at start of empty file"""
    test_file = setup_test_file(tmp_path, "")
    result = markdown_edit(test_file, "# Header\n\nContent.", coscope_with="__FILE_START__")
    assert result  # Check operation succeeded
    with open(test_file) as f:
        content = f.read()
    assert content.strip().startswith("# Header")


def test_file_end_insertion_empty(tmp_path):
    """Test inserting at end of empty file"""
    test_file = setup_test_file(tmp_path, "")
    result = markdown_edit(test_file, "# Header\n\nContent.", coscope_with="__FILE_END__")
    assert result  # Check operation succeeded
    with open(test_file) as f:
        content = f.read()
    assert "# Header" in content


def test_file_start_multiple_insertions(tmp_path):
    """Test multiple insertions at file start"""
    content = "# Original\n\nContent."
    test_file = setup_test_file(tmp_path, content)
    markdown_edit(test_file, "First insert.\n", coscope_with="__FILE_START__")
    markdown_edit(test_file, "Second insert.\n", coscope_with="__FILE_START__")
    with open(test_file) as f:
        lines = f.readlines()
    assert "Second insert." in lines[0]
    assert "First insert." in lines[1]


def test_file_end_multiple_insertions(tmp_path):
    """Test multiple insertions at file end"""
    content = "# Original\n\nContent."
    test_file = setup_test_file(tmp_path, content)
    markdown_edit(test_file, "\nFirst append.", coscope_with="__FILE_END__")
    markdown_edit(test_file, "\nSecond append.", coscope_with="__FILE_END__")
    with open(test_file) as f:
        content = f.read()
    assert content.index("First append.") < content.index("Second append.")


def test_preserve_blank_lines(tmp_path):
    """Test that blank lines are preserved"""
    content = """
    # Heading


    Paragraph with blank lines above.


    Another paragraph.
    """
    test_file = setup_test_file(tmp_path, content)
    result = markdown_edit(f"{test_file}::Heading", content)
    assert result  # Check operation succeeded
    with open(test_file) as f:
        new_content = f.read()
    # Count blank lines
    assert new_content.count("\n\n") >= 2


def test_heading_levels_1_to_6(tmp_path):
    """Test all heading levels from # to ######"""
    content = """
    # Level 1
    ## Level 2
    ### Level 3
    #### Level 4
    ##### Level 5
    ###### Level 6
    """
    test_file = setup_test_file(tmp_path, content)

    # Test replacing level 4
    result = markdown_edit(f"{test_file}::Level 1::Level 2::Level 3::Level 4", "#### Level 4\n\nNew content.")
    assert "replaced" in result.lower()
    with open(test_file) as f:
        new_content = f.read()
    assert "New content." in new_content


def test_duplicate_heading_removal(tmp_path):
    """Test that duplicate headings are removed when inserting"""
    content = """
    # Document

    ## Section A

    Content A.

    ## Section B

    Content B.
    """
    test_file = setup_test_file(tmp_path, content)

    # Insert a section that already exists
    result = markdown_edit(
        test_file,
        "## Section A\n\nNew content A.",
        coscope_with="__FILE_END__",
    )
    assert result  # Check operation succeeded

    with open(test_file) as f:
        content = f.read()

    # Count occurrences of "## Section A"
    count = content.count("## Section A")
    assert count == 1, f"Expected 1 occurrence of '## Section A', found {count}"


def test_code_blocks_preserved(tmp_path):
    """Test that code blocks with # are not treated as headings"""
    content = """
    # Document

    ## Code Example

    ```python
    # This is a comment, not a heading
    def function():
        pass
    ```

    ## Another Section

    Content.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(
        f"{test_file}::Code Example", content[content.index("## Code Example") : content.index("## Another Section")]
    )
    assert result  # Check operation succeeded
    with open(test_file) as f:
        new_content = f.read()
    assert "# This is a comment, not a heading" in new_content


def test_inline_code_with_hash(tmp_path):
    """Test that inline code with # is preserved"""
    content = """
    # Document

    Use `#include` for C headers.

    ## Section

    More content.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Document", content)
    assert result  # Check operation succeeded
    with open(test_file) as f:
        new_content = f.read()
    assert "`#include`" in new_content


def test_atx_style_headings_only(tmp_path):
    """Test that only ATX-style headings (# prefix) are recognized"""
    content = """
    # ATX Heading

    Setext Heading
    ==============

    This should not be treated as a heading.

    ## Another ATX

    Content.
    """
    test_file = setup_test_file(tmp_path, content)

    # Should be able to find ATX heading
    result = markdown_view(f"{test_file}::ATX Heading")
    assert "# ATX Heading" in result

    # Setext heading should not be recognized as a scope
    result = markdown_view(f"{test_file}::Setext Heading")
    assert "not found" in result.lower() or "error" in result.lower()


def test_heading_with_trailing_hashes(tmp_path):
    """Test headings with trailing # characters"""
    content = """
    # Heading One #

    Content.

    ## Heading Two ##

    More content.
    """
    test_file = setup_test_file(tmp_path, content)

    # Should match heading without trailing hashes
    result = markdown_edit(f"{test_file}::Heading One", "# Heading One\n\nNew content.")
    assert "replaced" in result.lower()


def test_whitespace_in_heading_names(tmp_path):
    """Test headings with various whitespace"""
    content = """
    # Heading  With  Spaces

    Content.

    ## Another Heading

    More.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Heading  With  Spaces", "# Heading  With  Spaces\n\nNew.")
    assert "replaced" in result.lower()


def test_case_sensitive_headings(tmp_path):
    """Test that heading matching is case-sensitive"""
    content = """
    # Introduction

    Content.

    ## INTRODUCTION

    Different content.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Introduction", "# Introduction\n\nUpdated.")
    assert result  # Check operation succeeded
    with open(test_file) as f:
        new_content = f.read()
    assert "Updated." in new_content
    assert "## INTRODUCTION" in new_content


def test_empty_heading_content(tmp_path):
    """Test heading with no content below it"""
    content = """
    # Heading One

    ## Heading Two

    ## Heading Three
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Heading One::Heading Two", "## Heading Two\n\nNew content.")
    assert "replaced" in result.lower()


def test_file_without_extension_error(tmp_path):
    """Test that files without .md extension get appropriate handling"""
    test_file = os.path.join(str(tmp_path), "test_file")
    result = markdown_edit(test_file, "Content")
    # Should either create it or warn
    assert "warning" in result.lower() or os.path.exists(test_file)


def test_ambiguous_heading_same_name_different_parents(tmp_path):
    """Test error when same heading name exists under different parents"""
    content = """
    # Parent One

    ## Common Name

    Content under parent one.

    # Parent Two

    ## Common Name

    Content under parent two.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Common Name", "New content")
    assert "ambiguous" in result.lower()
    assert "Parent One::Common Name" in result
    assert "Parent Two::Common Name" in result


def test_ambiguous_heading_same_name_different_levels(tmp_path):
    """Test error when same heading name exists at different nesting levels"""
    content = """
    # Section

    ## Subsection

    ### Details

    Content at level 3.

    ## Details

    Content at level 2.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Details", "New content")
    assert "ambiguous" in result.lower()
    assert "Section::Subsection::Details" in result
    assert "Section::Details" in result


def test_unique_heading_no_ambiguity(tmp_path):
    """Test that unique heading names work without ambiguity errors"""
    content = """
    # Parent One

    ## Unique Name

    Content.

    # Parent Two

    ## Different Name

    Content.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Unique Name", "## Unique Name\n\nNew content")
    assert "replaced" in result.lower()
    assert "ambiguous" not in result.lower()

    with open(test_file, "r") as f:
        content = f.read()
    assert "New content" in content


def test_full_path_resolves_ambiguity(tmp_path):
    """Test that specifying full path works even when duplicates exist"""
    content = """
    # Parent One

    ## Common Name

    Content under parent one.

    # Parent Two

    ## Common Name

    Content under parent two.
    """
    test_file = setup_test_file(tmp_path, content)

    # Full path should work
    result = markdown_edit(f"{test_file}::Parent One::Common Name", "## Common Name\n\nUpdated content")
    assert "replaced" in result.lower()
    assert "ambiguous" not in result.lower()

    with open(test_file, "r") as f:
        content = f.read()
    assert "Updated content" in content
    assert content.count("Common Name") == 2  # Both headings still exist


def test_ambiguous_heading_three_matches(tmp_path):
    """Test error message with three or more matches"""
    content = """
    # Section A

    ## Info

    Content A.

    # Section B

    ## Info

    Content B.

    # Section C

    ## Info

    Content C.
    """
    test_file = setup_test_file(tmp_path, content)

    result = markdown_edit(f"{test_file}::Info", "New content")
    assert "ambiguous" in result.lower()
    assert "Section A::Info" in result
    assert "Section B::Info" in result
    assert "Section C::Info" in result
