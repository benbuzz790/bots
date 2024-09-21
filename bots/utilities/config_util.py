import configparser
import os

def load_config(config_path='config.ini'):
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    config.read(config_path)
    return config

def get_model_config(model_name):
    config = load_config()
    if model_name.upper() not in config:
        raise ValueError(f"Model {model_name} not found in configuration")
    return dict(config[model_name.upper()])
