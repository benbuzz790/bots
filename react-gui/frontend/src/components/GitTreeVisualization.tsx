/**
 * GitTreeVisualization.tsx
 * 
 * Git-like tree visualization for conversation history.
 * Provides hover tooltips and double-click navigation with smart assistant node targeting.
 */

import React, { useState, useCallback, useMemo } from 'react';
import type { ConversationNode } from '../types';

interface GitTreeVisualizationProps {
  botId: string;
  conversationTree: Record<string, ConversationNode>;
  currentNodeId: string;
  onNodeClick?: (nodeId: string) => void;
}

interface TreeNodeInfo {
  id: string;
  node: ConversationNode;
  depth: number;
  isLast: boolean;
  parentConnectors: boolean[];
}

// Validation functions with defensive programming
const validateProps = (props: GitTreeVisualizationProps): void => {
  if (!props.botId || typeof props.botId !== 'string') {
    throw new Error('botId must be a non-empty string');
  }
  
  if (!props.conversationTree || typeof props.conversationTree !== 'object') {
    throw new Error('conversationTree must be an object');
  }
  
  if (typeof props.currentNodeId !== 'string') {
    throw new Error('currentNodeId must be a string');
  }
  
  if (props.onNodeClick && typeof props.onNodeClick !== 'function') {
    throw new Error('onNodeClick must be a function');
  }
};

const validateNode = (node: ConversationNode): void => {
  if (!node || typeof node !== 'object') {
    throw new Error('Node must be an object');
  }
  
  if (!node.id || typeof node.id !== 'string') {
    throw new Error('Node must have a valid id');
  }
  
  if (!node.message || typeof node.message !== 'object') {
    throw new Error('Node must have a valid message');
  }
  
  if (!['user', 'assistant', 'system'].includes(node.message.role)) {
    throw new Error(`Invalid node role: ${node.message.role}`);
  }
};

export const GitTreeVisualization: React.FC<GitTreeVisualizationProps> = (props) => {
  const { conversationTree, currentNodeId, onNodeClick } = props;
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null);

  // HOOK FIX: Moved validation to JSX to ensure consistent hook calls
  let validationError: Error | null = null;
  try {
    validateProps(props);
  } catch (error) {
    console.error('GitTreeVisualization props validation failed:', error);
    validationError = error instanceof Error ? error : new Error('Invalid props');
  }
  const isValid = !validationError;

  // Build tree structure with git-like connectors
  const treeStructure = useMemo(() => {
    try {
      const nodes: TreeNodeInfo[] = [];
      const visited = new Set<string>();

      const buildTree = (nodeId: string, depth: number, parentConnectors: boolean[]): void => {
        if (visited.has(nodeId) || !conversationTree[nodeId]) {
          return;
        }

        const node = conversationTree[nodeId];
        validateNode(node);
        visited.add(nodeId);

        const children = node.children || [];
        const isLast = depth === 0 || (node.parent && conversationTree[node.parent]?.children?.indexOf(nodeId) === (conversationTree[node.parent]?.children?.length || 0) - 1);

        nodes.push({
          id: nodeId,
          node,
          depth,
          isLast: Boolean(isLast),
          parentConnectors: [...parentConnectors]
        });

        // Process children
                children.forEach((childId) => {
          if (conversationTree[childId]) {
            const newConnectors = [...parentConnectors, !isLast];
            buildTree(childId, depth + 1, newConnectors);
          }
        });
      };

      // Find root node (node with no parent)
      const rootNodes = Object.values(conversationTree).filter(node => !node.parent);
      if (rootNodes.length > 0) {
        buildTree(rootNodes[0].id, 0, []);
      }

      return nodes;
    } catch (error) {
      console.error('Error building tree structure:', error);
      return [];
    }
  }, [conversationTree]);

  // Handle node hover
  const handleNodeHover = useCallback((event: React.MouseEvent, nodeId: string | null) => {
    try {
      if (nodeId) {
        const rect = event.currentTarget.getBoundingClientRect();
        setTooltipPosition({
          x: rect.right + 10,
          y: rect.top
        });
        setHoveredNode(nodeId);
      } else {
        setHoveredNode(null);
        setTooltipPosition(null);
      }
    } catch (error) {
      console.error('Error handling node hover:', error);
    }
  }, []);

  // Handle node click with smart navigation
  const handleNodeClick = useCallback((nodeId: string) => {
    try {
      if (!onNodeClick) return;

      const node = conversationTree[nodeId];
      if (!node) return;

      // If it's a user node, try to navigate to the assistant response
      if (node.message.role === 'user') {
        // Find the first assistant child
        const assistantChild = node.children?.find(childId => {
          const child = conversationTree[childId];
          return child && child.message.role === 'assistant';
        });

        if (assistantChild) {
          onNodeClick(assistantChild);
        }
        // If no assistant child, don't navigate
      } else if (node.message.role === 'assistant') {
        // Navigate directly to assistant nodes
        onNodeClick(nodeId);
      }
    } catch (error) {
      console.error('Error handling node click:', error);
    }
  }, [conversationTree, onNodeClick]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent, nodeId: string) => {
    try {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleNodeClick(nodeId);
      }
    } catch (error) {
      console.error('Error handling keyboard navigation:', error);
    }
  }, [handleNodeClick]);

  // Generate git-like connector string
  const generateConnector = (nodeInfo: TreeNodeInfo): string => {
    try {
      let connector = '';
      
      // Add parent connectors
      for (let i = 0; i < nodeInfo.depth; i++) {
        if (i < nodeInfo.parentConnectors.length && nodeInfo.parentConnectors[i]) {
          connector += '│  ';
        } else {
          connector += '   ';
        }
      }
      
      // Add current level connector
      if (nodeInfo.depth > 0) {
        connector += nodeInfo.isLast ? '└─ ' : '├─ ';
      }
      
      return connector;
    } catch (error) {
      console.error('Error generating connector:', error);
      return '';
    }
  };

  // Get role icon
  const getRoleIcon = (role: string): string => {
    switch (role) {
      case 'user': return '👤';
      case 'assistant': return '🤖';
      case 'system': return '⚙️';
      default: return '❓';
    }
  };

  // Get node styling classes
  const getNodeClasses = (nodeInfo: TreeNodeInfo): string => {
    const { node } = nodeInfo;
    const isCurrent = node.id === currentNodeId;
    const isAssistant = node.message.role === 'assistant';
    const isUser = node.message.role === 'user';
    
    let classes = 'inline-block px-2 py-1 rounded text-sm cursor-pointer transition-all duration-200 ';
    
    if (isCurrent) {
      classes += isAssistant 
        ? 'bg-green-100 border border-green-500 text-green-800 '
        : 'bg-blue-100 border border-blue-500 text-blue-800 ';
    } else {
      classes += isAssistant 
        ? 'bg-green-50 border border-green-200 text-green-700 hover:bg-green-100 '
        : isUser
        ? 'bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 '
        : 'bg-gray-50 border border-gray-200 text-gray-700 hover:bg-gray-100 ';
    }
    
    return classes;
  };

  // Get content preview
  const getContentPreview = (content: string, maxLength: number = 50): string => {
    if (!content) return '';
    return content.length > maxLength ? content.substring(0, maxLength) + '...' : content;
  };

  // HOOK FIX: Check empty state for conditional rendering
  const hasTreeNodes = treeStructure.length > 0;

  return isValid ? (hasTreeNodes ? (
    <div className="h-full flex flex-col p-4">
      <h3 className="font-semibold text-sm mb-4">Conversation Tree</h3>
      
      <div 
        className="flex-1 overflow-auto font-mono text-sm"
        data-testid="git-tree-container"
      >
        {treeStructure.map((nodeInfo) => {
          const { id, node } = nodeInfo;
          const connector = generateConnector(nodeInfo);
          const roleIcon = getRoleIcon(node.message.role);
          const preview = getContentPreview(node.message.content);
          const hasTools = node.message.toolCalls && node.message.toolCalls.length > 0;
          
          return (
            <div key={id} className="mb-1">
              <div className="flex items-start">
                {/* Git-like connector */}
                <span className="text-gray-400 select-none whitespace-pre">
                  {connector}
                </span>
                
                {/* Node content */}
                <div
                  data-testid={`tree-node-${id}`}
                  className={getNodeClasses(nodeInfo)}
                  onMouseEnter={(e) => handleNodeHover(e, id)}
                  onMouseLeave={(e) => handleNodeHover(e, null)}
                  onDoubleClick={() => handleNodeClick(id)}
                  onKeyDown={(e) => handleKeyDown(e, id)}
                  tabIndex={0}
                  role="button"
                  aria-label={`${node.message.role}: ${preview}`}
                >
                  <span className="mr-1">{roleIcon}</span>
                  <span>{preview}</span>
                  {hasTools && (
                    <span className="ml-2 text-orange-600">
                      🔧 {node.message.toolCalls?.length}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tooltip */}
      {hoveredNode && tooltipPosition && conversationTree[hoveredNode] && (
        <div
          className="fixed z-50 bg-gray-900 text-white text-xs rounded px-2 py-1 max-w-xs shadow-lg"
          style={{
            left: tooltipPosition.x,
            top: tooltipPosition.y,
            transform: 'translateY(-50%)'
          }}
        >
          <div className="font-semibold mb-1">
            {getRoleIcon(conversationTree[hoveredNode].message.role)} {conversationTree[hoveredNode].message.role}
          </div>
          <div className="break-words">
            {conversationTree[hoveredNode].message.content}
          </div>
          {conversationTree[hoveredNode].message.toolCalls && conversationTree[hoveredNode].message.toolCalls!.length > 0 && (
            <div className="mt-1 text-orange-300">
              🔧 {conversationTree[hoveredNode].message.toolCalls!.length} tool calls
            </div>
          )}
        </div>
      )}

      {/* Help text */}
      <div className="mt-4 text-xs text-gray-500 space-y-1">
        <div>• Hover to see full content</div>
        <div>• Double-click to navigate</div>
        <div>• User nodes → navigate to assistant response</div>
        <div>• Assistant nodes → navigate directly</div>
      </div>
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
      )) : (
        <div className="p-4 text-red-600">
          <div className="font-semibold">Error:</div>
          <div className="text-sm">{validationError?.message || 'Invalid props'}</div>
        </div>
  );
};

export default GitTreeVisualization;


