import pytest
import time
from unittest.mock import patch, MagicMock
import json
from bots.dev.decorators import create_issues
from bots.tools.github_tools import list_issues, get_issue, update_issue


def divide(a: int, b: int) ->float:
    """Simple division function that might raise ZeroDivisionError"""
    return a / b


def complex_error():
    """Function that raises a custom error with nested calls"""

    def nested_func():
        raise ValueError('Something went wrong in nested function')
    return nested_func()


def recursive_error(n: int):
    """Function that demonstrates recursive error"""
    if n <= 0:
        raise RuntimeError('Recursion limit reached')
    return recursive_error(n - 1)


@pytest.mark.integration
class TestIssueTrackerIntegration:
    """Integration tests using real GitHub API calls to benbuzz790/test repo"""
    TEST_REPO = 'benbuzz790/test'
    wait_period = 300

    def setup_method(self):
        """Setup method to verify GitHub token is available"""
        import os
        if not (os.environ.get('GITHUB_TOKEN') or os.environ.get(
            'GITHUB_ACCESS_TOKEN')):
            pytest.skip('No GitHub token available for integration tests')

    def test_real_issue_creation(self):
        """Test creating a real issue in the test repository"""

        @create_issues(repo=self.TEST_REPO)
        def failing_function():
            x = {'key': 'value'}
            return x['nonexistent_key']
        
        initial_issues = json.loads(list_issues(self.TEST_REPO))
        initial_count = len(initial_issues)

        with pytest.raises(KeyError):
            failing_function()
        time.sleep(self.wait_period)
        
        new_issues = json.loads(list_issues(self.TEST_REPO))
        assert len(new_issues) > initial_count
        latest_issue = json.loads(get_issue(self.TEST_REPO, new_issues[0]['number']))

        assert 'Error in failing_function' in latest_issue['title']
        assert 'KeyError' in latest_issue['body']
        assert 'nonexistent_key' in latest_issue['body']

    def test_async_real_issue_creation(self):
        """Test creating a real issue asynchronously"""

        @create_issues(repo=self.TEST_REPO)
        def async_failing_function(msg: str):
            raise RuntimeError(msg)
        
        test_message = f'Test error {time.time()}'
        initial_issues = json.loads(list_issues(self.TEST_REPO))
        initial_count = len(initial_issues)

        with pytest.raises(RuntimeError):
            async_failing_function(test_message)
        
        time.sleep(self.wait_period)
        new_issues = json.loads(list_issues(self.TEST_REPO))
        assert len(new_issues) > initial_count
        
        latest_issue = new_issues[0]
        assert 'Error in async_failing_function' in latest_issue['title']
        assert 'RuntimeError' in latest_issue['body']

    def test_multiple_async_issues(self):
        """Test creating multiple async issues in quick succession"""

        @create_issues(repo=self.TEST_REPO)
        def multi_error(id: int):
            raise ValueError(f'Multi error test {id}')
        
        initial_issues = json.loads(list_issues(self.TEST_REPO))
        initial_count = len(initial_issues)
        error_count = 3
        
        for i in range(error_count):
            with pytest.raises(ValueError):
                multi_error(i)
        
        time.sleep(self.wait_period)
        new_issues = json.loads(list_issues(self.TEST_REPO))
        assert len(new_issues) > initial_count

    def teardown_method(self):
        """Clean up by closing issues created during tests"""
        issues = json.loads(list_issues(self.TEST_REPO))
        for issue in issues:
            if any(marker in issue['title'].lower() for marker in ['test',
                'error in', 'failing_function', 'nonexistent_key']):
                update_issue(self.TEST_REPO, issue['number'], kwargs={
                    'state': 'closed', 'body':
                    'Automatically closed by integration test cleanup'})

import unittest
if __name__ == '__main__':
    unittest.main()