import pytest
import sys
import os
from unittest.mock import patch, MagicMock, call
from io import StringIO
from cli2 import DynamicParameterCollector, DynamicFunctionalPromptHandler
import bots.flows.functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
"""
Comprehensive test suite for cli2.py dynamic parameter collection system.
Tests parameter collection with mocked user input and functional prompt execution.
"""
# Add the parent directory to the path so we can import cli2
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)