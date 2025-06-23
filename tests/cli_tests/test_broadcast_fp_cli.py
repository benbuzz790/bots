from unittest.mock import Mock, patch

from bots.dev.cli import CLI, DynamicFunctionalPromptHandler, DynamicParameterCollector
from bots.flows import functional_prompts as fp
from bots.foundation.base import ConversationNode

"""Tests for broadcast_fp functionality in CLI."""


def test_collect_functional_prompt():
    """Test collecting functional prompt parameter."""
    collector = DynamicParameterCollector()
    with patch("builtins.input", return_value="1"):
        result = collector._collect_functional_prompt("functional_prompt", None)
        assert result == fp.single_prompt


def test_collect_functional_prompt_invalid_choice():
    """Test collecting functional prompt with invalid choice."""
    collector = DynamicParameterCollector()
    with patch("builtins.input", return_value="invalid"):
        result = collector._collect_functional_prompt("functional_prompt", None)
        assert result == fp.single_prompt


def test_collect_skip_labels():
    """Test collecting skip labels."""
    collector = DynamicParameterCollector()
    with patch("builtins.input", return_value="draft, test, incomplete"):
        result = collector._collect_skip_labels("skip", None)
        assert result == ["draft", "test", "incomplete"]


def test_collect_skip_labels_empty():
    """Test collecting empty skip labels."""
    collector = DynamicParameterCollector()
    with patch("builtins.input", return_value=""):
        result = collector._collect_skip_labels("skip", None)
        assert result == []


def test_discover_fp_functions_includes_broadcast_fp():
    """Test that broadcast_fp is discovered."""
    handler = DynamicFunctionalPromptHandler()
    functions = handler._discover_fp_functions()
    assert "broadcast_fp" in functions
    assert functions["broadcast_fp"] == fp.broadcast_fp


def test_discover_fp_functions_excludes_descoped():
    """Test that descoped functions are excluded."""
    handler = DynamicFunctionalPromptHandler()
    functions = handler._discover_fp_functions()
    assert "prompt_for" not in functions
    assert "par_dispatch" not in functions


@patch("bots.dev.cli.AnthropicBot")
def test_fp_command_includes_broadcast_fp(mock_bot_class):
    """Test that /fp command includes broadcast_fp option."""
    mock_bot = Mock()
    mock_bot_class.return_value = mock_bot
    cli = CLI()
    # Check that broadcast_fp is in the discovered functions
    assert "broadcast_fp" in cli.fp.fp_functions


def test_parameter_handlers_include_functional_prompt():
    """Test that parameter handlers include functional_prompt."""
    collector = DynamicParameterCollector()
    assert "functional_prompt" in collector.param_handlers
    assert collector.param_handlers["functional_prompt"] == collector._collect_functional_prompt


@patch("builtins.input")
@patch("builtins.print")
def test_broadcast_fp_new_system_all_leaves(mock_print, mock_input):
    """Test broadcast_fp with new leaf selection system - select all leaves."""
    # Setup mock bot and context
    mock_bot = Mock()
    mock_context = Mock()
    mock_conversation_handler = Mock()
    # Create mock leaves
    leaf1 = Mock(spec=ConversationNode)
    leaf1.content = "First leaf content"
    leaf1.labels = []
    leaf2 = Mock(spec=ConversationNode)
    leaf2.content = "Second leaf content"
    leaf2.labels = ["test"]
    leaves = [leaf1, leaf2]
    # Setup mock methods
    mock_conversation_handler._find_leaves.return_value = leaves
    mock_conversation_handler._get_leaf_preview.side_effect = lambda leaf: leaf.content[:50]
    mock_conversation_handler._calculate_depth.return_value = 1
    mock_context.conversation = mock_conversation_handler
    # Setup input sequence: select all leaves, choose single_prompt,
    # provide prompt
    mock_input.side_effect = ["all", "1", "Test prompt"]
    # Setup functional prompt execution - mock the actual fp.broadcast_fp
    # function
    mock_fp_responses = ["Response 1", "Response 2"]
    mock_fp_nodes = [Mock(), Mock()]
    # Create handler and test
    handler = DynamicFunctionalPromptHandler()
    with patch.object(handler.collector, "collect_parameters") as mock_collect:
        mock_collect.return_value = {"prompt": "Test prompt"}
        with patch.object(fp, "broadcast_fp", return_value=(mock_fp_responses, mock_fp_nodes)):
            result = handler.broadcast_fp(mock_bot, mock_context, [])
    # Verify the result indicates success
    assert "Broadcast completed" in result
    assert "successful" in result


@patch("builtins.input")
@patch("builtins.print")
def test_broadcast_fp_new_system_specific_leaves(mock_print, mock_input):
    """Test broadcast_fp with new leaf selection system - select specific
    leaves."""
    # Setup mock bot and context
    mock_bot = Mock()
    mock_context = Mock()
    mock_conversation_handler = Mock()
    # Create mock leaves
    leaf1 = Mock(spec=ConversationNode)
    leaf1.content = "First leaf content"
    leaf1.labels = []
    leaf2 = Mock(spec=ConversationNode)
    leaf2.content = "Second leaf content"
    leaf2.labels = ["test"]
    leaf3 = Mock(spec=ConversationNode)
    leaf3.content = "Third leaf content"
    leaf3.labels = []
    leaves = [leaf1, leaf2, leaf3]
    # Setup mock methods
    mock_conversation_handler._find_leaves.return_value = leaves
    mock_conversation_handler._get_leaf_preview.side_effect = lambda leaf: leaf.content[:50]
    mock_conversation_handler._calculate_depth.return_value = 1
    mock_context.conversation = mock_conversation_handler
    # Setup input sequence: select leaves 1 and 3, choose single_prompt,
    # provide prompt
    mock_input.side_effect = ["1,3", "1", "Test prompt"]
    # Setup functional prompt execution - mock the actual fp.broadcast_fp
    # function
    mock_fp_responses = ["Response 1", "Response 3"]  # Only 2 responses for selected leaves
    mock_fp_nodes = [Mock(), Mock()]
    # Create handler and test
    handler = DynamicFunctionalPromptHandler()
    with patch.object(handler.collector, "collect_parameters") as mock_collect:
        mock_collect.return_value = {"prompt": "Test prompt"}
        with patch.object(fp, "broadcast_fp", return_value=(mock_fp_responses, mock_fp_nodes)):
            result = handler.broadcast_fp(mock_bot, mock_context, [])
    # Verify the result indicates success
    assert "Broadcast completed" in result
    assert "successful" in result


@patch("builtins.input")
@patch("builtins.print")
def test_broadcast_fp_no_leaves(mock_print, mock_input):
    """Test broadcast_fp when no leaves are found."""
    # Setup mock bot and context
    mock_bot = Mock()
    mock_context = Mock()
    mock_conversation_handler = Mock()
    # No leaves found
    mock_conversation_handler._find_leaves.return_value = []
    mock_context.conversation = mock_conversation_handler
    # Create handler and test
    handler = DynamicFunctionalPromptHandler()
    result = handler.broadcast_fp(mock_bot, mock_context, [])
    # Should return no leaves message
    assert result == "No leaves found from current node"


@patch("builtins.input")
@patch("builtins.print")
def test_broadcast_fp_invalid_leaf_selection(mock_print, mock_input):
    """Test broadcast_fp with invalid leaf selection."""
    # Setup mock bot and context
    mock_bot = Mock()
    mock_context = Mock()
    mock_conversation_handler = Mock()
    # Create mock leaves
    leaf1 = Mock(spec=ConversationNode)
    leaf1.content = "First leaf content"
    leaf1.labels = []
    leaves = [leaf1]
    # Setup mock methods
    mock_conversation_handler._find_leaves.return_value = leaves
    mock_conversation_handler._get_leaf_preview.side_effect = lambda leaf: leaf.content[:50]
    mock_conversation_handler._calculate_depth.return_value = 1
    mock_context.conversation = mock_conversation_handler
    # Setup input sequence: invalid leaf selection
    mock_input.side_effect = ["5"]  # Invalid - only 1 leaf available
    # Create handler and test
    handler = DynamicFunctionalPromptHandler()
    result = handler.broadcast_fp(mock_bot, mock_context, [])
    # Should return error message
    assert "Invalid leaf number" in result
