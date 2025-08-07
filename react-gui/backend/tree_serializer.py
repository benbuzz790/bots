"""
Fixed tree serialization utilities that preserve original node IDs.
"""

import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json
import math
import logging

logger = logging.getLogger(__name__)

class NodeType(str, Enum):
    """Enumeration of conversation node types for React Flow."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    EMPTY = "empty"


@dataclass
class ReactFlowNode:
    """React Flow node representation with defensive validation."""
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]

    def __post_init__(self):
        """Validate node structure after initialization."""
        assert isinstance(self.id, str) and self.id.strip(), f"Node ID must be non-empty string, got {type(self.id)}: {self.id}"
        assert isinstance(self.type, str) and self.type.strip(), f"Node type must be non-empty string, got {type(self.type)}: {self.type}"
        assert isinstance(self.position, dict), f"Position must be dict, got {type(self.position)}"
        assert 'x' in self.position and 'y' in self.position, f"Position must have x,y keys, got {self.position.keys()}"
        assert isinstance(self.position['x'], (int, float)), f"Position x must be number, got {type(self.position['x'])}"
        assert isinstance(self.position['y'], (int, float)), f"Position y must be number, got {type(self.position['y'])}"
        assert isinstance(self.data, dict), f"Data must be dict, got {type(self.data)}"


@dataclass
class ReactFlowEdge:
    """React Flow edge representation with defensive validation."""
    id: str
    source: str
    target: str
    type: str = "default"

    def __post_init__(self):
        """Validate edge structure after initialization."""
        assert isinstance(self.id, str) and self.id.strip(), f"Edge ID must be non-empty string, got {self.id}"
        assert isinstance(self.source, str) and self.source.strip(), f"Source must be non-empty string, got {self.source}"
        assert isinstance(self.target, str) and self.target.strip(), f"Target must be non-empty string, got {self.target}"
        assert isinstance(self.type, str) and self.type.strip(), f"Type must be non-empty string, got {self.type}"


@dataclass
class TreeLayout:
    """Layout configuration for tree visualization."""
    node_width: int = 200
    node_height: int = 100
    horizontal_spacing: int = 250
    vertical_spacing: int = 150
    start_x: int = 100
    start_y: int = 100


def create_react_flow_node_fixed(node_id: str, conversation_node, position: Dict[str, float], is_current: bool = False) -> ReactFlowNode:
    """Create a React Flow node using the original node ID."""

    # Input validation
    assert isinstance(node_id, str) and node_id.strip(), f"Node ID must be non-empty string, got {node_id}"
    assert conversation_node is not None, "Conversation node cannot be None"
    assert isinstance(position, dict), f"Position must be dict, got {type(position)}"
    assert 'x' in position and 'y' in position, f"Position must have x,y keys, got {position.keys()}"
    assert isinstance(is_current, bool), f"is_current must be bool, got {type(is_current)}"

    # Extract content and role
    content = ""
    role = "system"
    timestamp = None

    if hasattr(conversation_node, 'message'):
        # GUI format with message wrapper
        message = conversation_node.message
        content = getattr(message, 'content', '')
        role = getattr(message, 'role', 'system')
        timestamp = getattr(message, 'timestamp', None)

        # Handle role enum
        if hasattr(role, 'value'):
            role = role.value
    elif hasattr(conversation_node, 'content'):
        # Direct bot framework format
        content = getattr(conversation_node, 'content', '')
        role = getattr(conversation_node, 'role', 'system')
    else:
        logger.warning(f"Unknown conversation node format: {type(conversation_node)}")
        content = str(conversation_node)
        role = "system"

    # Create preview text
    preview = content[:50].replace('\n', ' ')
    if len(content) > 50:
        preview += "..."

    # Determine node type
    node_type = role.lower() if role.lower() in ['user', 'assistant', 'system'] else 'system'

    # Create node data
    node_data = {
        'role': role,
        'content': content,
        'preview': preview,
        'timestamp': timestamp,
                    'isCurrent': is_current,  # Keep for React compatibility
                    'is_current': is_current,  # Add for backend compatibility
                    'hasToolCalls': False,  # React compatibility
                    'has_tool_calls': False,  # Backend compatibility
                    'toolCount': 0,  # React compatibility
                    'tool_count': 0  # Backend compatibility
    }

    # Extract tool information if available
    if hasattr(conversation_node, 'message'):
        message = conversation_node.message
        tool_calls = getattr(message, 'tool_calls', None) or getattr(message, 'toolCalls', None)
        if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
            node_data['hasToolCalls'] = True
            node_data['toolCount'] = len(tool_calls)

    return ReactFlowNode(
        id=node_id,  # Use original node ID!
        type=node_type,
        position=position,
        data=node_data
    )


def create_react_flow_edges_from_gui_tree_fixed(conversation_tree: Dict[str, Any]) -> List[ReactFlowEdge]:
    """Create React Flow edges from GUI conversation tree using original node IDs."""

    assert isinstance(conversation_tree, dict), f"conversation_tree must be dict, got {type(conversation_tree)}"

    edges = []

    for node_id, node_data in conversation_tree.items():
        if not node_data or not hasattr(node_data, 'children'):
            continue

        # Create edges to all children using original node IDs
        for child_id in node_data.children:
            if child_id in conversation_tree:
                edge_id = f"edge_{node_id}_{child_id}"
                edge = ReactFlowEdge(
                    id=edge_id,
                    source=node_id,  # Use original node ID
                    target=child_id,  # Use original node ID
                    type="default"
                )
                edges.append(edge)

    logger.info(f"Created {len(edges)} edges from conversation tree")
    return edges


def calculate_simple_layout_fixed(conversation_tree: Dict[str, Any], layout: TreeLayout) -> Dict[str, Dict[str, float]]:
    """Calculate layout positions for nodes using original node IDs."""

    assert isinstance(conversation_tree, dict), f"conversation_tree must be dict, got {type(conversation_tree)}"
    assert isinstance(layout, TreeLayout), f"Layout must be TreeLayout, got {type(layout)}"

    positions = {}

    if not conversation_tree:
        return positions

    # Find root node (node with no parent)
    root_node_id = None
    for node_id, node_data in conversation_tree.items():
        if not hasattr(node_data, 'parent') or not node_data.parent:
            root_node_id = node_id
            break

    if not root_node_id:
        # Fallback: use first node as root
        root_node_id = list(conversation_tree.keys())[0]

    # Simple vertical layout
    def layout_subtree(node_id: str, x: float, y: float, visited: Set[str]) -> float:
        if node_id in visited or node_id not in conversation_tree:
            return y

        visited.add(node_id)
        positions[node_id] = {'x': x, 'y': y}

        node_data = conversation_tree[node_id]
        current_y = y + layout.vertical_spacing

        if hasattr(node_data, 'children') and node_data.children:
            for child_id in node_data.children:
                current_y = layout_subtree(child_id, x, current_y, visited)

        return current_y

    # Start layout from root
    layout_subtree(root_node_id, layout.start_x, layout.start_y, set())

    logger.info(f"Calculated positions for {len(positions)} nodes")
    return positions


def serialize_gui_conversation_tree_fixed(
    conversation_tree: Dict[str, Any],
    current_node_id: str,
    layout: Optional[TreeLayout] = None
) -> Dict[str, Any]:
    """
    Serialize GUI conversation tree to React Flow format using original node IDs.

    Args:
        conversation_tree: GUI conversation tree format
        current_node_id: Current conversation position node ID
        layout: Optional layout configuration

    Returns:
        Dict[str, Any]: Complete React Flow data structure with nodes and edges
    """
    assert isinstance(conversation_tree, dict), f"conversation_tree must be dict, got {type(conversation_tree)}"
    assert isinstance(current_node_id, str), f"current_node_id must be str, got {type(current_node_id)}"

    if layout is None:
        layout = TreeLayout()
    assert isinstance(layout, TreeLayout), f"Layout must be TreeLayout, got {type(layout)}"

    logger.info(f"🔄 Serializing GUI conversation tree: {len(conversation_tree)} nodes, current: {current_node_id}")

    # Calculate layout positions using original node IDs
    positions = calculate_simple_layout_fixed(conversation_tree, layout)

    # Create React Flow nodes using original node IDs
    nodes = []
    for node_id, node_data in conversation_tree.items():
        if not node_data:
            continue

        try:
            is_current = (node_id == current_node_id)
            position = positions.get(node_id, {'x': 0, 'y': 0})

            react_node = create_react_flow_node_fixed(node_id, node_data, position, is_current)
            nodes.append(react_node)

        except Exception as e:
            logger.error(f"❌ Error processing node {node_id}: {e}")
            continue

    # Create edges using original node IDs
    edges = create_react_flow_edges_from_gui_tree_fixed(conversation_tree)

    # Build final result
    result = {
        'nodes': [
            {
                'id': node.id,
                'type': node.type,
                'position': node.position,
                'data': node.data
            }
            for node in nodes
        ],
        'edges': [
            {
                'id': edge.id,
                'source': edge.source,
                'target': edge.target,
                'type': edge.type
            }
            for edge in edges
        ],
        'current_node_id': current_node_id,
        'layout_config': {
            'node_width': layout.node_width,
            'node_height': layout.node_height,
            'horizontal_spacing': layout.horizontal_spacing,
            'vertical_spacing': layout.vertical_spacing
        }
    }

    # Validate output
    assert isinstance(result, dict), f"Result must be dict, got {type(result)}"
    assert 'nodes' in result and 'edges' in result, "Result must have nodes and edges"
    assert isinstance(result['nodes'], list), f"Nodes must be list, got {type(result['nodes'])}"
    assert isinstance(result['edges'], list), f"Edges must be list, got {type(result['edges'])}"

    logger.info(f"✅ Serialized to React Flow format: {len(result['nodes'])} nodes, {len(result['edges'])} edges")

    return result
