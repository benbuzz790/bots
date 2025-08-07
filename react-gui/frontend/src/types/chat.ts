// Re-export from index.ts for compatibility
export { Message, BotState, ConversationNode, ToolCall } from './index';

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}