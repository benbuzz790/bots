/**
 * ConversationTree.tsx
 *
 * React Flow component for displaying conversation trees from the bots framework.
 * Provides interactive visualization with custom node types, navigation, and tool indicators.
 */

import React, { useCallback, useMemo, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
  NodeTypes,
  Position,
  MarkerType,
  ReactFlowProvider,
  useReactFlow,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ConversationTreeProps, ConversationNodeData, ConversationTreeData } from '../types/tree';
import { useBotStore } from '../store/botStore';

// ============================================================================
// Validation Utilities
// ============================================================================

const validateTreeData = (data: any): ConversationTreeData => {
  if (!data || typeof data !== 'object') {
    throw new Error('Tree data must be an object');
  }

  if (!Array.isArray(data.nodes)) {
    throw new Error('Tree data must have nodes array');
  }

  if (!Array.isArray(data.edges)) {
    throw new Error('Tree data must have edges array');
  }

  if (!data.current_node_id || typeof data.current_node_id !== 'string') {
    throw new Error('Tree data must have current_node_id string');
  }

  // Validate nodes
  data.nodes.forEach((node: any, index: number) => {
    if (!node.id || typeof node.id !== 'string') {
      throw new Error(`Node ${index} must have string id`);
    }
    if (!node.data || typeof node.data !== 'object') {
      throw new Error(`Node ${index} must have data object`);
    }
    if (!node.position || typeof node.position.x !== 'number' || typeof node.position.y !== 'number') {
      throw new Error(`Node ${index} must have valid position`);
    }
  });

  // Validate edges
  data.edges.forEach((edge: any, index: number) => {
    if (!edge.id || typeof edge.id !== 'string') {
      throw new Error(`Edge ${index} must have string id`);
    }
    if (!edge.source || typeof edge.source !== 'string') {
      throw new Error(`Edge ${index} must have string source`);
    }
    if (!edge.target || typeof edge.target !== 'string') {
      throw new Error(`Edge ${index} must have string target`);
    }
  });

  return data as ConversationTreeData;
};

const validateNodeData = (data: any): ConversationNodeData => {
  if (!data || typeof data !== 'object') {
    throw new Error('Node data must be an object');
  }

  const requiredFields = ['role', 'content', 'preview', 'is_current', 'has_tool_calls', 'tool_count'];
  for (const field of requiredFields) {
    if (!(field in data)) {
      throw new Error(`Node data missing required field: ${field}`);
    }
  }

  if (!['user', 'assistant', 'system', 'empty'].includes(data.role)) {
    throw new Error(`Invalid role: ${data.role}`);
  }

  if (typeof data.content !== 'string') {
    throw new Error('Node content must be string');
  }

  if (typeof data.is_current !== 'boolean') {
    throw new Error('Node is_current must be boolean');
  }

  return data as ConversationNodeData;
};

// ============================================================================
// Custom Node Components
// ============================================================================

const UserNode: React.FC<{ data: ConversationNodeData; selected: boolean }> = ({ data, selected }) => {
  const validatedData = validateNodeData(data);

  return (
    <div className={`
      bg-blue-100 border-2 rounded-lg p-3 min-w-[200px] max-w-[300px] shadow-md
      ${validatedData.is_current ? 'border-blue-500 ring-2 ring-blue-300' : 'border-blue-300'}
      ${selected ? 'ring-2 ring-blue-400' : ''}
      hover:shadow-lg transition-shadow cursor-pointer
    `}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
        <span className="text-sm font-medium text-blue-700">User</span>
        {validatedData.is_current && (
          <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">Current</span>
        )}
      </div>
      <div className="text-sm text-gray-800 break-words">
        {validatedData.preview}
      </div>
      {validatedData.timestamp && (
        <div className="text-xs text-gray-500 mt-2">
          {new Date(validatedData.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

const AssistantNode: React.FC<{ data: ConversationNodeData; selected: boolean }> = ({ data, selected }) => {
  const validatedData = validateNodeData(data);

  return (
    <div className={`
      bg-green-100 border-2 rounded-lg p-3 min-w-[200px] max-w-[300px] shadow-md
      ${validatedData.is_current ? 'border-green-500 ring-2 ring-green-300' : 'border-green-300'}
      ${selected ? 'ring-2 ring-green-400' : ''}
      hover:shadow-lg transition-shadow cursor-pointer
    `}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
        <span className="text-sm font-medium text-green-700">Assistant</span>
        {validatedData.is_current && (
          <span className="text-xs bg-green-500 text-white px-2 py-1 rounded-full">Current</span>
        )}
        {validatedData.has_tool_calls && (
          <span className="text-xs bg-orange-500 text-white px-2 py-1 rounded-full flex items-center gap-1">
            🔧 {validatedData.tool_count}
          </span>
        )}
      </div>
      <div className="text-sm text-gray-800 break-words">
        {validatedData.preview}
      </div>
      {validatedData.has_tool_calls && validatedData.tool_calls.length > 0 && (
        <div className="mt-2 space-y-1">
          {validatedData.tool_calls.slice(0, 3).map((tool, index) => (
            <div key={index} className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
              {tool.name} {tool.status === 'running' ? '⏳' : tool.status === 'completed' ? '✅' : '❌'}
            </div>
          ))}
          {validatedData.tool_calls.length > 3 && (
            <div className="text-xs text-gray-500">
              +{validatedData.tool_calls.length - 3} more tools
            </div>
          )}
        </div>
      )}
      {validatedData.timestamp && (
        <div className="text-xs text-gray-500 mt-2">
          {new Date(validatedData.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

const SystemNode: React.FC<{ data: ConversationNodeData; selected: boolean }> = ({ data, selected }) => {
  const validatedData = validateNodeData(data);

  return (
    <div className={`
      bg-gray-100 border-2 rounded-lg p-3 min-w-[200px] max-w-[300px] shadow-md
      ${validatedData.is_current ? 'border-gray-500 ring-2 ring-gray-300' : 'border-gray-300'}
      ${selected ? 'ring-2 ring-gray-400' : ''}
      hover:shadow-lg transition-shadow cursor-pointer
    `}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
        <span className="text-sm font-medium text-gray-700">System</span>
        {validatedData.is_current && (
          <span className="text-xs bg-gray-500 text-white px-2 py-1 rounded-full">Current</span>
        )}
      </div>
      <div className="text-sm text-gray-800 break-words">
        {validatedData.preview}
      </div>
    </div>
  );
};

const EmptyNode: React.FC<{ data: ConversationNodeData; selected: boolean }> = ({ data, selected }) => {
  const validatedData = validateNodeData(data);

  return (
    <div className={`
      bg-gray-50 border-2 border-dashed rounded-lg p-3 min-w-[150px] max-w-[200px] shadow-sm
      ${validatedData.is_current ? 'border-gray-400 ring-2 ring-gray-200' : 'border-gray-200'}
      ${selected ? 'ring-2 ring-gray-300' : ''}
      hover:shadow-md transition-shadow cursor-pointer opacity-60
    `}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
        <span className="text-sm font-medium text-gray-500">Root</span>
      </div>
      <div className="text-xs text-gray-500 italic">
        Conversation start
      </div>
    </div>
  );
};

// ============================================================================
// Conversion Function - Convert current format to React Flow format
// ============================================================================

const convertToReactFlowFormat = (
  conversationTree: Record<string, any>,
  currentNodeId: string
): ConversationTreeData => {
  console.log('🔄 Converting conversation tree to React Flow format');
  console.log('🔄 Input tree:', Object.keys(conversationTree).length, 'nodes');
  console.log('🔄 Current node ID:', currentNodeId);

  // For now, create a simple fallback visualization
  const nodes = [];
  const edges = [];
  let yOffset = 0;

  // Convert each node in the conversation tree
  for (const [nodeId, node] of Object.entries(conversationTree)) {
    if (!node || !node.message) continue;

    const message = node.message;
    const nodeData: ConversationNodeData = {
      role: message.role as 'user' | 'assistant' | 'system' | 'empty',
      content: message.content || '',
      preview: (message.content || '').substring(0, 50) + ((message.content || '').length > 50 ? '...' : ''),
      is_current: nodeId === currentNodeId,
      has_tool_calls: (message.toolCalls && message.toolCalls.length > 0) || false,
      tool_calls: message.toolCalls || [],
      tool_results: [],
      tool_count: (message.toolCalls && message.toolCalls.length) || 0,
      timestamp: message.timestamp
    };

    nodes.push({
      id: nodeId,
      type: message.role || 'system',
      position: { x: 0, y: yOffset },
      data: nodeData
    });

    // Create edge to parent if exists
    if (node.parent) {
      edges.push({
        id: `edge_${node.parent}_${nodeId}`,
        source: node.parent,
        target: nodeId,
        type: 'default'
      });
    }

    yOffset += 150;
  }

  console.log('🔄 Converted to React Flow format:', nodes.length, 'nodes,', edges.length, 'edges');

  return {
    nodes,
    edges,
    current_node_id: currentNodeId,
    layout_config: {
      node_width: 200,
      node_height: 100,
      horizontal_spacing: 250,
      vertical_spacing: 150
    }
  };
};

// ============================================================================
// Main Component
// ============================================================================

const ConversationTreeInner: React.FC<ConversationTreeProps> = ({
  botId,
  conversationTree,
  currentNodeId,
  _onNodeClick,
  _onNavigate,
}) => {
  console.log('🌳 ConversationTree render:', { botId, nodeCount: Object.keys(conversationTree).length, currentNodeId });
  
  // Check if we have React Flow data from backend
  const botState = useBotStore(state => state.bots[botId]);
  const backendTreeData = botState?.reactFlowData;

  // Convert current format to React Flow format
  const treeData = useMemo(() => {
    try {
      // Use backend React Flow data if available, otherwise convert
      if (backendTreeData && backendTreeData.nodes && backendTreeData.nodes.length > 0) {
        console.log('🌳 Using backend React Flow data:', backendTreeData.nodes.length, 'nodes');
        return backendTreeData;
      }
      return convertToReactFlowFormat(conversationTree, currentNodeId);
    } catch (error) {
      console.error('❌ Error converting tree data:', error);
      // Return empty tree data as fallback
      return {
        nodes: [],
        edges: [],
        current_node_id: currentNodeId,
        layout_config: {
          node_width: 200,
          node_height: 100,
          horizontal_spacing: 250,
          vertical_spacing: 150
        }
      };
    }
    }, [conversationTree, currentNodeId, backendTreeData]);

  // React Flow hooks
  const { fitView, zoomIn, zoomOut, zoomTo } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Custom node types
  const nodeTypes: NodeTypes = useMemo(() => ({
    user: ({ data, selected }) => <UserNode data={data} selected={selected} />,
    assistant: ({ data, selected }) => <AssistantNode data={data} selected={selected} />,
    system: ({ data, selected }) => <SystemNode data={data} selected={selected} />,
    empty: ({ data, selected }) => <EmptyNode data={data} selected={selected} />,
  }), []);

  // Update nodes and edges when tree data changes
  useEffect(() => {
    try {
      console.log('🔄 Updating React Flow with tree data:', treeData.nodes.length, 'nodes');
      
      const processedNodes = treeData.nodes.map(node => ({
        ...node,
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      }));

      const processedEdges = treeData.edges.map(edge => ({
        ...edge,
        type: 'smoothstep',
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#6b7280',
        },
        style: {
          stroke: '#6b7280',
          strokeWidth: 2,
        },
      }));

      setNodes(processedNodes);
      setEdges(processedEdges);

      // HOOK FIX: Auto-fit view with proper cleanup to prevent double-click issues
      const timeoutId = setTimeout(() => {
        try {
          fitView({ padding: 0.1, duration: 800 });
        } catch (error) {
          console.warn('fitView failed during timeout:', error);
        }
      }, 100);

      // Cleanup function to clear timeout on re-render
      return () => clearTimeout(timeoutId);
    } catch (error) {
      console.error('❌ Error processing tree data:', error);
    }
  }, [treeData, setNodes, setEdges, fitView]);

  // Handle node clicks
  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    try {
      console.log('🖱️ Node clicked:', node.id);
      const validatedData = validateNodeData(node.data);
      setSelectedNode(node.id);

      if (_onNodeClick) {
        _onNodeClick(node.id);
      }
    } catch (error) {
      console.error('❌ Error handling node click:', error);
    }
  }, [_onNodeClick]);

  // Focus on current node
  const focusCurrentNode = useCallback(() => {
    const currentNode = nodes.find(node => node.data.is_current);
    if (currentNode) {
      fitView({
        nodes: [currentNode],
        padding: 0.3,
        duration: 800,
      });
    }
  }, [nodes, fitView]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case '0':
            event.preventDefault();
            zoomTo(1);
            break;
          case '=':
          case '+':
            event.preventDefault();
            zoomIn();
            break;
          case '-':
            event.preventDefault();
            zoomOut();
            break;
          case 'f':
            event.preventDefault();
            fitView({ padding: 0.1, duration: 800 });
            break;
          case 'c':
            event.preventDefault();
            focusCurrentNode();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [zoomIn, zoomOut, zoomTo, fitView, focusCurrentNode]);

  // HOOK FIX: Moved conditional rendering to JSX to ensure consistent hook calls
  const hasNodes = treeData.nodes.length > 0;

  return hasNodes ? (
    <div className="conversation-tree-display h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        className="bg-gray-50"
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Background color="#e5e7eb" gap={20} />
        <Controls
          position="top-right"
          showInteractive={false}
        />
        <MiniMap
          position="bottom-right"
          nodeColor={(node) => {
            switch (node.type) {
              case 'user': return '#3b82f6';
              case 'assistant': return '#10b981';
              case 'system': return '#6b7280';
              case 'empty': return '#d1d5db';
              default: return '#6b7280';
            }
          }}
          maskColor="rgba(255, 255, 255, 0.8)"
          style={{
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            border: '1px solid #d1d5db',
          }}
        />

        {/* Custom control panel */}
        <Panel position="top-left" className="bg-white rounded-lg shadow-md p-3 space-y-2">
          <div className="text-sm font-medium text-gray-700 mb-2">
            Conversation Tree
          </div>
          <button
            onClick={focusCurrentNode}
            className="w-full px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Focus Current (Ctrl+C)
          </button>
          <button
            onClick={() => fitView({ padding: 0.1, duration: 800 })}
            className="w-full px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Fit View (Ctrl+F)
          </button>
          <div className="text-xs text-gray-500 space-y-1">
            <div>Ctrl+0: Reset Zoom</div>
            <div>Ctrl++: Zoom In</div>
            <div>Ctrl+-: Zoom Out</div>
          </div>

          {/* Node count info */}
          <div className="text-xs text-gray-500 pt-2 border-t">
            <div>Nodes: {nodes.length}</div>
            <div>Edges: {edges.length}</div>
            {selectedNode && (
              <div>Selected: {selectedNode.slice(0, 8)}...</div>
            )}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  ) : (
    <div className="h-full flex flex-col p-4">
      <h3 className="font-semibold text-sm mb-2">Conversation Tree</h3>
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p>No conversation yet</p>
          <p className="text-xs mt-1">Send a message to start</p>
        </div>
      </div>
    </div>
  );
};

// Wrapper component with ReactFlowProvider
export const ConversationTree: React.FC<ConversationTreeProps> = (props) => {
  return (
    <ReactFlowProvider>
      <ConversationTreeInner {...props} />
    </ReactFlowProvider>
  );
};

export default ConversationTree;

