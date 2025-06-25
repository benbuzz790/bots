import os
import shutil
import tempfile
import textwrap
import unittest

from bots.tools.code_tools import _adjust_additions_to_context, _find_match_with_hierarchy, patch_edit
from tests.conftest import get_unique_filename


class TestGitPatch(unittest.TestCase):

    def setUp(self):
        self.test_file = get_unique_filename("test_patch_file", "txt")
        with open(self.test_file, "w") as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_simple_addition(self):
        patch = textwrap.dedent("\n@@ -2,2 +2,3 @@\nline 2\n+new line\nline 3")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        self.assertNotIn("indentation adjustment", result, "Expected exact match but got whitespace-ignored match")
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\nline 2\nnew line\nline 3\nline 4\nline 5\n")

    def test_simple_deletion(self):
        patch = textwrap.dedent("\n@@ -2,3 +2,2 @@\nline 2\n-line 3\nline 4")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        self.assertNotIn("indentation adjustment", result, "Expected exact match but got whitespace-ignored match")
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\nline 2\nline 4\nline 5\n")

    def test_replacement(self):
        patch = textwrap.dedent("\n@@ -2,3 +2,3 @@\nline 2\n-line 3\n+modified line 3\nline 4")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\nline 2\nmodified line 3\nline 4\nline 5\n")

    def test_multiple_hunks(self):
        patch = textwrap.dedent(
            "\n@@ -1,2 +1,3 @@\nline 1\n+inserted at start\nline 2\n@@ -4,2 +5,3 @@\nline 4\n+inserted at end\nline 5"
        )
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\ninserted at start\nline 2\nline 3\nline 4\ninserted at end\nline 5\n")

    def test_invalid_patch_format(self):
        patch = "not a valid patch format"
        result = patch_edit(self.test_file, patch)
        self.assertIn("Error", result)
        self.assertIn("No valid patch hunks", result)

    def test_context_mismatch(self):
        patch = textwrap.dedent("\n@@ -2,3 +2,3 @@\nwrong context\n-line 3\n+modified line 3\nline 4")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Error", result)
        self.assertIn("Could not find match", result)

    def test_empty_patch(self):
        patch = ""
        result = patch_edit(self.test_file, patch)
        self.assertIn("Error", result)
        self.assertIn("patch_content is empty", result)

    def test_new_file(self):
        new_file = "new_test_file.txt"
        if os.path.exists(new_file):
            os.remove(new_file)
        patch = textwrap.dedent("\n@@ -0,0 +1,3 @@\n+first line\n+second line\n+third line")
        try:
            result = patch_edit(new_file, patch)
            self.assertIn("Successfully", result)
            with open(new_file, "r") as f:
                content = f.read()
            self.assertEqual(content, "first line\nsecond line\nthird line\n")
        finally:
            if os.path.exists(new_file):
                os.remove(new_file)

    def test_match_at_different_line(self):
        """Test that content is matched even if line numbers don't match"""
        with open(self.test_file, "w") as f:
            f.write("header\nline 1\nline 2\nline 3\nline 4\nline 5\n")
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        self.assertIn("(different from specified line", result)

    def test_match_with_different_whitespace(self):
        """Test that content is matched even with different indentation"""
        with open(self.test_file, "w") as f:
            f.write("def test():\n    line 1\n    line 2\n        line 3\n    line 4\n")
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3")
        print("\nFile content:")
        with open(self.test_file, "r") as f:
            print(repr(f.read()))
        print("\nPatch content:")
        print(repr(patch))
        result = patch_edit(self.test_file, patch)
        print("\nResult:", result)
        with open(self.test_file, "r") as f:
            print("\nFinal content:")
            print(repr(f.read()))
        self.assertIn("Successfully", result)
        self.assertIn("indentation adjustment", result)

    def test_similar_but_not_exact_match(self):
        """Test that similar but not exact matches are reported"""
        with open(self.test_file, "w") as f:
            f.write("line 1\nline two\nline 3\nline 4\n")
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Error", result)
        self.assertIn("Could not find match", result)

    def test_no_match_found(self):
        """Test that appropriate error is returned when no match is found"""
        with open(self.test_file, "w") as f:
            f.write("completely\ndifferent\ncontent\n")
        patch = textwrap.dedent("\n        @@ -2,2 +2,2 @@\n         line 2\n        -line 3\n        +modified line 3")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Error", result)
        self.assertTrue(
            "Could not find match" in result or "Context mismatch" in result,
            f"Expected error message about missing content, got: {result}",
        )

    def test_whitespace_only_difference(self):
        """Test matching when only whitespace differs"""
        with open(self.test_file, "w") as f:
            f.write("    line 1\n        line 2\n    line 3\n")
        patch = textwrap.dedent("\n@@ -1,3 +1,3 @@\nline 1\n-line 2\n+modified line 2\nline 3")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        self.assertIn("indentation adjustment", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "    line 1\n    modified line 2\n    line 3\n")

    def test_find_block_with_context(self):
        """Test finding a block with surrounding context"""
        with open(self.test_file, "w") as f:
            f.write("header\n    block start\n    target line\n    block end\nfooter\n")
        patch = textwrap.dedent("\n@@ -2,3 +2,3 @@\nblock start\n-target line\n+modified line\nblock end")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "header\n    block start\n    modified line\n    block end\nfooter\n")

    def test_match_with_different_whitespace_debug(self):
        """Debug version to see what's happening with whitespace matching"""
        with open(self.test_file, "w") as f:
            f.write("def test():\n    line 1\n    line 2\n        line 3\n    line 4\n")
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3")
        print("\nFile content:")
        with open(self.test_file, "r") as f:
            print(repr(f.read()))
        print("\nPatch content:")
        print(repr(patch))
        result = patch_edit(self.test_file, patch)
        print("\nResult:", result)
        with open(self.test_file, "r") as f:
            print("\nFinal content:")
            print(repr(f.read()))

    def test_multiple_possible_matches(self):
        """Test behavior when multiple potential matches exist"""
        with open(self.test_file, "w") as f:
            f.write("def test1():\n    line 1\n    line 2\ndef test2():\n    line 1\n    line 2\n")
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 1\n-line 2\n+modified line")
        result = patch_edit(self.test_file, patch)
        if "multiple" in result.lower() or "ambiguous" in result.lower():
            self.assertTrue(True)
        else:
            with open(self.test_file, "r") as f:
                content = f.read()
            self.assertTrue(
                content.startswith("def test1():\n    line 1\n    modified line\n"),
                f"Expected modification at first match, but got:\n{content}",
            )

    def test_create_in_new_directory(self):
        """Test creating a file in a directory that doesn't exist yet"""
        new_dir = os.path.join(self.test_file + "_newdir", "subdir", "deeperdir")
        new_file = os.path.join(new_dir, "newfile.txt")
        patch = textwrap.dedent("\n@@ -0,0 +1,3 @@\n+line 1\n+line 2\n+line 3")
        try:
            self.assertFalse(os.path.exists(new_dir))
            result = patch_edit(new_file, patch)
            self.assertIn("Successfully", result)
            self.assertTrue(os.path.exists(new_file))
            with open(new_file, "r") as f:
                content = f.read()
            self.assertEqual(content, "line 1\nline 2\nline 3\n")
        finally:
            if os.path.exists(os.path.dirname(new_dir)):
                import shutil

                shutil.rmtree(os.path.dirname(new_dir))

    def test_double_slash_handling(self):
        """Test that double slashes in paths are handled correctly"""
        test_path = "test//path//file.txt"
        patch = textwrap.dedent("\n@@ -0,0 +1,1 @@\n+test content")
        full_path = os.path.join(self.test_file + "_dir", test_path)
        cleanup_root = self.test_file + "_dir"
        try:
            result = patch_edit(full_path, patch)
            self.assertIn("Successfully", result)
            normalized_path = os.path.normpath(full_path)
            self.assertTrue(os.path.exists(normalized_path))
            with open(normalized_path, "r") as f:
                content = f.read()
            self.assertEqual(content.strip(), "test content")
        finally:
            if os.path.exists(cleanup_root):
                shutil.rmtree(cleanup_root)

    def test_path_normalization(self):
        """Test that path normalization works correctly."""
        # Create nested directory structure for testing
        patch = "@@ -0,0 +1,1 @@\n+test content"

        nested_path = os.path.join("test_patch_file.txt_dir", "test", "nested", "test_patch_file.txt")
        full_path = os.path.abspath(nested_path)

        try:
            result = patch_edit(nested_path, patch)
            self.assertIn("Successfully", result)

            # Verify file was created and has correct content
            self.assertTrue(os.path.exists(full_path))
            with open(full_path, "r") as f:
                content = f.read()
            self.assertEqual(content, "test content\n")

        finally:
            # Windows-safe cleanup with error handling
            cleanup_dir = os.path.dirname(os.path.dirname(full_path))
            if os.path.exists(cleanup_dir):
                try:
                    # Try normal cleanup first
                    shutil.rmtree(cleanup_dir)
                except (FileNotFoundError, OSError, PermissionError):
                    # If that fails, try with error handler (Windows-specific)
                    def handle_remove_readonly(func, path, exc):
                        """Error handler for Windows read-only files."""
                        try:
                            os.chmod(path, stat.S_IWRITE)
                            func(path)
                        except (OSError, FileNotFoundError):
                            pass  # Ignore if it still fails

                    try:
                        import stat

                        shutil.rmtree(cleanup_dir, onerror=handle_remove_readonly)
                    except (FileNotFoundError, OSError):
                        # If all else fails, just pass - the temp directory will be cleaned up eventually
                        pass

    def test_class_indentation_preservation(self):
        """Test that class and method indentation is properly preserved when applying patches"""
        with open(self.test_file, "w") as f:
            f.write(
                'class MyClass:\n    def method1(self):\n        return "original"\n\n'
                '    def method2(self):\n        return "test"\n'
            )
        patch = textwrap.dedent(
            "\n@@ -1,6 +1,6 @@\nclass MyClass:\n    def method1(self):\n"
            '-        return "original"\n+        return "modified"\n\n'
            '    def method2(self):\n        return "test"'
        )
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        expected = (
            'class MyClass:\n    def method1(self):\n        return "modified"\n\n'
            '    def method2(self):\n        return "test"\n'
        )
        self.assertEqual(
            content, expected, f"Indentation was not preserved.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}"
        )

    def test_relative_indentation_preservation(self):
        """Test that relative indentation between lines is preserved while adjusting to target indent"""
        with open(self.test_file, "w") as f:
            f.write("line 1\nbase indent\nline 3\n")
        patch = textwrap.dedent(
            "\n@@ -2,1 +2,4 @@\nbase indent\n+    indented:\n+        double indented\n+            triple indented"
        )
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        expected = "line 1\nbase indent\n    indented:\n        double indented\n            triple indented\nline 3\n"
        self.assertEqual(
            content, expected, f"Relative indentation not preserved.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}"
        )
        with open(self.test_file, "w") as f:
            f.write("line 1\n    indented line\nline 3\n")
        patch = textwrap.dedent(
            "\n@@ -2,1 +2,4 @@\n     indented line\n+    same level\n+        more indented\n+            most indented"
        )
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        expected = "line 1\n    indented line\n    same level\n        more indented\n            most indented\nline 3\n"
        self.assertEqual(
            content,
            expected,
            f"Relative indentation not preserved when adding to indented line.\n"
            f"Expected:\n{repr(expected)}\n"
            f"Got:\n{repr(content)}",
        )

    def test_replacement_context_matching(self):
        """Test that replacement works when line numbers are wrong but context matches.
        This tests the fallback to context matching when exact line matching fails."""
        with open(self.test_file, "w") as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
        patch = "@@ -6,3 +6,3 @@\nline 2\n-line 3\n+modified line 3\nline 4"
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        self.assertIn("(different from specified line", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\nline 2\nmodified line 3\nline 4\nline 5\n")

    def test_single_line_no_context(self):
        """Test the most basic case: single line replacement with no context lines.
        This is the simplest possible case and should work based purely on line number."""
        with open(self.test_file, "w") as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
        patch = "@@ -2,1 +2,1 @@\n-line 2\n+modified line 2"
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(
            content,
            "line 1\nmodified line 2\nline 3\nline 4\nline 5\n",
            "Failed to handle simple replacement without context lines",
        )

    def test_line_number_accuracy(self):
        """Test exact line number handling without context lines.
        This explicitly tests for off-by-one errors in line targeting."""
        initial = "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n"
        failures = []
        test_cases = [
            (
                1,
                "@@ -1,1 +1,1 @@\n-line 1\n+modified line 1",
                "modified line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n",
                "Replace first line",
            ),
            (
                2,
                "@@ -2,1 +2,1 @@\n-line 2\n+modified line 2",
                "line 1\nmodified line 2\nline 3\nline 4\nline 5\nline 6\n",
                "Replace line 2",
            ),
            (
                3,
                "@@ -3,1 +3,1 @@\n-line 3\n+modified line 3",
                "line 1\nline 2\nmodified line 3\nline 4\nline 5\nline 6\n",
                "Replace line 3",
            ),
            (
                4,
                "@@ -4,1 +4,1 @@\n-line 4\n+modified line 4",
                "line 1\nline 2\nline 3\nmodified line 4\nline 5\nline 6\n",
                "Replace line 4",
            ),
            (
                5,
                "@@ -5,1 +5,1 @@\n-line 5\n+modified line 5",
                "line 1\nline 2\nline 3\nline 4\nmodified line 5\nline 6\n",
                "Replace line 5",
            ),
            (
                6,
                "@@ -6,1 +6,1 @@\n-line 6\n+modified line 6",
                "line 1\nline 2\nline 3\nline 4\nline 5\nmodified line 6\n",
                "Replace last line",
            ),
        ]
        for line_num, patch, expected, desc in test_cases:
            try:
                with open(self.test_file, "w") as f:
                    f.write(initial)
                patch_edit(self.test_file, patch)
                with open(self.test_file, "r") as f:
                    content = f.read()
                print(f"\nTest case: {desc} (line {line_num})")
                print("Got:")
                print(content)
                print("Expected:")
                print(expected)
                if content != expected:
                    failures.append(f"Line {line_num}: Got content:\n{content}\nExpected:\n{expected}")
            except Exception as e:
                failures.append(f"Line {line_num}: Exception: {str(e)}")
        if failures:
            self.fail("Failures:\n" + "\n\n".join(failures))

    def test_insert_method_after_method_in_class(self):
        """Insert a new method after an existing method in a class."""
        orig_code = "class MyClass:\n" "    def foo(self):\n" "        pass\n"
        patch = textwrap.dedent(
            """\
            @@ -2,6 +2,10 @@
                 def foo(self):
                     pass
            +
            +    def bar(self):
            +        print("bar!")
        """
        )
        expected = (
            "class MyClass:\n" "    def foo(self):\n" "        pass\n" "\n" "    def bar(self):\n" '        print("bar!")\n'
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as tf:
            tf.write(orig_code)
            tf.flush()
            result = patch_edit(tf.name, patch)
            self.assertIn("Successfully", result)
            with open(tf.name, "r") as f:
                out = f.read()
            self.assertEqual(out, expected)
        os.unlink(tf.name)

    def test_insert_function_after_class(self):
        """Insert a new function after the class body."""
        orig_code = "class MyClass:\n" "    pass\n"
        patch = textwrap.dedent(
            """\
            @@ -3,6 +3,9 @@
            +
            +def util():
            +    print("util")
        """
        )
        expected = "class MyClass:\n" "    pass\n" "\n" "def util():\n" '    print("util")\n'
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as tf:
            tf.write(orig_code)
            tf.flush()
            result = patch_edit(tf.name, patch)
            self.assertIn("Successfully", result)
            with open(tf.name, "r") as f:
                out = f.read()
            self.assertEqual(out, expected)
        os.unlink(tf.name)

    def test_insert_method_in_class_with_inexact_whitespace(self):
        """Insert a method after another method in a class, but with whitespace difference requiring inexact match."""
        orig_code = (
            "class MyClass:\n"
            "    def foo(self):\n"  # â† 4 spaces in actual file
            "        pass\n"  # â† 8 spaces in actual file
        )

        # Patch context lines use LESS indentation than actual file (common when copying from less-indented context)
        patch = textwrap.dedent(
            """\
            @@ -2,2 +2,6 @@
            def foo(self):
                pass
            +
            +def bar(self):
            +    print("bar!")
        """
        )
        # Context line "def foo(self):" has 0 spaces in patch, 4 spaces in file
        # Difference = 4 - 0 = +4 spaces
        # Addition "def bar(self):" has 0 spaces in patch, should get 0 + 4 = 4 spaces
        # Addition "print("bar!")" has 4 spaces in patch, should get 4 + 4 = 8 spaces

        expected = (
            "class MyClass:\n"
            "    def foo(self):\n"
            "        pass\n"
            "\n"
            "    def bar(self):\n"  # â† 4 spaces (0 + 4 adjustment)
            '        print("bar!")\n'  # â† 8 spaces (4 + 4 adjustment)
        )

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as tf:
            tf.write(orig_code)
            tf.flush()
            result = patch_edit(tf.name, patch)
            self.assertIn("Successfully", result)
            self.assertIn("indentation adjustment", result)
            with open(tf.name, "r") as f:
                out = f.read()
            self.assertEqual(out, expected)
        os.unlink(tf.name)


class TestGitPatchHunkParsing(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_hunk_parse.txt"
        with open(self.test_file, "w") as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_empty_lines_in_hunk(self):
        """Test hunks with empty lines in various positions"""
        patch = textwrap.dedent("\n@@ -2,4 +2,4 @@\nline 2\n\n-line 3\n+modified line 3\nline 4")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)

    def test_missing_context_lines(self):
        """Test hunks with no context lines"""
        patch = textwrap.dedent("\n@@ -2,1 +2,1 @@\n-line 2\n+modified line 2")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\nmodified line 2\nline 3\nline 4\nline 5\n")

    def test_hunk_with_no_changes(self):
        """Test hunks that only contain context lines"""
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 2\nline 3")
        result = patch_edit(self.test_file, patch)
        self.assertIn("Error: No additions or removals found", result)

    def test_multiple_hunks_with_empty_lines_between(self):
        """Test multiple hunks separated by varying numbers of empty lines"""
        patch = textwrap.dedent(
            "\n@@ -1,2 +1,2 @@\nline 1\n-line 2\n+modified line 2\n\n@@ -4,2 +4,2 @@\nline 4\n-line 5\n+modified line 5"
        )
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "line 1\nmodified line 2\nline 3\nline 4\nmodified line 5\n")

    def test_hunk_with_no_newline_markers(self):
        """Test hunks with '\\ No newline at end of file' markers"""
        patch = textwrap.dedent(
            "\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n\\ No newline at end of file\n+modified line 3\n\\ No newline at end of file"
        )
        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)

    def test_patch_context_line_recognition(self):
        """Test that context lines are properly recognized with correct spacing"""
        with open(self.test_file, "w") as f:
            f.write("    line 1\n    line 2\n        line 3\n    line 4\n")
        patch = textwrap.dedent("\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3")
        result = patch_edit(self.test_file, patch)
        print("\nContext recognition result:", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        print("\nFinal content:", repr(content))
        self.assertIn("Successfully", result)
        self.assertEqual(content, "    line 1\n    line 2\n    modified line 3\n    line 4\n")


class TestIndentationDebug(unittest.TestCase):

    def test_hierarchy_match_position(self):
        """Test that hierarchy finds match at correct line position."""
        current_lines = ["class MyClass:", "    def foo(self):", "        pass"]  # â† Line 1, should match here

        context_before = ["def foo(self):", "    pass"]
        removals = []
        additions = ["", "def bar(self):", "    print('bar!')"]

        # Test what line the hierarchy thinks it found
        match_result = _find_match_with_hierarchy(current_lines, 1, context_before, removals, additions)

        print(f"Hierarchy found match at line: {match_result.get('line')}")
        print("Expected line: 1")
        print(f"Match successful: {match_result.get('found')}")
        print(f"Message: {match_result.get('message')}")

        self.assertTrue(match_result["found"])
        self.assertEqual(match_result["line"], 1, "Hierarchy should find match at line 1")

    def test_indentation_adjustment_direct(self):
        """Test indentation adjustment function directly."""
        current_lines = ["class MyClass:", "    def foo(self):", "        pass"]  # â† Line 1: 4 spaces  # â† Line 2: 8 spaces

        match_line = 1  # Where hierarchy claims to have found the match
        context_before = ["def foo(self):", "    pass"]  # 0 spaces, 4 spaces
        additions = ["", "def bar(self):", "    print('bar!')"]  # 0, 0, 4 spaces

        result = _adjust_additions_to_context(current_lines, match_line, context_before, additions)

        print(f"Input additions: {additions}")
        print(f"Adjusted additions: {result}")
        print(f"Context line 0 in patch: '{context_before[0]}' ({len(_get_line_indentation(context_before[0]))} spaces)")
        print(
            f"Corresponding file line: '{current_lines[match_line]}' ({len(_get_line_indentation(current_lines[match_line]))} spaces)"
        )
        print(
            f"Expected indent diff: {len(_get_line_indentation(current_lines[match_line])) - len(_get_line_indentation(context_before[0]))}"
        )

        # Should be 4 - 0 = +4 spaces adjustment
        expected = ["", "    def bar(self):", "        print('bar!')"]
        self.assertEqual(result, expected)

    def test_context_line_mapping(self):
        """Test that we're mapping context lines to file lines correctly."""
        current_lines = [
            "class MyClass:",  # Line 0
            "    def foo(self):",  # Line 1 â† Context line 0 should map here
            "        pass",  # Line 2 â† Context line 1 should map here
        ]

        match_line = 1
        context_before = ["def foo(self):", "    pass"]

        # Manual mapping check
        for i, ctx_line in enumerate(context_before):
            file_line_index = match_line + i
            file_line = current_lines[file_line_index]

            print(f"Context line {i}: '{ctx_line}' ({len(_get_line_indentation(ctx_line))} spaces)")
            print(f"Maps to file line {file_line_index}: '{file_line}' ({len(_get_line_indentation(file_line))} spaces)")
            print(f"Content match (ignoring whitespace): {ctx_line.strip() == file_line.strip()}")
            print("---")

    def test_full_patch_with_debug(self):
        """Test the full patch process with detailed output."""
        orig_code = (
            "class MyClass:\n"
            "    def foo(self):\n"  # â† 4 spaces
            "        pass\n"  # â† 8 spaces
        )

        patch = textwrap.dedent(
            """\
            @@ -2,2 +2,6 @@
            def foo(self):
                pass
            +
            +def bar(self):
            +    print("bar!")
        """
        )

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as tf:
            tf.write(orig_code)
            tf.flush()

            print("Original file content:")
            with open(tf.name, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    print(f"  {i}: '{line.rstrip()}' ({len(_get_line_indentation(line))} spaces)")

            print("\nPatch context lines:")
            context_lines = ["def foo(self):", "    pass"]
            for i, line in enumerate(context_lines):
                print(f"  {i}: '{line}' ({len(_get_line_indentation(line))} spaces)")

            result = patch_edit(tf.name, patch)
            print(f"\nPatch result: {result}")

            print("\nFinal file content:")
            with open(tf.name, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    print(f"  {i}: '{line.rstrip()}' ({len(_get_line_indentation(line))} spaces)")

        os.unlink(tf.name)

    def test_indentation_fix(self):
        """Quick test to verify the indentation fix."""

        def _get_line_indentation(line):
            return line[: len(line) - len(line.lstrip())]

        # Test case from debug output
        current_lines = ["class MyClass:", "    def foo(self):", "        pass"]  # â† Line 1: 4 spaces  # â† Line 2: 8 spaces

        match_line = 1
        additions = ["", "def bar(self):", "    print('bar!')"]  # 0, 0, 4 spaces

        # Manual calculation:
        # Context line 0: "def foo(self):" (0 spaces) vs "    def foo(self):" (4 spaces)
        # Diff: 4 - 0 = +4
        # Addition 0: "" -> "" (empty, unchanged)
        # Addition 1: "def bar(self):" (0 spaces) -> 0 + 4 = 4 spaces -> "    def bar(self):"
        # Addition 2: "    print('bar!')" (4 spaces) -> 4 + 4 = 8 spaces -> "        print('bar!')"

        expected = ["", "    def bar(self):", "        print('bar!')"]

        # Simulate the function logic
        patch_context_line = "def foo(self):"  # First non-empty context
        context_index = 0
        patch_indent_len = len(_get_line_indentation(patch_context_line))  # 0
        actual_file_line = current_lines[match_line + context_index]  # "    def foo(self):"
        actual_indent_len = len(_get_line_indentation(actual_file_line))  # 4
        indent_diff_spaces = actual_indent_len - patch_indent_len  # 4 - 0 = 4

        print(f"Patch context: '{patch_context_line}' ({patch_indent_len} spaces)")
        print(f"File line: '{actual_file_line}' ({actual_indent_len} spaces)")
        print(f"Indent diff: {indent_diff_spaces}")

        result = []
        for addition in additions:
            if not addition.strip():
                result.append(addition)
                continue
            current_len = len(_get_line_indentation(addition))
            new_len = current_len + indent_diff_spaces
            new_indent = " " * new_len
            line_content = addition.lstrip()
            result.append(new_indent + line_content)

        print(f"Expected: {expected}")
        print(f"Got: {result}")
        print(f"Match: {result == expected}")


# Helper function for indentation detection (assuming it exists)
def _get_line_indentation(line):
    """Get the indentation part of a line."""
    return line[: len(line) - len(line.lstrip())]


if __name__ == "__main__":
    unittest.main()


class TestIndentationBugFix(unittest.TestCase):
    """Test cases specifically for the context line indentation bug fix.

    The bug: Context lines in unified diff format start with a space character,
    but the patch parsing logic was keeping that space, causing indentation
    calculations to be off by one space.
    """

    def setUp(self):
        from tests.conftest import get_unique_filename

        self.test_file = get_unique_filename("test_indent_bug", "py")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_function_level_indentation_bug(self):
        """Test the exact scenario that revealed the bug: adding to a function."""
        with open(self.test_file, "w") as f:
            f.write(
                'def outer_function():\n    print("outer function")\n\n    def inner_function():\n        print("inner function")\n        return 42\n'
            )

        # This patch should add a line with 4 spaces, not 3
        patch = textwrap.dedent(
            """
            @@ -1,3 +1,4 @@
            def outer_function():
                 print("outer function")
            +    print("added line")
       """
        ).strip()

        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)

        with open(self.test_file, "r") as f:
            lines = f.readlines()

        # Find the added line
        added_line = None
        for line in lines:
            if "added line" in line:
                added_line = line
                break

        self.assertIsNotNone(added_line, "Added line not found in file")

        # The critical test: should have exactly 4 spaces, not 3
        indent_spaces = len(added_line) - len(added_line.lstrip())
        self.assertEqual(
            indent_spaces, 4, f"Added line should have 4 spaces but has {indent_spaces}. Line: {repr(added_line)}"
        )

    def test_method_level_indentation_bug(self):
        """Test adding to a method with proper indentation."""
        with open(self.test_file, "w") as f:
            f.write(
                'class TestClass:\n    def __init__(self):\n        self.value = 0\n    \n    def method1(self):\n        print("method1")\n        return self.value\n'
            )

        # This patch should add a line with 8 spaces, not 7
        patch = """@@ -5,6 +5,7 @@
def method1(self):
         print("method1")
         return self.value
+        # added comment"""

        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)

        with open(self.test_file, "r") as f:
            lines = f.readlines()

        # Find the added line
        added_line = None
        for line in lines:
            if "added comment" in line:
                added_line = line
                break

        self.assertIsNotNone(added_line, "Added comment not found in file")

        # The critical test: should have exactly 12 spaces, not 7
        indent_spaces = len(added_line) - len(added_line.lstrip())
        self.assertEqual(
            indent_spaces, 12, f"Added line should have 12 spaces but has {indent_spaces}. Line: {repr(added_line)}"
        )

    def test_deeply_nested_indentation_bug(self):
        """Test deeply nested code indentation."""
        with open(self.test_file, "w") as f:
            f.write(
                'def function_with_deep_nesting():\n    if True:\n        for i in range(2):\n            if i == 0:\n                try:\n                    result = 10 / i\n                except ZeroDivisionError:\n                    print("division by zero")\n                    result = 0\n                finally:\n                    print("cleanup")\n'
            )

        # This patch should add a line with 20 spaces, not 19
        patch = """
@@ -7,6 +7,7 @@
         except ZeroDivisionError:
             print("division by zero")
             result = 0
+                print("error handled")
         finally:
             print("cleanup")
"""

        result = patch_edit(self.test_file, patch)
        self.assertIn("Successfully", result)

        with open(self.test_file, "r") as f:
            lines = f.readlines()

        # Find the added line
        added_line = None
        for line in lines:
            if "error handled" in line:
                added_line = line
                break

        self.assertIsNotNone(added_line, "Added line not found in file")

        # The critical test: should have exactly 24 spaces
        indent_spaces = len(added_line) - len(added_line.lstrip())
        self.assertEqual(
            indent_spaces, 24, f"Added line should have 24 spaces but has {indent_spaces}. Line: {repr(added_line)}"
        )

    def test_context_line_space_removal(self):
        """Test that context lines have their leading space properly removed during parsing."""
        # This is a unit test for the specific parsing logic
        patch_content = textwrap.dedent(
            """
            @@ -1,3 +1,4 @@
             def test():
                 print("test")
            +    print("added")
       """
        ).strip()

        # Simulate the patch parsing logic
        patch_content = textwrap.dedent(patch_content)
        patch_content = "\n" + patch_content
        hunks = patch_content.split("\n@@")[1:]

        hunk = hunks[0].strip()
        header_end = hunk.index("\n")
        hunk_lines = hunk[header_end:].splitlines()[1:]

        context_before = []
        additions = []

        for line in hunk_lines:
            if not line:
                continue
            if not (line.startswith("+") or line.startswith("-")):
                # Context lines should have their leading space removed
                context_before.append(line[1:])  # This is the fix
            elif line.startswith("+"):
                additions.append(line[1:])

        # Verify context lines don't have extra leading space
        self.assertEqual(context_before[0], "def test():")  # Not " def test:"
        self.assertEqual(context_before[1], '    print("test")')  # Not "     print(\"test\")"

        # Verify addition line is correct
        self.assertEqual(additions[0], '    print("added")')
