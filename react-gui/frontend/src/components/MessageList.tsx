import React, { useEffect, useRef } from 'react';
import type { MessageListProps, Message, ToolCall } from '../types';

/**
 * Individual message component with defensive validation
 */
const MessageItem: React.FC<{ message: Message }> = ({ message }) => {
  // Input validation
  if (!message || typeof message !== 'object') {
    throw new Error(`Message must be object, got ${typeof message}`);
  }
  if (typeof message.id !== 'string' || !message.id.trim()) {
    throw new Error('Message must have valid ID');
  }
  if (!['user', 'assistant', 'system'].includes(message.role)) {
    throw new Error(`Invalid message role: ${message.role}`);
  }
  if (typeof message.content !== 'string') {
    throw new Error(`Message content must be string, got ${typeof message.content}`);
  }

  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  const roleIcon = isUser ? '👤' : isSystem ? '⚙️' : '🤖';
  const roleName = isUser ? 'You' : isSystem ? 'System' : 'Bot';
  
  const messageStyle: React.CSSProperties = {
    marginBottom: '16px',
    padding: '12px',
    borderRadius: '8px',
    backgroundColor: isUser ? '#007bff' : isSystem ? '#f5f5f5' : '#f0f8ff',
    border: `1px solid ${isUser ? '#0056b3' : isSystem ? '#e0e0e0' : '#b3e5fc'}`,
    color: isUser ? 'white' : '#333',
  };
  messageStyle.marginLeft = isUser ? 'auto' : '0';
  messageStyle.maxWidth = '70%';

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
    fontSize: '12px',
    color: isUser ? 'rgba(255,255,255,0.8)' : '#666',
    fontWeight: 'bold'
  };

  const contentStyle: React.CSSProperties = {
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    fontSize: '14px',
    lineHeight: '1.4',
    textAlign: 'left',
    color: isUser ? 'white' : '#333'
  };

  return (
    <div style={messageStyle}>
      <div style={headerStyle}>
        {isUser ? (
          // User messages: timestamp first, then name and icon
          <>
            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)' }}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
            <span style={{ marginLeft: 'auto' }}>{roleName}</span>
            <span>{roleIcon}</span>
          </>
        ) : (
          // Bot messages: icon and name first, then timestamp
          <>
            <span>{roleIcon}</span>
            <span>{roleName}</span>
            <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#999' }}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          </>
        )}
      </div>
      
      <div style={contentStyle}>
        {message.content}
      </div>
      
      {message.toolCalls && message.toolCalls.length > 0 && (
        <ToolCallsDisplay toolCalls={message.toolCalls} />
      )}
    </div>
  );
};

/**
 * Tool calls display component
 */
const ToolCallsDisplay: React.FC<{ toolCalls: ToolCall[] }> = ({ toolCalls }) => {
  // Input validation
  if (!Array.isArray(toolCalls)) {
    throw new Error(`Tool calls must be array, got ${typeof toolCalls}`);
  }

  const containerStyle: React.CSSProperties = {
    marginTop: '8px',
    padding: '8px',
    backgroundColor: '#f8f9fa',
    border: '1px solid #dee2e6',
    borderRadius: '4px',
    fontSize: '12px'
  };

  return (
    <div style={containerStyle}>
      <div style={{ fontWeight: 'bold', marginBottom: '4px', color: '#495057' }}>
        🔧 Tools Used:
      </div>
      {toolCalls.map((toolCall, index) => {
        const statusColor = toolCall.status === 'completed' ? '#28a745' : 
                           toolCall.status === 'error' ? '#dc3545' : '#ffc107';
        
        return (
          <div key={toolCall.id || index} style={{ marginBottom: '4px' }}>
            <span style={{ color: statusColor, fontWeight: 'bold' }}>
              {toolCall.status === 'completed' ? '✅' : 
               toolCall.status === 'error' ? '❌' : '⏳'}
            </span>
            <span style={{ marginLeft: '4px' }}>{toolCall.name}</span>
            {toolCall.error && (
              <div style={{ color: '#dc3545', marginLeft: '16px', fontSize: '11px' }}>
                Error: {toolCall.error}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

/**
 * Message list component with auto-scroll and defensive validation
 */
export const MessageList: React.FC<MessageListProps> = ({ messages, isThinking }) => {
  // Input validation
  if (!Array.isArray(messages)) {
    throw new Error(`Messages must be array, got ${typeof messages}`);
  }
  if (typeof isThinking !== 'boolean') {
    throw new Error(`isThinking must be boolean, got ${typeof isThinking}`);
  }

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    try {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      console.error('Error scrolling to bottom:', error);
    }
  }, [messages, isThinking]);

  const containerStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    backgroundColor: '#fafafa'
  };

  return (
    <div style={containerStyle}>
      {messages.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          color: '#666', 
          fontStyle: 'italic',
          marginTop: '50px'
        }}>
          No messages yet. Start a conversation!
        </div>
      ) : (
        messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))
      )}
      
      {isThinking && (
        <div style={{
          padding: '12px',
          fontStyle: 'italic',
          color: '#666',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <div style={{
            width: '16px',
            height: '16px',
            border: '2px solid #f3f3f3',
            borderTop: '2px solid #007bff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          Bot is thinking...
        </div>
      )}
      
      <div ref={messagesEndRef} />
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
