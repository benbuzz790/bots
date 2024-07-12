
import unittest
from unittest.mock import patch, MagicMock
import requests
from terminal_browser import TerminalBrowser

class TestTerminalBrowser(unittest.TestCase):
    def setUp(self):
        self.browser = TerminalBrowser()

    def test_initialization(self):
        self.assertIsNone(self.browser.current_page)
        self.assertEqual(self.browser.history, [])
        self.assertEqual(self.browser.forward_stack, [])

    @patch('requests.get')
    def test_fetch_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test Page</body></html>"
        mock_get.return_value = mock_response
        
        result = self.browser.fetch_page("https://example.com")
        
        self.assertEqual(result, "Test Page")
        self.assertEqual(self.browser.history, ["https://example.com"])
        self.assertEqual(self.browser.forward_stack, [])

    @patch('requests.get')
    def test_fetch_page_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Error")
        
        result = self.browser.fetch_page("https://example.com")
        
        self.assertTrue(result.startswith("Error fetching page"))
        self.assertEqual(self.browser.history, [])
        self.assertEqual(self.browser.forward_stack, [])

    def test_parse_page_success(self):
        html = "<html><body><h1>Test</h1><script>alert('test');</script><p>Content</p></body></html>"
        result = self.browser.parse_page(html)
        self.assertEqual(result, "Test\nContent")

    def test_parse_page_error(self):
        result = self.browser.parse_page("Invalid HTML")
        self.assertEqual(result, "Invalid HTML")

    @patch('terminal_browser.TerminalBrowser.fetch_page')
    def test_go_back(self, mock_fetch):
        self.browser.history = ["https://example.com", "https://test.com"]
        mock_fetch.return_value = "Previous Page"
        
        result = self.browser.go_back()
        
        self.assertEqual(result, "Previous Page")
        self.assertEqual(self.browser.history, ["https://example.com"])
        self.assertEqual(self.browser.forward_stack, ["https://test.com"])

    def test_go_back_empty_history(self):
        result = self.browser.go_back()
        self.assertEqual(result, "No previous page in history.")

    @patch('terminal_browser.TerminalBrowser.fetch_page')
    def test_go_forward(self, mock_fetch):
        self.browser.history = ["https://example.com"]
        self.browser.forward_stack = ["https://test.com"]
        mock_fetch.return_value = "Next Page"
        
        result = self.browser.go_forward()
        
        self.assertEqual(result, "Next Page")
        self.assertEqual(self.browser.history, ["https://example.com"])
        self.assertEqual(self.browser.forward_stack, [])
        mock_fetch.assert_called_with("https://test.com")

    def test_go_forward_empty_stack(self):
        result = self.browser.go_forward()
        self.assertEqual(result, "No forward page available.")

    def test_current_url(self):
        self.assertIsNone(self.browser.current_url())
        self.browser.history = ["https://example.com"]
        self.assertEqual(self.browser.current_url(), "https://example.com")

if __name__ == '__main__':
    unittest.main()

    def test_render_page(self):
        self.browser.current_page = "<html><head><title>Test Page</title></head><body><h1>Header</h1><p>Content</p></body></html>"
        rendered = self.browser.render_page(max_width=20, max_lines=3)
        expected = "Title: Test Page\n\nHeader\nContent"
        self.assertEqual(rendered, expected)

    def test_render_page_no_page_loaded(self):
        self.browser.current_page = None
        rendered = self.browser.render_page()
        self.assertEqual(rendered, "No page loaded")

    def test_add_bookmark(self):
        self.browser.history = ["https://example.com"]
        result = self.browser.add_bookmark("Example")
        self.assertEqual(result, "Bookmark 'Example' added for https://example.com")
        self.assertEqual(self.browser.bookmarks["Example"], "https://example.com")

    def test_add_bookmark_no_page(self):
        result = self.browser.add_bookmark("Test")
        self.assertEqual(result, "No page loaded to bookmark")

    @patch('terminal_browser.TerminalBrowser.fetch_page')
    def test_go_to_bookmark(self, mock_fetch):
        self.browser.bookmarks["Test"] = "https://test.com"
        mock_fetch.return_value = "Test Page"
        result = self.browser.go_to_bookmark("Test")
        self.assertEqual(result, "Test Page")
        mock_fetch.assert_called_with("https://test.com")

    def test_go_to_nonexistent_bookmark(self):
        result = self.browser.go_to_bookmark("Nonexistent")
        self.assertEqual(result, "No bookmark named 'Nonexistent'")

    def test_list_bookmarks(self):
        self.browser.bookmarks = {"Example": "https://example.com", "Test": "https://test.com"}
        result = self.browser.list_bookmarks()
        expected = "Example: https://example.com\nTest: https://test.com"
        self.assertEqual(result, expected)
