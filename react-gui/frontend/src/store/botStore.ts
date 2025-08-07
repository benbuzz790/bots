import { create } from 'zustand';
import { WebSocketService } from '../services/websocket';
import type { BotState } from '../types';
interface SystemMessage {
  id: string;
  timestamp: string;
  content: string;
}
interface BotStore {
  bots: Record<string, BotState>;
  currentBotId: string | null;
  connected: boolean;
  thinking: boolean;
  error: string | null;
  systemMessages: SystemMessage[];
  showHelp: boolean;
  wsService: WebSocketService | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  createBot: (name?: string) => Promise<string>;
  sendMessage: (botId: string, content: string) => Promise<void>;
  setBotState: (botState: BotState) => void;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;
  navigate: (botId: string, direction: string) => void;
  navigateToNode: (botId: string, nodeId: string) => void;
  addSystemMessage: (message: string) => void;
  setShowHelp: (show: boolean) => void;
}
export const useBotStore = create<BotStore>((set, get) => ({
  bots: {},
  currentBotId: null,
  connected: false,
  thinking: false,
  error: null,
  systemMessages: [],
  showHelp: false,
  wsService: null,
  connect: async () => {
    const wsUrl = 'ws://127.0.0.1:8000/ws';
    const wsService = new WebSocketService(wsUrl);
    // Set up event handlers
    wsService.on('bot_response', (data) => {
      try {
        if (!data || typeof data !== 'object') {
          console.error('Invalid bot_response data:', data);
          return;
        }
        const { botId, botState } = data;
        console.log('🤖 bot_response received:', data);
        console.log('🤖 Extracted:', { botId, botState: !!botState, reactFlowData: !!data.reactFlowData });
        if (botState && typeof botState === 'object') {
          // Add React Flow data to bot state if available
          if (data.reactFlowData) {
            botState.reactFlowData = data.reactFlowData;
            console.log('🌳 React Flow data added to bot state:', data.reactFlowData.nodes?.length, 'nodes');
          }
          console.log('🤖 Calling setBotState with:', botState);
          get().setBotState(botState);
          set({ thinking: false, error: null });
          console.log('🤖 Bot state updated successfully');
        }
      } catch (error) {
        console.error('Error handling bot_response:', error);
      }
    });
    wsService.on('bot_thinking', (data) => {
      const { thinking } = data;
      set({ thinking: thinking || false });
    });
    wsService.on('error', (data) => {
      const { message } = data;
      set({ error: message || 'Unknown error', thinking: false });
      console.error('WebSocket error:', message);
    });
    wsService.on('navigation_response', (data) => {
      try {
        const { botId, botState, success } = data;
        if (success && botState) {
          console.log('🧭 Navigation response received:', { botId, success });
          get().setBotState(botState);
        }
      } catch (error) {
        console.error('Error handling navigation_response:', error);
      }
    });

    wsService.on('tool_update', (data) => {
      console.log('Tool update:', data);
    });
    try {
      await wsService.connect();
      set({ wsService, connected: true, error: null });
    } catch (error) {
      set({ error: 'Connection failed' });
    }
  },
  disconnect: () => {
    const { wsService } = get();
    if (wsService) wsService.disconnect();
    set({ wsService: null, connected: false });
  },
  createBot: async (name = 'Default Bot') => {
    try {
      // Call the backend REST API to create the bot
      const response = await fetch('http://127.0.0.1:8000/api/bots/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(`Failed to create bot: ${response.statusText}`);
      }
      const result = await response.json();
      const botId = result.bot_id;
      // Create initial bot state
      const initialBotState = {
        id: botId,
        name: result.name,
        conversationTree: {},
        currentNodeId: '',
        isConnected: true,
        isThinking: false
      };
      get().setBotState(initialBotState);
      // Set the current bot ID
      set({ currentBotId: botId, error: null });
      console.log(`Created bot: ${botId} (${name})`);
      return botId;
    } catch (error) {
      set({ error: `Failed to create bot: ${error instanceof Error ? error.message : 'Unknown error'}` });
      throw error;
    }
  },
  sendMessage: async (botId: string, content: string) => {
    const { wsService } = get();
    console.log('botStore sendMessage called:', { botId, content, wsService: !!wsService });
    console.log('Sending WebSocket message...');
    if (wsService) {
      // Immediately add user message to conversation tree
      const state = get();
      const bot = state.bots[botId];
      if (bot) {
        const userMessageId = Date.now().toString() + '_user';
        const userMessage = {
          id: userMessageId,
          role: 'user' as const,
          content: content,
          timestamp: new Date().toISOString(),
          toolCalls: []
        };
        
        const userNode = {
          id: userMessageId,
          message: userMessage,
          parent: bot.currentNodeId || undefined,
          children: [],
          isCurrent: true
        };
        
        // Update bot state with new user message
        const updatedConversationTree = { ...bot.conversationTree, [userMessageId]: userNode };
        get().setBotState({ ...bot, conversationTree: updatedConversationTree, currentNodeId: userMessageId });
      }
      
      set({ thinking: true });
      wsService.sendMessage('send_message', { botId, content });
    }
  },
  setBotState: (botState: BotState) => {
    // Ensure all required properties are present
    console.log('🔄 setBotState called with:', { id: botState.id, hasConversationTree: !!botState.conversationTree });
    console.log('🔄 Current bots before update:', Object.keys(get().bots));
    const completeState = {
      ...botState,
      isConnected: botState.isConnected ?? true,
      isThinking: botState.isThinking ?? false
    };
    set((state) => ({ bots: { ...state.bots, [botState.id]: completeState } }));
    console.log('🔄 Current bots after update:', Object.keys(get().bots));
    console.log('🔄 Updated bot state:', { id: completeState.id, messageCount: Object.keys(completeState.conversationTree || {}).length });
  },
  setConnected: (connected: boolean) => set({ connected }),
  setError: (error: string | null) => set({ error }),
  navigate: (botId: string, direction: string) => {
    const { wsService } = get();
    if (wsService) {
      console.log('🧭 Sending navigation:', { botId, direction });
      wsService.sendMessage('navigate', { botId, direction });
    } else {
      console.error('WebSocket not connected for navigation');
    }
  },
  navigateToNode: (botId: string, nodeId: string) => {
    const { wsService } = get();
    if (wsService) {
      console.log('🧭 Sending navigate to node:', { botId, nodeId });
      wsService.sendMessage('navigate_to_node', { botId, nodeId });
    } else {
      console.error('WebSocket not connected for node navigation');
    }
  },
  addSystemMessage: (message: string) => {
    const msg = { id: Date.now().toString(), timestamp: new Date().toISOString(), content: message };
    set((state) => ({ systemMessages: [...state.systemMessages, msg] }));
  },
  setShowHelp: (show: boolean) => set({ showHelp: show })
}));