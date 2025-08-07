import React, { useState, useRef, KeyboardEvent, useMemo } from 'react';
import type { MessageInputProps } from '../types';
/**
 * Enhanced message input component with slash command hints
 */
export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled }) => {
  // Input validation
  if (typeof onSendMessage !== 'function') {
    throw new Error(`onSendMessage must be function, got ${typeof onSendMessage}`);
  }
  if (typeof disabled !== 'boolean') {
    throw new Error(`disabled must be boolean, got ${typeof disabled}`);
  }
  const [message, setMessage] = useState('');
  const [showHints, setShowHints] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  // Slash command hints
  const slashCommands = useMemo(() => [
    { command: '/up', description: 'Navigate up in conversation tree' },
    { command: '/down', description: 'Navigate down in conversation tree' },
    { command: '/left', description: 'Navigate to left sibling' },
    { command: '/right', description: 'Navigate to right sibling' },
    { command: '/root', description: 'Navigate to root of conversation' },
    { command: '/save', description: 'Save bot state to file' },
    { command: '/load', description: 'Load bot state from file' },
    { command: '/help', description: 'Show help information' },
    { command: '/auto', description: 'Toggle autonomous mode' },
    { command: '/fp', description: 'Show functional prompt info' }
  ], []);
  // Filter commands based on current input
  const filteredCommands = useMemo(() => {
    if (!message.startsWith('/') || message.includes(' ')) {
      return [];
    }
    const query = message.toLowerCase();
    return slashCommands.filter(cmd =>
      cmd.command.toLowerCase().startsWith(query)
    ).slice(0, 5); // Show max 5 suggestions
  }, [message, slashCommands]);
  /**
   * Handle message sending with validation
   */
  const handleSend = () => {
    try {
      const trimmedMessage = message.trim();
      console.log('MessageInput handleSend called:', { message: trimmedMessage, disabled });
      // Validate message content
      if (!trimmedMessage) {
        console.warn('Cannot send empty message');
        return;
      }
      if (disabled) {
        console.warn('Cannot send message while disabled');
        return;
      }
      // Send message
      console.log('Calling onSendMessage with:', trimmedMessage);
      onSendMessage(trimmedMessage);
      setMessage('');
      setShowHints(false);
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };
  /**
   * Handle keyboard events with validation and hint navigation
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    try {
      if (!e || typeof e.key !== 'string') {
        return;
      }
      // Handle hint selection with Tab
      if (e.key === 'Tab' && filteredCommands.length > 0) {
        e.preventDefault();
        const firstCommand = filteredCommands[0];
        setMessage(firstCommand.command + ' ');
        setShowHints(false);
        return;
      }
      // Escape to hide hints
      if (e.key === 'Escape') {
        setShowHints(false);
        return;
      }
      // Enter to send, Shift+Enter for new line
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    } catch (error) {
      console.error('Error handling key down:', error);
    }
  };
  /**
   * Auto-resize textarea and handle slash command hints
   */
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    try {
      const target = e.target;
      if (!target) return;
      const newValue = target.value;
      setMessage(newValue);
      // Show/hide hints based on slash command input
      const shouldShowHints = newValue.startsWith('/') &&
                             !newValue.includes(' ') &&
                             newValue.length > 1;
      setShowHints(shouldShowHints);
      // Auto-resize
      target.style.height = 'auto';
      target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
    } catch (error) {
      console.error('Error handling input:', error);
    }
  };
  /**
   * Handle hint click
   */
  const handleHintClick = (command: string) => {
    try {
      setMessage(command + ' ');
      setShowHints(false);
      // Focus back to textarea
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    } catch (error) {
      console.error('Error handling hint click:', error);
    }
  };
  const isSlashCommand = message.trim().startsWith('/');
  const placeholderText = disabled
    ? "Bot is thinking..."
    : "Type your message or /command... (Enter to send, Shift+Enter for new line)";
  return (
    <div className="relative">
      {/* Slash Command Hints */}
      {showHints && filteredCommands.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <div className="p-2 text-xs text-gray-600 border-b border-gray-100">
            Slash Commands (Tab to complete, Esc to close)
          </div>
          {filteredCommands.map((cmd, _index) => (
            <div
              key={cmd.command}
              className="flex items-center justify-between p-2 hover:bg-gray-50 cursor-pointer text-sm"
              onClick={() => handleHintClick(cmd.command)}
            >
              <span className="font-mono text-blue-600">{cmd.command}</span>
              <span className="text-gray-500 text-xs">{cmd.description}</span>
            </div>
          ))}
        </div>
      )}
      {/* Input Container */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder={placeholderText}
              className={`
                w-full min-h-[40px] max-h-[120px] p-3
                border border-gray-300 rounded-lg resize-none
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900
                ${disabled ? 'bg-gray-50 text-gray-500' : 'bg-white'}
              `}
            />
            {/* Slash command indicator */}
            {isSlashCommand && (
              <div className="absolute top-1 right-1 text-xs text-blue-500 bg-blue-50 px-1 rounded">
                CMD
              </div>
            )}
          </div>
          <button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            className={`
              px-4 py-2 rounded-lg font-medium text-sm transition-colors
              ${disabled || !message.trim() 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-blue-500 text-white hover:bg-blue-600'}
            `}
          >
            Send
          </button>
        </div>
        {/* Help text */}
        <div className="mt-2 text-xs text-gray-500 flex justify-between">
          <span>
            {isSlashCommand ? 'Type slash commands for navigation and controls' : 'Enter to send • Shift+Enter for new line'}
          </span>
          {filteredCommands.length > 0 && (
            <span>Tab to complete command</span>
          )}
        </div>
      </div>
    </div>
  );
};
export default MessageInput;
