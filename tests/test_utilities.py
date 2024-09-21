import unittest
import time
from unittest.mock import patch, mock_open
from bots.utilities.cache_util import get_cache_key, cache_response, get_cached_response
from bots.utilities.rate_limit_util import RateLimiter
from bots.utilities.config_util import load_config, get_model_config

@unittest.skip("probably deleting these utilities")
class TestCacheUtil(unittest.TestCase):
    def test_get_cache_key(self):
        key1 = get_cache_key("test prompt", "test_model")
        key2 = get_cache_key("test prompt", "test_model")
        self.assertEqual(key1, key2)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_cache_response(self, mock_json_dump, mock_file):
        cache_response("test prompt", "test_model", "test response")
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"prompt": "test", "model": "test", "response": "cached", "timestamp": "2023-01-01T00:00:00"}')
    def test_get_cached_response(self, mock_file, mock_exists):
        response = get_cached_response("test", "test")
        self.assertEqual(response, "cached")

@unittest.skip("")
class TestRateLimitUtil(unittest.TestCase):
    def test_rate_limiter(self):
        @RateLimiter(max_calls=2, period=1)
        def test_func():
            return time.time()

        start_time = time.time()
        test_func()
        test_func()
        test_func()
        end_time = time.time()

        self.assertGreaterEqual(end_time - start_time, 1)

@unittest.skip("")
class TestConfigUtil(unittest.TestCase):
    @patch('configparser.ConfigParser.read')
    def test_load_config(self, mock_read):
        load_config()
        mock_read.assert_called_once()

    @patch('utilities.config_util.load_config')
    def test_get_model_config(self, mock_load_config):
        mock_load_config.return_value = {
            'ANTHROPIC': {'model_engine': 'claude-v1'}
        }
        config = get_model_config('anthropic')
        self.assertEqual(config, {'model_engine': 'claude-v1'})

if __name__ == '__main__':
    unittest.main()
