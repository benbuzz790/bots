import React, { useMemo, useCallback, useState } from 'react';
import type { ChatInterfaceProps, Message } from '../types';
import { useBotStore } from '../store/botStore';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { GitTreeVisualization } from './GitTreeVisualization';
import { useSlashCommandProcessor, SlashCommandHelp } from './SlashCommandProcessor';
/**
 * Enhanced chat interface with tree navigation and slash commands
 */
export const ChatInterface: React.FC<ChatInterfaceProps> = ({ botId }) => {
  // Input validation
  if (typeof botId !== 'string') {
    throw new Error(`Bot ID must be string, got ${typeof botId}`);
  }
  if (!botId.trim()) {
    throw new Error('Bot ID cannot be empty');
  }
  // Local state
  const [showHelp, setShowHelp] = useState(false);
  const [autoMode, setAutoMode] = useState(false);
  // Get bot state from store
  const bot = useBotStore(state => state.bots[botId]);
  const connected = useBotStore(state => state.connected);
  const systemMessages = useBotStore(state => state.systemMessages);
  const sendMessage = useBotStore(state => state.sendMessage);
  const navigate = useBotStore(state => state.navigate);
  const navigateToNode = useBotStore(state => state.navigateToNode);
  const addSystemMessage = useBotStore(state => state.addSystemMessage);
  // HOOK FIX: Moved bot validation to JSX to ensure consistent hook calls
  const botExists = !!bot;
  /**
   * Extract messages from conversation tree with defensive validation
   */
  const messages = useMemo(() => {
    try {
      if (!bot.conversationTree || typeof bot.conversationTree !== 'object') {
        console.warn('Invalid conversation tree');
        return [];
      }
      const messageList: Message[] = [];
      // Find path from root to current node
      const buildPath = (nodeId: string): string[] => {
        const path: string[] = [];
        let currentId = nodeId;
        while (currentId) {
          const node = bot.conversationTree[currentId];
          if (!node) break;
          path.unshift(currentId);
          currentId = node.parent || '';
        }
        return path;
      };
      const pathToCurrentNode = buildPath(bot.currentNodeId);
      // Extract messages along the path
      for (const nodeId of pathToCurrentNode) {
        const node = bot.conversationTree[nodeId];
        if (node && node.message.content.trim()) {
          // Skip system initialization messages unless they have meaningful content
          if (node.message.role !== 'system' || node.message.content !== 'Bot initialized') {
            messageList.push(node.message);
          }
        }
      }
      return messageList;
    } catch (error) {
      console.error('Error extracting messages:', error);
      return [];
    }
  }, [bot.conversationTree, bot.currentNodeId]);
  /**
   * Handle navigation with defensive validation
   */
  const handleNavigate = useCallback((direction: 'up' | 'down' | 'left' | 'right' | 'root') => {
    try {
      if (!connected) {
        addSystemMessage('Cannot navigate: not connected to server');
        return;
      }
      navigate(botId, direction);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Navigation failed';
      addSystemMessage(`Navigation error: ${errorMessage}`);
      console.error('Navigation error:', error);
    }
  }, [botId, connected, navigate, addSystemMessage]);
  /**
   * Handle node click navigation
   */
  const handleNodeClick = useCallback((nodeId: string) => {
    try {
      if (!connected) {
        addSystemMessage('Cannot navigate: not connected to server');
        return;
      }
      navigateToNode(botId, nodeId);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Navigation failed';
      addSystemMessage(`Navigation error: ${errorMessage}`);
      console.error('Node click error:', error);
    }
  }, [botId, connected, navigateToNode, addSystemMessage]);
  /**
   * Slash command handlers
   */
  const slashCommandHandlers = useMemo(() => ({
    onNavigate: handleNavigate,
    onSave: () => {
      addSystemMessage('Save functionality not yet implemented');
      // TODO: Implement save functionality
    },
    onLoad: () => {
      addSystemMessage('Load functionality not yet implemented');
      // TODO: Implement load functionality
    },
    onHelp: () => {
      setShowHelp(true);
    },
    onAuto: () => {
      setAutoMode(prev => !prev);
      addSystemMessage(autoMode ? 'Auto mode disabled' : 'Auto mode enabled');
      // TODO: Implement auto mode functionality
    },
    onFunctionalPrompt: () => {
      addSystemMessage('Functional prompts: Use the CLI for advanced functional prompts like chain, branch, and prompt_while');
    },
    onSystemMessage: addSystemMessage
  }), [handleNavigate, addSystemMessage, autoMode]);
  const { processCommand } = useSlashCommandProcessor(slashCommandHandlers);
  /**
   * Handle sending message with slash command processing
   */
  const handleSendMessage = useCallback((content: string) => {
    try {
      console.log('ChatInterface handleSendMessage called:', { content, connected, botId });
      if (!connected) {
        addSystemMessage('Cannot send message: not connected to server');
        return;
      }
      // Check if it's a slash command
      if (content.trim().startsWith('/')) {
        const wasProcessed = processCommand(content.trim());
        if (wasProcessed) {
          return; // Command was handled
        }
      }
      // Regular message
      console.log('Calling sendMessage with:', { botId, content });
      sendMessage(botId, content);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      addSystemMessage(`Error: ${errorMessage}`);
      console.error('Error sending message:', error);
    }
  }, [botId, connected, sendMessage, processCommand, addSystemMessage]);
  return botExists ? (
    <div className="flex min-h-screen bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Left Panel - Conversation Tree */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col">
          <GitTreeVisualization
          botId={botId}
          conversationTree={bot.conversationTree}
          currentNodeId={bot.currentNodeId}
          onNodeClick={handleNodeClick}
        />
      </div>
      {/* Right Panel - Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 p-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div 
              className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}
            />
            <span className="font-semibold text-sm">{bot.name}</span>
            <span className="text-xs text-gray-600 ml-auto">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
            {autoMode && (
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                AUTO
              </span>
            )}
          </div>
        </div>
        {/* Messages */}
        <div className="flex-1 overflow-hidden">
          <MessageList
            messages={messages}
            isThinking={bot.isThinking}
          />
        </div>
        {/* System Messages */}
        {systemMessages.length > 0 && (
          <div className="flex-shrink-0 max-h-20 overflow-y-auto bg-yellow-50 border-t border-yellow-200 p-2">
            {systemMessages.slice(-3).map(msg => (
              <div key={msg.id} className="text-xs text-yellow-800 mb-1">
                <span className="font-mono">[{new Date(msg.timestamp).toLocaleTimeString()}]</span> {msg.content}
              </div>
            ))}
          </div>
        )}
        {/* Input */}
        <div className="flex-shrink-0">
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={!connected || bot.isThinking}
          />
        </div>
      </div>
      {/* Help Modal */}
      {showHelp && (
        <SlashCommandHelp onClose={() => setShowHelp(false)} />
      )}
    </div>
  ) : (
    <div className="flex justify-center items-center h-full text-gray-600 text-lg">
      Bot not found: {botId}
    </div>
  );
};
export default ChatInterface;
