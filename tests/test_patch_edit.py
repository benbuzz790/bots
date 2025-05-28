import os
import unittest
from bots.tools.code_tools import patch_edit
import textwrap
import tempfile

class TestGitPatch(unittest.TestCase):

    def setUp(self):
        self.test_file = 'test_patch_file.txt'
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline 2\nline 3\nline 4\nline 5\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_simple_addition(self):
        patch = textwrap.dedent('\n@@ -2,2 +2,3 @@\nline 2\n+new line\nline 3')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertNotIn('ignore whitespace', result, 'Expected exact match but got whitespace-ignored match')
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nnew line\nline 3\nline 4\nline 5\n')

    def test_simple_deletion(self):
        patch = textwrap.dedent('\n@@ -2,3 +2,2 @@\nline 2\n-line 3\nline 4')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertNotIn('ignore whitespace', result, 'Expected exact match but got whitespace-ignored match')
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nline 4\nline 5\n')

    def test_replacement(self):
        patch = textwrap.dedent('\n@@ -2,3 +2,3 @@\nline 2\n-line 3\n+modified line 3\nline 4')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nmodified line 3\nline 4\nline 5\n')

    def test_multiple_hunks(self):
        patch = textwrap.dedent('\n@@ -1,2 +1,3 @@\nline 1\n+inserted at start\nline 2\n@@ -4,2 +5,3 @@\nline 4\n+inserted at end\nline 5')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\ninserted at start\nline 2\nline 3\nline 4\ninserted at end\nline 5\n')

    def test_invalid_patch_format(self):
        patch = 'not a valid patch format'
        result = patch_edit(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('No valid patch hunks', result)

    def test_context_mismatch(self):
        patch = textwrap.dedent('\n@@ -2,3 +2,3 @@\nwrong context\n-line 3\n+modified line 3\nline 4')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('Could not find match', result)

    def test_empty_patch(self):
        patch = ''
        result = patch_edit(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('patch_content is empty', result)

    def test_new_file(self):
        new_file = 'new_test_file.txt'
        if os.path.exists(new_file):
            os.remove(new_file)
        patch = textwrap.dedent('\n@@ -0,0 +1,3 @@\n+first line\n+second line\n+third line')
        try:
            result = patch_edit(new_file, patch)
            self.assertIn('Successfully', result)
            with open(new_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, 'first line\nsecond line\nthird line\n')
        finally:
            if os.path.exists(new_file):
                os.remove(new_file)

    def test_match_at_different_line(self):
        """Test that content is matched even if line numbers don't match"""
        with open(self.test_file, 'w') as f:
            f.write('header\nline 1\nline 2\nline 3\nline 4\nline 5\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertIn('(different from specified line', result)

    def test_match_with_different_whitespace(self):
        """Test that content is matched even with different indentation"""
        with open(self.test_file, 'w') as f:
            f.write('def test():\n    line 1\n    line 2\n        line 3\n    line 4\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3')
        print('\nFile content:')
        with open(self.test_file, 'r') as f:
            print(repr(f.read()))
        print('\nPatch content:')
        print(repr(patch))
        result = patch_edit(self.test_file, patch)
        print('\nResult:', result)
        with open(self.test_file, 'r') as f:
            print('\nFinal content:')
            print(repr(f.read()))
        self.assertIn('Successfully', result)
        self.assertIn('ignore whitespace', result)

    def test_similar_but_not_exact_match(self):
        """Test that similar but not exact matches are reported"""
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline two\nline 3\nline 4\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('Could not find match', result)

    def test_no_match_found(self):
        """Test that appropriate error is returned when no match is found"""
        with open(self.test_file, 'w') as f:
            f.write('completely\ndifferent\ncontent\n')
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n         line 2\n        -line 3\n        +modified line 3')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertTrue('Could not find match' in result or 'Context mismatch' in result, f'Expected error message about missing content, got: {result}')

    def test_whitespace_only_difference(self):
        """Test matching when only whitespace differs"""
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n        line 2\n    line 3\n')
        patch = textwrap.dedent('\n@@ -1,3 +1,3 @@\nline 1\n-line 2\n+modified line 2\nline 3')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertIn('ignore whitespace', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, '    line 1\n        modified line 2\n    line 3\n')

    def test_indentation_preservation_simple(self):
        """Test that existing indentation is preserved on modified lines"""
        with open(self.test_file, 'w') as f:
            f.write('line 1\n    indented line\n        double indented\n')
        patch = textwrap.dedent('\n@@ -2,1 +2,1 @@\nindented line\n-double indented\n+modified line')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\n    indented line\n        modified line\n')

    def test_find_block_with_context(self):
        """Test finding a block with surrounding context"""
        with open(self.test_file, 'w') as f:
            f.write('header\n    block start\n    target line\n    block end\nfooter\n')
        patch = textwrap.dedent('\n@@ -2,3 +2,3 @@\nblock start\n-target line\n+modified line\nblock end')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'header\n    block start\n    modified line\n    block end\nfooter\n')

    def test_match_with_different_whitespace_debug(self):
        """Debug version to see what's happening with whitespace matching"""
        with open(self.test_file, 'w') as f:
            f.write('def test():\n    line 1\n    line 2\n        line 3\n    line 4\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3')
        print('\nFile content:')
        with open(self.test_file, 'r') as f:
            print(repr(f.read()))
        print('\nPatch content:')
        print(repr(patch))
        result = patch_edit(self.test_file, patch)
        print('\nResult:', result)
        with open(self.test_file, 'r') as f:
            print('\nFinal content:')
            print(repr(f.read()))

    def test_multiple_possible_matches(self):
        """Test behavior when multiple potential matches exist"""
        with open(self.test_file, 'w') as f:
            f.write('def test1():\n    line 1\n    line 2\ndef test2():\n    line 1\n    line 2\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 1\n-line 2\n+modified line')
        result = patch_edit(self.test_file, patch)
        if 'multiple' in result.lower() or 'ambiguous' in result.lower():
            self.assertTrue(True)
        else:
            with open(self.test_file, 'r') as f:
                content = f.read()
            self.assertTrue(content.startswith('def test1():\n    line 1\n    modified line\n'), f'Expected modification at first match, but got:\n{content}')

    def test_create_in_new_directory(self):
        """Test creating a file in a directory that doesn't exist yet"""
        new_dir = os.path.join(self.test_file + '_newdir', 'subdir', 'deeperdir')
        new_file = os.path.join(new_dir, 'newfile.txt')
        patch = textwrap.dedent('\n@@ -0,0 +1,3 @@\n+line 1\n+line 2\n+line 3')
        try:
            self.assertFalse(os.path.exists(new_dir))
            result = patch_edit(new_file, patch)
            self.assertIn('Successfully', result)
            self.assertTrue(os.path.exists(new_file))
            with open(new_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, 'line 1\nline 2\nline 3\n')
        finally:
            if os.path.exists(os.path.dirname(new_dir)):
                import shutil
                shutil.rmtree(os.path.dirname(new_dir))

    def test_double_slash_handling(self):
        """Test that double slashes in paths are handled correctly"""
        test_path = 'test//path//file.txt'
        patch = textwrap.dedent('\n@@ -0,0 +1,1 @@\n+test content')
        full_path = os.path.join(self.test_file + '_dir', test_path)
        try:
            result = patch_edit(full_path, patch)
            self.assertIn('Successfully', result)
            normalized_path = os.path.normpath(full_path)
            self.assertTrue(os.path.exists(normalized_path))
            with open(normalized_path, 'r') as f:
                content = f.read()
            self.assertEqual(content.strip(), 'test content')
        finally:
            if os.path.exists(os.path.dirname(full_path)):
                import shutil
                shutil.rmtree(os.path.dirname(os.path.dirname(full_path)))

    def test_path_normalization(self):
        """Test that both forward and backward slashes work in paths"""
        test_paths = ['test/path/file.txt', 'test\\path\\file.txt', 'test/path\\mixed/slashes\\file.txt']
        patch = textwrap.dedent('\n@@ -0,0 +1,1 @@\n+test content')
        for path in test_paths:
            full_path = os.path.join(self.test_file + '_dir', path)
            try:
                result = patch_edit(full_path, patch)
                self.assertIn('Successfully', result)
                self.assertTrue(os.path.exists(os.path.normpath(full_path)))
                with open(os.path.normpath(full_path), 'r') as f:
                    content = f.read()
                self.assertEqual(content.strip(), 'test content')
            finally:
                if os.path.exists(os.path.dirname(full_path)):
                    import shutil
                    shutil.rmtree(os.path.dirname(os.path.dirname(full_path)))

    def test_class_indentation_preservation(self):
        """Test that class and method indentation is properly preserved when applying patches"""
        with open(self.test_file, 'w') as f:
            f.write('class MyClass:\n    def method1(self):\n        return "original"\n\n    def method2(self):\n        return "test"\n')
        patch = textwrap.dedent('\n@@ -1,6 +1,6 @@\nclass MyClass:\n    def method1(self):\n-        return "original"\n+        return "modified"\n\n    def method2(self):\n        return "test"')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'class MyClass:\n    def method1(self):\n        return "modified"\n\n    def method2(self):\n        return "test"\n'
        self.assertEqual(content, expected, f'Indentation was not preserved.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')

    def test_relative_indentation_preservation(self):
        """Test that relative indentation between lines is preserved while adjusting to target indent"""
        with open(self.test_file, 'w') as f:
            f.write('line 1\nbase indent\nline 3\n')
        patch = textwrap.dedent('\n@@ -2,1 +2,4 @@\nbase indent\n+    indented:\n+        double indented\n+            triple indented')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'line 1\nbase indent\n    indented:\n        double indented\n            triple indented\nline 3\n'
        self.assertEqual(content, expected, f'Relative indentation not preserved.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')
        with open(self.test_file, 'w') as f:
            f.write('line 1\n    indented line\nline 3\n')
        patch = textwrap.dedent('\n@@ -2,1 +2,4 @@\n    indented line\n+    same level\n+        more indented\n+            most indented')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'line 1\n    indented line\n    same level\n        more indented\n            most indented\nline 3\n'
        self.assertEqual(content, expected, f'Relative indentation not preserved when adding to indented line.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')

    def test_replacement_context_matching(self):
        """Test that replacement works when line numbers are wrong but context matches.
    This tests the fallback to context matching when exact line matching fails."""
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline 2\nline 3\nline 4\nline 5\n')
        patch = '@@ -6,3 +6,3 @@\nline 2\n-line 3\n+modified line 3\nline 4'
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertIn('(different from specified line', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nmodified line 3\nline 4\nline 5\n')

    def test_single_line_no_context(self):
        """Test the most basic case: single line replacement with no context lines.
    This is the simplest possible case and should work based purely on line number."""
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline 2\nline 3\nline 4\nline 5\n')
        patch = '@@ -2,1 +2,1 @@\n-line 2\n+modified line 2'
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nmodified line 2\nline 3\nline 4\nline 5\n', 'Failed to handle simple replacement without context lines')

    def test_line_number_accuracy(self):
        """Test exact line number handling without context lines.
    This explicitly tests for off-by-one errors in line targeting."""
        initial = 'line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n'
        failures = []
        test_cases = [(1, '@@ -1,1 +1,1 @@\n-line 1\n+modified line 1', 'modified line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n', 'Replace first line'), (2, '@@ -2,1 +2,1 @@\n-line 2\n+modified line 2', 'line 1\nmodified line 2\nline 3\nline 4\nline 5\nline 6\n', 'Replace line 2'), (3, '@@ -3,1 +3,1 @@\n-line 3\n+modified line 3', 'line 1\nline 2\nmodified line 3\nline 4\nline 5\nline 6\n', 'Replace line 3'), (4, '@@ -4,1 +4,1 @@\n-line 4\n+modified line 4', 'line 1\nline 2\nline 3\nmodified line 4\nline 5\nline 6\n', 'Replace line 4'), (5, '@@ -5,1 +5,1 @@\n-line 5\n+modified line 5', 'line 1\nline 2\nline 3\nline 4\nmodified line 5\nline 6\n', 'Replace line 5'), (6, '@@ -6,1 +6,1 @@\n-line 6\n+modified line 6', 'line 1\nline 2\nline 3\nline 4\nline 5\nmodified line 6\n', 'Replace last line')]
        for line_num, patch, expected, desc in test_cases:
            try:
                with open(self.test_file, 'w') as f:
                    f.write(initial)
                result = patch_edit(self.test_file, patch)
                with open(self.test_file, 'r') as f:
                    content = f.read()
                print(f'\nTest case: {desc} (line {line_num})')
                print('Got:')
                print(content)
                print('Expected:')
                print(expected)
                if content != expected:
                    failures.append(f'Line {line_num}: Got content:\n{content}\nExpected:\n{expected}')
            except Exception as e:
                failures.append(f'Line {line_num}: Exception: {str(e)}')
        if failures:
            self.fail('Failures:\n' + '\n\n'.join(failures))

    def test_insert_method_after_method_in_class(self):
        """Insert a new method after an existing method in a class."""
        orig_code = (
            "class MyClass:\n"
            "    def foo(self):\n"
            "        pass\n"
        )
        patch = textwrap.dedent("""\
            @@ -2,6 +2,10 @@
                def foo(self):
                    pass
            +
            +    def bar(self):
            +        print("bar!")
        """)
        expected = (
            "class MyClass:\n"
            "    def foo(self):\n"
            "        pass\n"
            "\n"
            "    def bar(self):\n"
            "        print(\"bar!\")\n"
        )
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.py') as tf:
            tf.write(orig_code)
            tf.flush()
            result = patch_edit(tf.name, patch)
            self.assertIn('Successfully', result)
            with open(tf.name, 'r') as f:
                out = f.read()
            self.assertEqual(out, expected)
        os.unlink(tf.name)

    def test_insert_function_after_class(self):
        """Insert a new function after the class body."""
        orig_code = (
            "class MyClass:\n"
            "    pass\n"
        )
        patch = textwrap.dedent("""\
            @@ -3,6 +3,9 @@
            +
            +def util():
            +    print("util")
        """)
        expected = (
            "class MyClass:\n"
            "    pass\n"
            "\n"
            "def util():\n"
            "    print(\"util\")\n"
        )
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.py') as tf:
            tf.write(orig_code)
            tf.flush()
            result = patch_edit(tf.name, patch)
            self.assertIn('Successfully', result)
            with open(tf.name, 'r') as f:
                out = f.read()
            self.assertEqual(out, expected)
        os.unlink(tf.name)

    def test_insert_method_in_class_with_inexact_whitespace(self):
        """Insert a method after another method in a class, but with whitespace difference requiring inexact match."""
        orig_code = (
            "class MyClass:\n"
            "    def foo(self):\n"
            "      pass\n"
        )
        # Patch context lines use different indentation (4 vs 6 spaces)
        patch = textwrap.dedent("""\
            @@ -2,6 +2,10 @@
                def foo(self):
            -      pass
            +            pass
            +
            +    def bar(self):
            +        print("bar!")
        """)
        expected = (
            "class MyClass:\n"
            "    def foo(self):\n"
            "        pass\n"
            "\n"
            "    def bar(self):\n"
            "        print(\"bar!\")\n"
        )
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.py') as tf:
            tf.write(orig_code)
            tf.flush()
            result = patch_edit(tf.name, patch)
            self.assertIn('Successfully', result)
            self.assertIn('ignore whitespace', result)
            with open(tf.name, 'r') as f:
                out = f.read()
            self.assertEqual(out, expected)
        os.unlink(tf.name)

class TestGitPatchHunkParsing(unittest.TestCase):

    def setUp(self):
        self.test_file = 'test_hunk_parse.txt'
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline 2\nline 3\nline 4\nline 5\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_empty_lines_in_hunk(self):
        """Test hunks with empty lines in various positions"""
        patch = textwrap.dedent('\n@@ -2,4 +2,4 @@\nline 2\n\n-line 3\n+modified line 3\nline 4')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)

    def test_missing_context_lines(self):
        """Test hunks with no context lines"""
        patch = textwrap.dedent('\n@@ -2,1 +2,1 @@\n-line 2\n+modified line 2')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nmodified line 2\nline 3\nline 4\nline 5\n')

    def test_hunk_with_no_changes(self):
        """Test hunks that only contain context lines"""
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\nline 3')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Error: No additons or removals found', result)

    def test_multiple_hunks_with_empty_lines_between(self):
        """Test multiple hunks separated by varying numbers of empty lines"""
        patch = textwrap.dedent('\n@@ -1,2 +1,2 @@\nline 1\n-line 2\n+modified line 2\n\n@@ -4,2 +4,2 @@\nline 4\n-line 5\n+modified line 5')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nmodified line 2\nline 3\nline 4\nmodified line 5\n')

    def test_hunk_with_no_newline_markers(self):
        """Test hunks with '\\ No newline at end of file' markers"""
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n\\ No newline at end of file\n+modified line 3\n\\ No newline at end of file')
        result = patch_edit(self.test_file, patch)
        self.assertIn('Successfully', result)

    def test_patch_line_marker_spacing(self):
        """Test handling of spaces after patch line markers (space, +, -)"""
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n    line 2\n        line 3\n    line 4\n')
        patches = [textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3'), textwrap.dedent('\n@@ -2,2 +2,2 @@\n line 2\n-line 3\n+modified line 3'), textwrap.dedent('\n@@ -2,2 +2,2 @@\n  line 2\n-  line 3\n+  modified line 3')]
        result1 = patch_edit(self.test_file, patches[0])
        print('\nNo spaces result:', result1)
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n    line 2\n        line 3\n    line 4\n')
        result2 = patch_edit(self.test_file, patches[1])
        print('\nCorrect spaces result:', result2)
        with open(self.test_file, 'r') as f:
            content = f.read()
        print('\nCorrect spaces content:', repr(content))
        self.assertIn('Successfully', result2)
        self.assertEqual(content, '    line 1\n    line 2\n        modified line 3\n    line 4\n')

    def test_patch_context_line_recognition(self):
        """Test that context lines are properly recognized with correct spacing"""
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n    line 2\n        line 3\n    line 4\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3')
        result = patch_edit(self.test_file, patch)
        print('\nContext recognition result:', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        print('\nFinal content:', repr(content))
        self.assertIn('Successfully', result)
        self.assertEqual(content, '    line 1\n    line 2\n        modified line 3\n    line 4\n')