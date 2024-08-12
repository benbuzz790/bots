import os
import json
from typing import Dict, Any

class FileHandler:
    @staticmethod
    def read_json_file(file_path: str) -> Dict[str, Any]:
        """
        Read a JSON file and return its contents as a dictionary.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                return data
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON format in file: {file_path}")

    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any]) -> None:
        """
        Write a dictionary to a JSON file.
        """
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        Get the file extension from a file path.
        """
        return os.path.splitext(file_path)[1]

    @staticmethod
    def is_valid_bot_file(file_path: str) -> bool:
        """
        Check if the given file is a valid bot file.
        """
        if FileHandler.get_file_extension(file_path) != '.bot':
            return False

        try:
            data = FileHandler.read_json_file(file_path)
            required_keys = ['name', 'model_engine', 'conversation']
            return all(key in data for key in required_keys)
        except (FileNotFoundError, ValueError):
            return False