import unittest
from unittest.mock import Mock, patch
import json
from bots.flows.flows import create_issue_flow
from bots.foundation.base import Bot, ToolHandler
from bots.foundation.base import Engines


class TestCreateIssueFlow(unittest.TestCase):

    def setUp(self):
        from bots import AnthropicBot
        self.bot = AnthropicBot()

    def test_create_issue_flow_missing_repo(self):
        """Test that create_issue_flow raises ValueError when repo is not provided"""
        with self.assertRaises(ValueError) as context:
            create_issue_flow(self.bot)
        self.assertEqual(str(context.exception),
            'kwargs must include repo name')

    def test_create_issue_flow_successful(self):
        """Test actual creation of a GitHub issue through the flow"""
        test_repo = 'benbuzz790/bots'
        test_error = {'error_type': 'TestError', 'message':
            'This is a test error from test_flows.py integration test',
            'traceback':
            """File 'test_flows.py', line 42, in test_function
    raise TestError('Test error')"""
            , 'context': 'Running integration test for create_issue_flow'}
        create_issue_flow(self.bot, repo=test_repo, **test_error)
        tool_names = [tool['name'] for tool in self.bot.tool_handler.tools]
        self.assertIn('create_issue', tool_names)
        self.assertIn('view_dir', tool_names)
        self.assertIn('view', tool_names)
        results = self.bot.tool_handler.get_results()
        create_issue_result = None
        for result in results:
            if 'create_issue' in str(result):
                create_issue_result = result
                break
        self.assertIsNotNone(create_issue_result, 'No issue was created')
        result_content = json.loads(create_issue_result.get('content', '{}'))
        self.assertIn('issue_number', result_content, 'Issue creation failed')
        self.assertIn('url', result_content, 'Issue URL not returned')
        print(f"Created test issue: {result_content['url']}")

    def test_autosave_disabled(self):
        """Test that autosave is disabled during flow execution"""
        test_repo = 'benbuzz790/bots'
        original_autosave = self.bot.autosave
        create_issue_flow(self.bot, repo=test_repo)
        current_autosave = self.bot.autosave
        self.assertFalse(current_autosave)
        self.bot.autosave = original_autosave
