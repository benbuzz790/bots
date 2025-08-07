// Tree-specific types for React Flow conversation tree visualization
import { ConversationNode } from './index';

export interface ToolCall {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'error';
  result?: string;
  error?: string;
}

export interface ConversationNodeData {
  role: 'user' | 'assistant' | 'system' | 'empty';
  content: string;
  preview: string;
  is_current: boolean;
  has_tool_calls: boolean;
  tool_calls: ToolCall[];
  tool_results: any[];
  tool_count: number;
  timestamp?: string;
}

export interface ConversationTreeNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: ConversationNodeData;
}

export interface ConversationTreeEdge {
  id: string;
  source: string;
  target: string;
  type: string;
}

export interface ConversationTreeData {
  nodes: ConversationTreeNode[];
  edges: ConversationTreeEdge[];
  current_node_id: string;
  layout_config: {
    node_width: number;
    node_height: number;
    horizontal_spacing: number;
    vertical_spacing: number;
  };
}

export interface ConversationTreeProps {
  botId: string;
  conversationTree: Record<string, ConversationNode>;
  currentNodeId: string;
  _onNodeClick?: (nodeId: string) => void;
  _onNavigate?: (direction: 'up' | 'down' | 'left' | 'right' | 'root') => void;
}

export interface ConversationTreeDisplayProps {
  treeData: ConversationTreeData;
  onNodeClick?: (nodeId: string, nodeData: ConversationNodeData) => void;
  onNavigate?: (nodeId: string) => void;
  className?: string;
  height?: string | number;
  width?: string | number;
}
