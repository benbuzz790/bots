// Core types matching the architecture.md specification
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  toolCalls?: ToolCall[];
}
export interface ToolCall {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'error';
  result?: string;
  error?: string;
}
export interface ConversationNode {
  id: string;
  message: Message;
  parent?: string;
  children: string[];
  isCurrent: boolean;
}
export interface BotState {
  id: string;
  name: string;
  conversationTree: Record<string, ConversationNode>;
  currentNodeId: string;
  isConnected: boolean;
  isThinking: boolean;
}
// WebSocket Event Types
export interface SendMessageEvent {
  type: 'send_message';
  data: {
    botId: string;
    content: string;
  };
}
export interface GetBotStateEvent {
  type: 'get_bot_state';
  data: {
    botId: string;
  };
}
export interface BotResponseEvent {
  type: 'bot_response';
  data: {
    botId: string;
    message: Message;
    conversationTree: Record<string, ConversationNode>;
    currentNodeId: string;
  };
}
export interface ToolUpdateEvent {
  type: 'tool_update';
  data: {
    botId: string;
    toolCall: ToolCall;
  };
}
export interface BotThinkingEvent {
  type: 'bot_thinking';
  data: {
    botId: string;
    thinking: boolean;
  };
}
export interface ErrorEvent {
  type: 'error';
  data: {
    message: string;
    code?: string;
  };
}
// Navigation Event Types (extensions beyond architecture)
export interface NavigateEvent {
  type: 'navigate';
  data: {
    botId: string;
    direction: 'up' | 'down' | 'left' | 'right' | 'root';
  };
}
export interface NavigateToNodeEvent {
  type: 'navigate_to_node';
  data: {
    botId: string;
    nodeId: string;
  };
}
export interface NavigationResponseEvent {
  type: 'navigation_response';
  data: {
    botId: string;
    conversationTree: Record<string, ConversationNode>;
    currentNodeId: string;
    success: boolean;
    message?: string;
  };
}
// Union types for WebSocket events
export type WebSocketEvent = 
  | SendMessageEvent 
  | GetBotStateEvent
  | NavigateEvent
  | NavigateToNodeEvent;
export type WebSocketResponse = 
  | BotResponseEvent 
  | ToolUpdateEvent 
  | BotThinkingEvent
  | ErrorEvent
  | NavigationResponseEvent;
// Component Props Types
export interface AppProps {}
export interface ChatInterfaceProps {
  botId: string;
}
export interface MessageListProps {
  messages: Message[];
  isThinking: boolean;
}
export interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled: boolean;
}
// Store Types
export interface BotStore {
  // State
  bots: Record<string, BotState>;
  currentBotId: string | null;
  connected: boolean;
  systemMessages: Array<{
    id: string;
    content: string;
    timestamp: string;
  }>;
  showHelp: boolean;
  // Actions
  sendMessage: (botId: string, content: string) => void;
  setBotState: (botState: BotState) => void;
  setConnected: (connected: boolean) => void;
  navigate: (botId: string, direction: 'up' | 'down' | 'left' | 'right' | 'root') => void;
  navigateToNode: (botId: string, nodeId: string) => void;
  addSystemMessage: (message: string) => void;
  setShowHelp: (show: boolean) => void;
  // WebSocket management
  connect: () => void;
  disconnect: () => void;
}
// Validation helper types
export type ValidationResult = {
  isValid: boolean;
  errors: string[];
};