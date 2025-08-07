/**
 * Comprehensive tests for React components with defensive programming validation.
 * Tests component rendering, props validation, user interactions, and error handling.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Import components we're testing (assuming they'll be created)
// For now, we'll create mock components for testing structure
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'error';
  result?: string;
  error?: string;
}

// Mock components for testing
const App: React.FC = () => {
  return (
    <div data-testid="app">
      <h1>Bot GUI</h1>
      <ChatInterface botId="test-bot" />
    </div>
  );
};

interface ChatInterfaceProps {
  botId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ botId }) => {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [isThinking, setIsThinking] = React.useState(false);

  const handleSendMessage = (content: string) => {
    // Defensive validation
    if (!content || typeof content !== 'string') {
      throw new Error('Content must be a non-empty string');
    }
    if (!botId || typeof botId !== 'string') {
      throw new Error('Bot ID must be a non-empty string');
    }

    const newMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
    setIsThinking(true);

    // Simulate bot response
    setTimeout(() => {
      const botMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: `Response to: ${content}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, botMessage]);
      setIsThinking(false);
    }, 1000);
  };

  return (
    <div data-testid="chat-interface">
      <MessageList messages={messages} isThinking={isThinking} />
      <MessageInput onSendMessage={handleSendMessage} disabled={isThinking} />
    </div>
  );
};

interface MessageListProps {
  messages: Message[];
  isThinking: boolean;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isThinking }) => {
  // Defensive validation
  if (!Array.isArray(messages)) {
    throw new Error('Messages must be an array');
  }
  if (typeof isThinking !== 'boolean') {
    throw new Error('isThinking must be a boolean');
  }

  return (
    <div data-testid="message-list">
      {messages.map(message => (
        <div key={message.id} data-testid={`message-${message.role}`}>
          <strong>{message.role}:</strong> {message.content}
        </div>
      ))}
      {isThinking && (
        <div data-testid="thinking-indicator">Bot is thinking...</div>
      )}
    </div>
  );
};

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled }) => {
  // Defensive validation
  if (typeof onSendMessage !== 'function') {
    throw new Error('onSendMessage must be a function');
  }
  if (typeof disabled !== 'boolean') {
    throw new Error('disabled must be a boolean');
  }

  const [input, setInput] = React.useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} data-testid="message-input-form">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder="Type your message..."
        data-testid="message-input"
      />
      <button 
        type="submit" 
        disabled={disabled || !input.trim()}
        data-testid="send-button"
      >
        Send
      </button>
    </form>
  );
};

describe('App Component', () => {
  test('renders app with title', () => {
    render(<App />);
    
    expect(screen.getByTestId('app')).toBeInTheDocument();
    expect(screen.getByText('Bot GUI')).toBeInTheDocument();
    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
  });

  test('app structure is correct', () => {
    render(<App />);
    
    const app = screen.getByTestId('app');
    expect(app).toContainElement(screen.getByText('Bot GUI'));
    expect(app).toContainElement(screen.getByTestId('chat-interface'));
  });
});

describe('ChatInterface Component', () => {
  test('renders with required props', () => {
    render(<ChatInterface botId="test-bot" />);
    
    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    expect(screen.getByTestId('message-list')).toBeInTheDocument();
    expect(screen.getByTestId('message-input-form')).toBeInTheDocument();
  });

  test('validates botId prop', () => {
    // Test with invalid botId
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    expect(() => {
      render(<ChatInterface botId="" />);
    }).toThrow();
    
    consoleSpy.mockRestore();
  });

  test('handles message sending flow', async () => {
    const user = userEvent.setup();
    render(<ChatInterface botId="test-bot" />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    // Send a message
    await user.type(input, 'Hello, bot!');
    await user.click(sendButton);
    
    // Check user message appears
    expect(screen.getByTestId('message-user')).toBeInTheDocument();
    expect(screen.getByText(/Hello, bot!/)).toBeInTheDocument();
    
    // Check thinking indicator appears
    expect(screen.getByTestId('thinking-indicator')).toBeInTheDocument();
    
    // Wait for bot response
    await waitFor(() => {
      expect(screen.getByTestId('message-assistant')).toBeInTheDocument();
    }, { timeout: 2000 });
    
    // Check thinking indicator disappears
    expect(screen.queryByTestId('thinking-indicator')).not.toBeInTheDocument();
  });

  test('disables input during thinking', async () => {
    const user = userEvent.setup();
    render(<ChatInterface botId="test-bot" />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    // Send a message to trigger thinking state
    await user.type(input, 'Hello');
    await user.click(sendButton);
    
    // Check input is disabled during thinking
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
    
    // Wait for thinking to finish
    await waitFor(() => {
      expect(input).not.toBeDisabled();
    }, { timeout: 2000 });
  });
});

describe('MessageList Component', () => {
  const mockMessages: Message[] = [
    {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      timestamp: '2023-01-01T00:00:00Z'
    },
    {
      id: 'msg-2',
      role: 'assistant',
      content: 'Hi there!',
      timestamp: '2023-01-01T00:00:01Z'
    }
  ];

  test('renders messages correctly', () => {
    render(<MessageList messages={mockMessages} isThinking={false} />);
    
    expect(screen.getByTestId('message-user')).toBeInTheDocument();
    expect(screen.getByTestId('message-assistant')).toBeInTheDocument();
    expect(screen.getByText(/Hello/)).toBeInTheDocument();
    expect(screen.getByText(/Hi there!/)).toBeInTheDocument();
  });

  test('shows thinking indicator when thinking', () => {
    render(<MessageList messages={mockMessages} isThinking={true} />);
    
    expect(screen.getByTestId('thinking-indicator')).toBeInTheDocument();
    expect(screen.getByText('Bot is thinking...')).toBeInTheDocument();
  });

  test('hides thinking indicator when not thinking', () => {
    render(<MessageList messages={mockMessages} isThinking={false} />);
    
    expect(screen.queryByTestId('thinking-indicator')).not.toBeInTheDocument();
  });

  test('validates messages prop type', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    expect(() => {
      // @ts-ignore - Testing runtime validation
      render(<MessageList messages="not-an-array" isThinking={false} />);
    }).toThrow('Messages must be an array');
    
    consoleSpy.mockRestore();
  });

  test('validates isThinking prop type', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    expect(() => {
      // @ts-ignore - Testing runtime validation
      render(<MessageList messages={[]} isThinking="not-a-boolean" />);
    }).toThrow('isThinking must be a boolean');
    
    consoleSpy.mockRestore();
  });

  test('handles empty messages array', () => {
    render(<MessageList messages={[]} isThinking={false} />);
    
    expect(screen.getByTestId('message-list')).toBeInTheDocument();
    expect(screen.queryByTestId('message-user')).not.toBeInTheDocument();
    expect(screen.queryByTestId('message-assistant')).not.toBeInTheDocument();
  });

  test('renders messages with tool calls', () => {
    const messagesWithTools: Message[] = [
      {
        id: 'msg-1',
        role: 'assistant',
        content: 'I\'ll help you with that.',
        timestamp: '2023-01-01T00:00:00Z',
        toolCalls: [
          {
            id: 'tool-1',
            name: 'code_tools',
            status: 'completed',
            result: 'File created successfully'
          }
        ]
      }
    ];

    render(<MessageList messages={messagesWithTools} isThinking={false} />);
    
    expect(screen.getByTestId('message-assistant')).toBeInTheDocument();
    expect(screen.getByText(/I'll help you with that./)).toBeInTheDocument();
  });
});

describe('MessageInput Component', () => {
  const mockOnSendMessage = jest.fn();

  beforeEach(() => {
    mockOnSendMessage.mockClear();
  });

  test('renders input form correctly', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    expect(screen.getByTestId('message-input-form')).toBeInTheDocument();
    expect(screen.getByTestId('message-input')).toBeInTheDocument();
    expect(screen.getByTestId('send-button')).toBeInTheDocument();
  });

  test('validates onSendMessage prop type', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    expect(() => {
      // @ts-ignore - Testing runtime validation
      render(<MessageInput onSendMessage="not-a-function" disabled={false} />);
    }).toThrow('onSendMessage must be a function');
    
    consoleSpy.mockRestore();
  });

  test('validates disabled prop type', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    expect(() => {
      // @ts-ignore - Testing runtime validation
      render(<MessageInput onSendMessage={mockOnSendMessage} disabled="not-a-boolean" />);
    }).toThrow('disabled must be a boolean');
    
    consoleSpy.mockRestore();
  });

  test('sends message on form submit', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    await user.type(input, 'Test message');
    await user.click(sendButton);
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
    expect(input).toHaveValue('');
  });

  test('sends message on Enter key', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    
    await user.type(input, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
  });

  test('trims whitespace from messages', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    await user.type(input, '  Test message  ');
    await user.click(sendButton);
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
  });

  test('does not send empty messages', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const sendButton = screen.getByTestId('send-button');
    
    // Try to send empty message
    await user.click(sendButton);
    
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  test('does not send whitespace-only messages', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    await user.type(input, '   ');
    await user.click(sendButton);
    
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  test('disables input when disabled prop is true', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={true} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  test('disables send button when input is empty', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const sendButton = screen.getByTestId('send-button');
    
    expect(sendButton).toBeDisabled();
  });

  test('enables send button when input has content', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    await user.type(input, 'Test');
    
    expect(sendButton).not.toBeDisabled();
  });

  test('handles very long messages', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    const longMessage = 'A'.repeat(10000);
    await user.type(input, longMessage);
    await user.click(sendButton);
    
    expect(mockOnSendMessage).toHaveBeenCalledWith(longMessage);
  });

  test('handles special characters in messages', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={false} />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    const specialMessage = '<script>alert("xss")</script>';
    await user.type(input, specialMessage);
    await user.click(sendButton);
    
    expect(mockOnSendMessage).toHaveBeenCalledWith(specialMessage);
  });
});

export {};
