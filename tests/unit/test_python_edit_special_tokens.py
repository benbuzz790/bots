"""Tests for python_edit special tokens (__FILE_START__ and __FILE_END__)."""

import os
import tempfile

from bots.tools.python_edit import python_edit


class TestFileStartToken:
    """Tests for __FILE_START__ special token."""

    def test_file_start_preserves_docstring(self):
        """Test that __FILE_START__ preserves module docstring at the top."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Module docstring."""
import os

def foo():
    pass
'''
            )
            temp_file = f.name

        try:
            new_code = """import sys
import json
"""

            result = python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_START__")

            assert "after docstring/future imports" in result

            with open(temp_file, "r") as f:
                content = f.read()

            # Docstring should still be first - don't use strip() to catch leading whitespace issues
            assert content.startswith('"""Module docstring."""')
            # New imports should come after docstring
            assert "import sys" in content
            assert content.index('"""') < content.index("import sys")

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_start_respects_future_imports(self):
        """Test that __FILE_START__ places imports after __future__ imports."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Module with future imports."""
from __future__ import annotations
from __future__ import division

import os

def foo():
    pass
'''
            )
            temp_file = f.name

        try:
            new_code = """import sys
import json
"""

            python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_START__")

            with open(temp_file, "r") as f:
                content = f.read()

            lines = content.strip().split("\n")

            # Find positions
            future_end_pos = 0
            new_import_pos = None

            for i, line in enumerate(lines):
                if "from __future__" in line:
                    future_end_pos = i
                if "import sys" in line:
                    new_import_pos = i
                    break

            # Verify order: docstring, __future__, new imports
            assert lines[0].startswith('"""')
            assert new_import_pos > future_end_pos

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_start_filters_duplicate_imports(self):
        """Test that __FILE_START__ filters out duplicate imports."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """import os
import sys

def foo():
    pass
"""
            )
            temp_file = f.name

        try:
            # Try to add imports that already exist
            new_code = """import os
import json
"""

            result = python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_START__")

            assert "duplicate imports filtered" in result

            with open(temp_file, "r") as f:
                content = f.read()

            # Should only have one 'import os'
            assert content.count("import os") == 1
            # Should have the new import
            assert "import json" in content

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_start_with_non_py_file(self):
        """Test that __FILE_START__ works with non-.py files as text mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                """# Existing Header

Some content
"""
            )
            temp_file = f.name

        try:
            new_code = """# New Header

New content
"""

            result = python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_START__")

            assert "text mode" in result
            assert "Error" not in result

            with open(temp_file, "r") as f:
                content = f.read()

            # New content should be at the start
            assert content.startswith("# New Header")
            # Original content should still be there
            assert "# Existing Header" in content

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_start_removes_duplicate_definitions(self):
        """Test that __FILE_START__ removes duplicate function/class definitions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """import os

def helper():
    return 42
"""
            )
            temp_file = f.name

        try:
            # Try to add the same function
            new_code = """import sys

def helper():
    return 99
"""

            result = python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_START__")

            assert "Overwrote" in result or "duplicate" in result.lower()

            with open(temp_file, "r") as f:
                content = f.read()

            # Should only have one 'def helper()'
            assert content.count("def helper():") == 1
            # Should have the new version
            assert "return 99" in content
            assert "return 42" not in content

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestFileEndToken:
    """Tests for __FILE_END__ special token."""

    def test_file_end_appends_code(self):
        """Test that __FILE_END__ appends code to the end of file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """import os

def foo():
    pass
"""
            )
            temp_file = f.name

        try:
            new_code = """
def bar():
    pass
"""

            result = python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_END__")

            assert "inserted at end" in result

            with open(temp_file, "r") as f:
                content = f.read()

            # New function should be at the end
            assert "def bar():" in content
            # Original content should still be there
            assert "def foo():" in content
            # bar should come after foo
            assert content.index("def foo():") < content.index("def bar():")

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_end_with_non_py_file(self):
        """Test that __FILE_END__ works with non-.py files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Existing content\n")
            temp_file = f.name

        try:
            new_code = "New content at end"

            result = python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_END__")

            assert "text mode" in result

            with open(temp_file, "r") as f:
                content = f.read()

            assert "Existing content" in content
            assert "New content at end" in content
            assert content.index("Existing") < content.index("New content")

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_file_end_removes_duplicates(self):
        """Test that __FILE_END__ removes duplicate definitions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """import os

def existing_function():
    pass
"""
            )
            temp_file = f.name

        try:
            # Try to add the same function at the end
            new_code = """def existing_function():
    return 42
"""

            python_edit(target_scope=temp_file, code=new_code, coscope_with="__FILE_END__")

            with open(temp_file, "r") as f:
                content = f.read()

            # Should only have one definition
            assert content.count("def existing_function():") == 1

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestSpecialTokenErrors:
    """Tests for error handling with special tokens."""

    def test_special_tokens_cannot_be_used_with_scoped_targets(self):
        """Test that __FILE_START__/__FILE_END__ cannot be used with scoped targets."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """class MyClass:
    def method(self):
        pass
"""
            )
            temp_file = f.name

        try:
            result = python_edit(
                target_scope=f"{temp_file}::MyClass", code="def new_method(self): pass", coscope_with="__FILE_START__"
            )

            assert "Error" in result or "cannot use" in result.lower()

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
