import os
import json
import logging
from typing import Dict, Any, Optional
import unittest
from unittest.mock import patch, mock_open, MagicMock

class ResourceManager:
    _instance = None
    _resource_dir = ""
    _image_cache = {}
    _config_cache = None
    _logger = None

    @classmethod
    def initialize(cls, resource_dir: str) -> None:
        cls._resource_dir = resource_dir
        cls._image_cache = {}
        cls._config_cache = None
        cls._logger = get_logger()

    @classmethod
    def get_image(cls, image_name: str) -> Any:
        if image_name not in cls._image_cache:
            image_path = cls.get_resource_path(f"images/{image_name}")
            cls._image_cache[image_name] = cls.load_image(image_path)
        return cls._image_cache[image_name]

    @classmethod
    def load_image(cls, image_path: str) -> Any:
        # Placeholder for image loading logic
        return "Loaded image"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        if cls._config_cache is None:
            config_path = cls.get_resource_path("config/settings.json")
            cls._config_cache = load_config(config_path)
            if not check_config_version(cls._config_cache):
                raise ResourceError("Incompatible config version")
        return cls._config_cache

    @classmethod
    def reload_resources(cls) -> None:
        cls._image_cache.clear()
        cls._config_cache = None
        cls._logger.info("Resources reloaded")

    @classmethod
    def cleanup(cls) -> None:
        cls._image_cache.clear()
        cls._config_cache = None
        cls._logger.info("Resources cleaned up")

    @classmethod
    def get_resource_path(cls, relative_path: str) -> str:
        return os.path.join(cls._resource_dir, *relative_path.split('/'))

    @classmethod
    def resize_image(cls, image_name: str, width: int, height: int) -> Any:
        image = cls.get_image(image_name)
        # Placeholder for image resizing logic
        return image

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def check_config_version(config: Dict[str, Any]) -> bool:
    return config.get('version', 0) == 1  # Assuming version 1 is current

def get_logger() -> logging.Logger:
    logger = logging.getLogger('ResourceManager')
    logger.setLevel(logging.INFO)
    return logger

class ResourceError(Exception):
    pass

class TestResourceManager(unittest.TestCase):
    def setUp(self):
        ResourceManager.initialize("test_resources")
        ResourceManager._config_cache = None  # Reset config cache before each test
        ResourceManager._image_cache = {}  # Reset image cache before each test

    @patch.object(ResourceManager, 'load_image')
    def test_get_image(self, mock_load_image):
        mock_load_image.return_value = "Mocked Image"
        image = ResourceManager.get_image("test.png")
        self.assertEqual(image, "Mocked Image")
        mock_load_image.assert_called_once_with(os.path.join("test_resources", "images", "test.png"))

    @patch('builtins.open', new_callable=mock_open, read_data='{"version": 1, "setting": "value"}')
    @patch('json.load')
    def test_get_config(self, mock_json_load, mock_file):
        mock_config = {"version": 1, "setting": "value"}
        mock_json_load.return_value = mock_config
        config = ResourceManager.get_config()
        self.assertEqual(config, mock_config)
        expected_path = os.path.join("test_resources", "config", "settings.json")
        mock_file.assert_called_once_with(expected_path, 'r')
        mock_json_load.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"version": 0, "setting": "value"}')
    @patch('json.load')
    def test_incompatible_config_version(self, mock_json_load, mock_file):
        mock_config = {"version": 0, "setting": "value"}
        mock_json_load.return_value = mock_config
        with self.assertRaises(ResourceError):
            ResourceManager.get_config()
        expected_path = os.path.join("test_resources", "config", "settings.json")
        mock_file.assert_called_once_with(expected_path, 'r')
        mock_json_load.assert_called_once()

    def test_get_resource_path(self):
        path = ResourceManager.get_resource_path("test.png")
        self.assertEqual(path, os.path.join("test_resources", "test.png"))

    def test_reload_resources(self):
        ResourceManager._image_cache = {"test": "image"}
        ResourceManager._config_cache = {"test": "config"}
        ResourceManager.reload_resources()
        self.assertEqual(ResourceManager._image_cache, {})
        self.assertIsNone(ResourceManager._config_cache)

    def test_cleanup(self):
        ResourceManager._image_cache = {"test": "image"}
        ResourceManager._config_cache = {"test": "config"}
        ResourceManager.cleanup()
        self.assertEqual(ResourceManager._image_cache, {})
        self.assertIsNone(ResourceManager._config_cache)

def run_tests():
    unittest.main(argv=[''], exit=False)

if __name__ == "__main__":
    run_tests()