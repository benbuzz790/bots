import unittest
import tempfile
import os
from bots.tools.code_tools import view, add_lines, change_lines, delete_lines, find_lines, replace_in_lines


class TestCodeTools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_file.txt')
        content = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n'
        with open(self.temp_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def tearDown(self):
        os.remove(self.temp_file)
        os.rmdir(self.temp_dir)

    def test_view(self):
        result = view(self.temp_file)
        expected = '1: Line 1\n2: Line 2\n3: Line 3\n4: Line 4\n5: Line 5'
        self.assertEqual(result, expected)

    def test_add_lines(self):
        new_content = 'New Line A\nNew Line B'
        result = add_lines(self.temp_file, new_content, 3)
        self.assertIn('Successfully added 2 lines starting at line 3', result)
        updated_content = view(self.temp_file)
        expected = """1: Line 1
2: Line 2
3: New Line A
4: New Line B
5: Line 3
6: Line 4
7: Line 5"""
        self.assertEqual(updated_content, expected)

    def test_add_lines_single_line(self):
        new_content = 'Single New Line'
        result = add_lines(self.temp_file, new_content, 3)
        self.assertIn('Successfully added 1 lines starting at line 3', result)
        updated_content = view(self.temp_file)
        expected = (
            '1: Line 1\n2: Line 2\n3: Single New Line\n4: Line 3\n5: Line 4\n6: Line 5'
            )
        self.assertEqual(updated_content, expected)

    def test_add_lines_with_trailing_newline(self):
        new_content = 'New Line A\nNew Line B\n'
        result = add_lines(self.temp_file, new_content, 3)
        self.assertIn('Successfully added 2 lines starting at line 3', result)
        updated_content = view(self.temp_file)
        expected = """1: Line 1
2: Line 2
3: New Line A
4: New Line B
5: Line 3
6: Line 4
7: Line 5"""
        self.assertEqual(updated_content, expected)

    def test_change_lines(self):
        new_content = 'Changed Line 2\nChanged Line 3'
        result = change_lines(self.temp_file, new_content, 2, 3)
        self.assertIn('Successfully changed lines 2 to 3', result)
        updated_content = view(self.temp_file)
        expected = (
            '1: Line 1\n2: Changed Line 2\n3: Changed Line 3\n4: Line 4\n5: Line 5'
            )
        self.assertEqual(updated_content, expected)

    def test_change_lines_with_trailing_newline(self):
        new_content = 'Changed Line 2\nChanged Line 3\n'
        result = change_lines(self.temp_file, new_content, 2, 3)
        self.assertIn('Successfully changed lines 2 to 3', result)
        updated_content = view(self.temp_file)
        expected = (
            '1: Line 1\n2: Changed Line 2\n3: Changed Line 3\n4: Line 4\n5: Line 5'
            )
        self.assertEqual(updated_content, expected)

    def test_change_lines_single_line(self):
        new_content = 'Single Changed Line'
        result = change_lines(self.temp_file, new_content, 2, 2)
        self.assertIn('Successfully changed lines 2 to 2', result)
        updated_content = view(self.temp_file)
        expected = (
            '1: Line 1\n2: Single Changed Line\n3: Line 3\n4: Line 4\n5: Line 5'
            )
        self.assertEqual(updated_content, expected)

    def test_delete_lines(self):
        result = delete_lines(self.temp_file, 2, 4)
        self.assertIn('Successfully deleted lines 2 to 4', result)
        updated_content = view(self.temp_file)
        expected = '1: Line 1\n2: Line 5'
        self.assertEqual(updated_content, expected)

    def test_find_lines(self):
        result = find_lines(self.temp_file, 'Line')
        self.assertIn('Found 5 matches', result)
        self.assertIn('Line 1: Line 1', result)
        self.assertIn('Line 5: Line 5', result)

    def test_replace_in_lines(self):
        result = replace_in_lines(self.temp_file, 'Line', 'NewLine', 2, 4)
        self.assertIn(
            "Successfully replaced 3 occurrences of 'Line' with 'NewLine'",
            result)
        updated_content = view(self.temp_file)
        expected = (
            '1: Line 1\n2: NewLine 2\n3: NewLine 3\n4: NewLine 4\n5: Line 5')
        self.assertEqual(updated_content, expected)

    def test_invalid_line_ranges(self):
        result = change_lines(self.temp_file, 'Invalid', 10, 11)
        self.assertIn('Error: Invalid line range', result)
        result = delete_lines(self.temp_file, 10, 11)
        self.assertIn('Error: Invalid line range', result)
        result = replace_in_lines(self.temp_file, 'old', 'new', 10, 11)
        self.assertIn('Error: Invalid line range', result)

    def test_empty_string_input(self):
        result = add_lines(self.temp_file, '', 3)
        self.assertIn('Successfully added 0 lines', result)
        result = change_lines(self.temp_file, '', 2, 3)
        self.assertIn('Successfully changed lines 2 to 3', result)
        updated_content = view(self.temp_file)
        expected = '1: Line 1\n2: Line 4\n3: Line 5'
        self.assertEqual(updated_content, expected)

    def test_utf8_content(self):
        utf8_content = 'Hello 世界\nTest 🌍\nПривет мир\n€ñçødîñg\n'
        utf8_file = os.path.join(self.temp_dir, 'utf8_test.txt')
        with open(utf8_file, 'w', encoding='utf-8') as f:
            f.write(utf8_content)
        result = view(utf8_file)
        expected = '1: Hello 世界\n2: Test 🌍\n3: Привет мир\n4: €ñçødîñg'
        self.assertEqual(result, expected)
        new_utf8_content = '新しい行\n🎈'
        result = add_lines(utf8_file, new_utf8_content, 2)
        self.assertIn('Successfully added 2 lines', result)
        result = find_lines(utf8_file, '世界')
        self.assertIn('Line 1: Hello 世界', result)
        result = replace_in_lines(utf8_file, 'мир', '世界', 1, 6)
        self.assertIn('Successfully replaced', result)
        os.remove(utf8_file)


if __name__ == '__main__':
    unittest.main()
