import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from bs4 import BeautifulSoup
import logging

try:
    import unidecode
except ImportError:
    unidecode = None

class TerminalBrowser:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.current_page = None
        self.history = []
        self.forward_stack = []
        self.bookmarks = {}
        self.current_page = None
        self.history = []
        self.forward_stack = []
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def fetch_page(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.current_page = response.text
            self.history.append(url)
            self.forward_stack.clear()
            return self.parse_page(response.text)
        except requests.RequestException as e:
            self.logger.error(f"Error fetching page: {e}")
            return f"Error fetching page: {e}"

    def parse_page(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator='\n', strip=True)
            if unidecode:
                return unidecode.unidecode(text)
            return text
        except Exception as e:
            self.logger.error(f"Error parsing page: {e}")
            return f"Error parsing page: {e}"

    def go_back(self):
        if len(self.history) > 1:
            current_url = self.history.pop()
            self.forward_stack.append(current_url)
            return self.fetch_page(self.history[-1])
        return "No previous page in history."

    def go_forward(self):
        if self.forward_stack:
            url = self.forward_stack.pop()
            return self.fetch_page(url)
        return "No forward page available."

    def current_url(self):
        return self.history[-1] if self.history else None

    
    def render_page(self, max_width=80, max_lines=25):
        if not self.current_page:
            return "No page loaded"
        
        soup = BeautifulSoup(self.current_page, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No title"
        
        # Extract main content
        content = soup.get_text(separator='\n', strip=True)
        
        # Truncate content
        lines = content.split('\n')[:max_lines]
        truncated_content = '\n'.join(line[:max_width] for line in lines)
        
        # Encode and decode to handle Unicode characters
        result = f"Title: {title}\n\n{truncated_content}"
        return result.encode('ascii', errors='ignore').decode('ascii')
    
        if not self.current_page:
            return "No page loaded"
        
        soup = BeautifulSoup(self.current_page, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No title"
        
        # Extract main content
        content = soup.get_text(separator='\n', strip=True)
        
        # Truncate content
        lines = content.split('\n')[:max_lines]
        truncated_content = '\n'.join(line[:max_width] for line in lines)
        
        return f"Title: {title}\n\n{truncated_content}"

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.current_page = None
        self.history = []
        self.forward_stack = []
        self.bookmarks = {}
        # ... (existing code) ...
        self.bookmarks = {}

    def add_bookmark(self, name):
        if self.current_url():
            self.bookmarks[name] = self.current_url()
            return f"Bookmark '{name}' added for {self.current_url()}"
        return "No page loaded to bookmark"

    def go_to_bookmark(self, name):
        if name in self.bookmarks:
            return self.fetch_page(self.bookmarks[name])
        return f"No bookmark named '{name}'"

    def list_bookmarks(self):
        return '\n'.join(f"{name}: {url}" for name, url in self.bookmarks.items())
