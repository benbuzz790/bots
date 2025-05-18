import os
import unittest
from bots.tools.code_tools import apply_git_patch
import textwrap

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
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertNotIn('ignoring whitespace', result, 'Expected exact match but got whitespace-ignored match')
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nnew line\nline 3\nline 4\nline 5\n')

    def test_simple_deletion(self):
        patch = textwrap.dedent('\n@@ -2,3 +2,2 @@\nline 2\n-line 3\nline 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertNotIn('ignoring whitespace', result, 'Expected exact match but got whitespace-ignored match')
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nline 4\nline 5\n')

    def test_replacement(self):
        patch = textwrap.dedent('\n@@ -2,3 +2,3 @@\nline 2\n-line 3\n+modified line 3\nline 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nmodified line 3\nline 4\nline 5\n')

    def test_multiple_hunks(self):
        patch = textwrap.dedent('\n@@ -1,2 +1,3 @@\nline 1\n+inserted at start\nline 2\n@@ -4,2 +5,3 @@\nline 4\n+inserted at end\nline 5')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\ninserted at start\nline 2\nline 3\nline 4\ninserted at end\nline 5\n')

    def test_invalid_patch_format(self):
        patch = 'not a valid patch format'
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('No valid patch hunks', result)

    def test_context_mismatch(self):
        patch = textwrap.dedent('\n@@ -2,3 +2,3 @@\nwrong context\n-line 3\n+modified line 3\nline 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('Could not find matching content', result)

    def test_empty_patch(self):
        patch = ''
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('patch_content is empty', result)

    def test_new_file(self):
        new_file = 'new_test_file.txt'
        if os.path.exists(new_file):
            os.remove(new_file)
        patch = textwrap.dedent('\n@@ -0,0 +1,3 @@\n+first line\n+second line\n+third line')
        try:
            result = apply_git_patch(new_file, patch)
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
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertIn('Note: Applied hunk at line', result)

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
        result = apply_git_patch(self.test_file, patch)
        print('\nResult:', result)
        with open(self.test_file, 'r') as f:
            print('\nFinal content:')
            print(repr(f.read()))
        self.assertIn('Successfully', result)
        self.assertIn('ignoring whitespace', result)

    def test_similar_but_not_exact_match(self):
        """Test that similar but not exact matches are reported"""
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline two\nline 3\nline 4\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('Could not find matching content', result)

    def test_no_match_found(self):
        """Test that appropriate error is returned when no match is found"""
        with open(self.test_file, 'w') as f:
            f.write('completely\ndifferent\ncontent\n')
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n         line 2\n        -line 3\n        +modified line 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertTrue('Could not find matching content anywhere in file' in result or 'Context mismatch' in result, f'Expected error message about missing content, got: {result}')

    def test_whitespace_only_difference(self):
        """Test matching when only whitespace differs"""
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n        line 2\n    line 3\n')
        patch = textwrap.dedent('\n@@ -1,3 +1,3 @@\nline 1\n-line 2\n+modified line 2\nline 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertIn('ignoring whitespace', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, '    line 1\n        modified line 2\n    line 3\n')

    def test_indentation_preservation_simple(self):
        """Test that existing indentation is preserved on modified lines"""
        with open(self.test_file, 'w') as f:
            f.write('line 1\n    indented line\n        double indented\n')
        patch = textwrap.dedent('\n@@ -2,1 +2,1 @@\nindented line\n-double indented\n+modified line')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\n    indented line\n        modified line\n')

    def test_find_block_with_context(self):
        """Test finding a block with surrounding context"""
        with open(self.test_file, 'w') as f:
            f.write('header\n    block start\n    target line\n    block end\nfooter\n')
        patch = textwrap.dedent('\n@@ -2,3 +2,3 @@\nblock start\n-target line\n+modified line\nblock end')
        result = apply_git_patch(self.test_file, patch)
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
        result = apply_git_patch(self.test_file, patch)
        print('\nResult:', result)
        with open(self.test_file, 'r') as f:
            print('\nFinal content:')
            print(repr(f.read()))

    def test_multiple_possible_matches(self):
        """Test behavior when multiple potential matches exist"""
        with open(self.test_file, 'w') as f:
            f.write('def test1():\n    line 1\n    line 2\ndef test2():\n    line 1\n    line 2\n')
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 1\n-line 2\n+modified line')
        result = apply_git_patch(self.test_file, patch)
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
            result = apply_git_patch(new_file, patch)
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
            result = apply_git_patch(full_path, patch)
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
                result = apply_git_patch(full_path, patch)
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
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'class MyClass:\n    def method1(self):\n        return "modified"\n\n    def method2(self):\n        return "test"\n'
        self.assertEqual(content, expected, f'Indentation was not preserved.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')

    def test_adding_to_import_only_file(self):
        """Test that adding content to a file with only imports preserves indentation"""
        with open(self.test_file, 'w') as f:
            f.write('import numpy as np\nimport time\nfrom typing import List, Tuple\n')
        patch = '@@ -1,3 +1,54 @@\nimport numpy as np\nimport time\nfrom typing import List, Tuple\n+\n+class GameOfLife:\n+    def __init__(self, size: Tuple[int, int]):\n+        self.size = size\n+        self.grid = np.random.choice([0, 1], size=size, p=[0.85, 0.15])\n+    \n+    def get_neighbors(self, pos: Tuple[int, int]) -> int:\n+        """Count live neighbors for a given cell position."""\n+        row, col = pos\n+        count = 0\n+        for i in [-1, 0, 1]:\n+            for j in [-1, 0, 1]:\n+                if i == 0 and j == 0:\n+                    continue\n+                r = (row + i) % self.size[0]\n+                c = (col + j) % self.size[1]\n+                count += self.grid[r, c]\n+        return count\n+    \n+    def step(self) -> None:\n+        """Advance the game by one generation."""\n+        new_grid = np.copy(self.grid)\n+        for i in range(self.size[0]):\n+            for j in range(self.size[1]):\n+                neighbors = self.get_neighbors((i, j))\n+                if self.grid[i, j] == 1:\n+                    if neighbors < 2 or neighbors > 3:\n+                        new_grid[i, j] = 0\n+                else:\n+                    if neighbors == 3:\n+                        new_grid[i, j] = 1\n+        self.grid = new_grid\n+    \n+    def display(self) -> None:\n+        """Display the current state of the game."""\n+        for row in self.grid:\n+            print(\'\'.join([\'■\' if cell else \'□\' for cell in row]))\n+\n+def main():\n+    # Initialize game with a 20x40 grid\n+    game = GameOfLife((20, 40))\n+    \n+    # Run for 100 generations\n+    for _ in range(100):\n+        print("\\033[2J\\033[H")  # Clear screen\n+        game.display()\n+        game.step()\n+        time.sleep(0.1)\n+\n+if __name__ == "__main__":\n+    main()'
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'import numpy as np\nimport time\nfrom typing import List, Tuple\n\nclass GameOfLife:\n    def __init__(self, size: Tuple[int, int]):\n        self.size = size\n        self.grid = np.random.choice([0, 1], size=size, p=[0.85, 0.15])\n\n    def get_neighbors(self, pos: Tuple[int, int]) -> int:\n        """Count live neighbors for a given cell position."""\n        row, col = pos\n        count = 0\n        for i in [-1, 0, 1]:\n            for j in [-1, 0, 1]:\n                if i == 0 and j == 0:\n                    continue\n                r = (row + i) % self.size[0]\n                c = (col + j) % self.size[1]\n                count += self.grid[r, c]\n        return count\n\n    def step(self) -> None:\n        """Advance the game by one generation."""\n        new_grid = np.copy(self.grid)\n        for i in range(self.size[0]):\n            for j in range(self.size[1]):\n                neighbors = self.get_neighbors((i, j))\n                if self.grid[i, j] == 1:\n                    if neighbors < 2 or neighbors > 3:\n                        new_grid[i, j] = 0\n                else:\n                    if neighbors == 3:\n                        new_grid[i, j] = 1\n        self.grid = new_grid\n\n    def display(self) -> None:\n        """Display the current state of the game."""\n        for row in self.grid:\n            print(\'\'.join([\'■\' if cell else \'□\' for cell in row]))\n\ndef main():\n    # Initialize game with a 20x40 grid\n    game = GameOfLife((20, 40))\n\n    # Run for 100 generations\n    for _ in range(100):\n        print("\\033[2J\\033[H")  # Clear screen\n        game.display()\n        game.step()\n        time.sleep(0.1)\n\nif __name__ == "__main__":\n    main()\n'
        self.assertEqual(content, expected, f'Content or indentation mismatch.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')

    def test_relative_indentation_preservation(self):
        """Test that relative indentation between lines is preserved while adjusting to target indent"""
        with open(self.test_file, 'w') as f:
            f.write('line 1\nbase indent\nline 3\n')
        patch = textwrap.dedent('\n@@ -2,1 +2,4 @@\nbase indent\n+    indented:\n+        double indented\n+            triple indented')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'line 1\nbase indent\n    indented:\n        double indented\n            triple indented\nline 3\n'
        self.assertEqual(content, expected, f'Relative indentation not preserved.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')
        with open(self.test_file, 'w') as f:
            f.write('line 1\n    indented line\nline 3\n')
        patch = textwrap.dedent('\n@@ -2,1 +2,4 @@\n    indented line\n+    same level\n+        more indented\n+            most indented')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        expected = 'line 1\n    indented line\n    same level\n        more indented\n            most indented\nline 3\n'
        self.assertEqual(content, expected, f'Relative indentation not preserved when adding to indented line.\nExpected:\n{repr(expected)}\nGot:\n{repr(content)}')

class TestGitPatchHunkParsing(unittest.TestCase):

    def setUp(self):
        self.test_file = 'test_hunk_parse.txt'
        with open(self.test_file, 'w') as f:
            f.write('line 1\nline 2\nline 3\nline 4\nline 5\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_malformed_hunk_header(self):
        """Test various malformed hunk headers"""
        bad_headers = ['@@ -2,2 +2,2\n line 2\n-line 3\n+modified line 3', '@@ -2 +2 @@\n line 2\n-line 3\n+modified line 3', '@@ -a,2 +2,2 @@\n line 2\n-line 3\n+modified line 3', '@@ -2,2 2,2 @@\n line 2\n-line 3\n+modified line 3', '@@ -2,2 +2,2 @@ extra\n line 2\n-line 3\n+modified line 3']
        for header in bad_headers:
            result = apply_git_patch(self.test_file, header)
            self.assertIn('Error', result, f'Expected error for malformed header: {header}')

    def test_incorrect_line_counts(self):
        """Test hunks where the stated line count doesn't match content"""
        patches = ['@@ -2,2 +2,2 @@\n line 2\n line 3\n line 4\n-line 5\n+modified line', '@@ -2,3 +2,3 @@\n line 2\n-line 3\n+modified line']
        for patch in patches:
            result = apply_git_patch(self.test_file, patch)
            self.assertIn('Error', result, f'Expected error for incorrect line count: {patch}')

    def test_empty_lines_in_hunk(self):
        """Test hunks with empty lines in various positions"""
        patch = textwrap.dedent('\n@@ -2,4 +2,4 @@\nline 2\n\n-line 3\n+modified line 3\nline 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)

    def test_missing_context_lines(self):
        """Test hunks with no context lines"""
        patch = textwrap.dedent('\n@@ -2,1 +2,1 @@\n-line 2\n+modified line 2')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nmodified line 2\nline 3\nline 4\nline 5\n')

    def test_malformed_change_lines(self):
        """Test hunks with malformed change lines"""
        bad_patches = ['@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3', '@@ -2,2 +2,2 @@\n line 2\n*line 3\n#modified line 3', '@@ -2,2 +2,2 @@\n  line 2\n -line 3\n + modified line 3']
        for patch in bad_patches:
            result = apply_git_patch(self.test_file, patch)
            self.assertIn('Error', result, f'Expected error for malformed change lines: {patch}')

    def test_hunk_with_no_changes(self):
        """Test hunks that only contain context lines"""
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\nline 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('No changes were applied', result)

    def test_multiple_hunks_with_empty_lines_between(self):
        """Test multiple hunks separated by varying numbers of empty lines"""
        patch = textwrap.dedent('\n@@ -1,2 +1,2 @@\nline 1\n-line 2\n+modified line 2\n\n@@ -4,2 +4,2 @@\nline 4\n-line 5\n+modified line 5')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nmodified line 2\nline 3\nline 4\nmodified line 5\n')

    def test_hunk_with_no_newline_markers(self):
        """Test hunks with '\\ No newline at end of file' markers"""
        patch = textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n\\ No newline at end of file\n+modified line 3\n\\ No newline at end of file')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)

    def test_patch_line_marker_spacing(self):
        """Test handling of spaces after patch line markers (space, +, -)"""
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n    line 2\n        line 3\n    line 4\n')
        patches = [textwrap.dedent('\n@@ -2,2 +2,2 @@\nline 2\n-line 3\n+modified line 3'), textwrap.dedent('\n@@ -2,2 +2,2 @@\n line 2\n-line 3\n+modified line 3'), textwrap.dedent('\n@@ -2,2 +2,2 @@\n  line 2\n-  line 3\n+  modified line 3')]
        result1 = apply_git_patch(self.test_file, patches[0])
        print('\nNo spaces result:', result1)
        with open(self.test_file, 'w') as f:
            f.write('    line 1\n    line 2\n        line 3\n    line 4\n')
        result2 = apply_git_patch(self.test_file, patches[1])
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
        result = apply_git_patch(self.test_file, patch)
        print('\nContext recognition result:', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        print('\nFinal content:', repr(content))
        self.assertIn('Successfully', result)
        self.assertEqual(content, '    line 1\n    line 2\n        modified line 3\n    line 4\n')