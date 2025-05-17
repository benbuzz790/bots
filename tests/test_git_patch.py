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
        patch = textwrap.dedent('\n        @@ -2,2 +2,3 @@\n         line 2\n        +new line\n         line 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nnew line\nline 3\nline 4\nline 5\n')

    def test_simple_deletion(self):
        patch = textwrap.dedent('\n        @@ -2,3 +2,2 @@\n         line 2\n        -line 3\n         line 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nline 4\nline 5\n')

    def test_replacement(self):
        patch = textwrap.dedent('\n        @@ -2,3 +2,3 @@\n         line 2\n        -line 3\n        +modified line 3\n         line 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\nline 2\nmodified line 3\nline 4\nline 5\n')

    def test_multiple_hunks(self):
        patch = textwrap.dedent('\n        @@ -1,2 +1,3 @@\n         line 1\n        +inserted at start\n         line 2\n        @@ -4,2 +5,3 @@\n         line 4\n        +inserted at end\n         line 5')
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
        patch = textwrap.dedent('\n        @@ -2,3 +2,3 @@\n         wrong context\n        -line 3\n        +modified line 3\n         line 4')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('Context mismatch', result)

    def test_empty_patch(self):
        patch = ''
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('No valid patch hunks', result)

    def test_new_file(self):
        new_file = 'new_test_file.txt'
        if os.path.exists(new_file):
            os.remove(new_file)
        patch = textwrap.dedent('\n        @@ -0,0 +1,3 @@\n        +first line\n        +second line\n        +third line')
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
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n         line 2\n        -line 3\n        +modified line 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        self.assertIn('different from specified line', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'header\nline 1\nline 2\nmodified line 3\nline 4\nline 5\n')

    def test_match_with_different_whitespace(self):
        """Test that content is matched even with different indentation"""
        with open(self.test_file, 'w') as f:
            f.write('def test():\n    line 1\n    line 2\n        line 3\n    line 4\n')
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n        line 2\n        -line 3\n        +modified line 3')
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
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n         line 2\n        -line 3\n        +modified line 3')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Error', result)
        self.assertIn('similar but not exact match', result)
        self.assertIn('Match quality:', result)

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
        patch = textwrap.dedent('\n        @@ -1,3 +1,3 @@\n         line 1\n        -line 2\n        +modified line 2\n         line 3')
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
        patch = textwrap.dedent('\n        @@ -2,1 +2,1 @@\n             indented line\n        -        double indented\n        +        modified line')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'line 1\n    indented line\n        modified line\n')

    def test_find_block_with_context(self):
        """Test finding a block with surrounding context"""
        with open(self.test_file, 'w') as f:
            f.write('header\n    block start\n    target line\n    block end\nfooter\n')
        patch = textwrap.dedent('\n        @@ -2,3 +2,3 @@\n             block start\n        -    target line\n        +    modified line\n             block end')
        result = apply_git_patch(self.test_file, patch)
        self.assertIn('Successfully', result)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'header\n    block start\n    modified line\n    block end\nfooter\n')

    def test_match_with_different_whitespace_debug(self):
        """Debug version to see what's happening with whitespace matching"""
        with open(self.test_file, 'w') as f:
            f.write('def test():\n    line 1\n    line 2\n        line 3\n    line 4\n')
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n        line 2\n        -line 3\n        +modified line 3')
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
        patch = textwrap.dedent('\n        @@ -2,2 +2,2 @@\n             line 1\n        -    line 2\n        +    modified line')
        result = apply_git_patch(self.test_file, patch)
        if 'multiple' in result.lower() or 'ambiguous' in result.lower():
            self.assertTrue(True)
        else:
            with open(self.test_file, 'r') as f:
                content = f.read()
            self.assertTrue(content.startswith('def test1():\n    line 1\n    modified line\n'), f'Expected modification at first match, but got:\n{content}')
