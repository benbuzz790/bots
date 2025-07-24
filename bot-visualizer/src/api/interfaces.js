/**
 * API Interface Specifications for Bot Visualizer
 * 
 * This file defines the data contracts between the bot system and visualizations.
 * All parallel development branches should use these interfaces.
 */

// ============================================================================
// CORE DATA MODELS
// ============================================================================

/**
 * ConversationNode - Represents a single node in the conversation tree
 * @typedef {Object} ConversationNode
 * @property {string} id - Unique identifier for the node
 * @property {string} role - 'user', 'assistant', 'system', 'tool'
 * @property {string} content - The message content
 * @property {string} timestamp - ISO timestamp of creation
 * @property {string|null} parentId - ID of parent node (null for root)
 * @property {string[]} childIds - Array of child node IDs
 * @property {ToolCall[]} toolCalls - Tools invoked in this message
 * @property {ToolResult[]} toolResults - Results from tool executions
 * @property {Object} metadata - Additional node metadata
 */

/**
 * ToolCall - Represents a tool invocation
 * @typedef {Object} ToolCall
 * @property {string} id - Unique call identifier
 * @property {string} name - Tool function name
 * @property {Object} parameters - Tool parameters
 * @property {string} timestamp - When the call was made
 */

/**
 * ToolResult - Represents a tool execution result
 * @typedef {Object} ToolResult
 * @property {string} callId - Corresponding tool call ID
 * @property {string} result - Tool execution result
 * @property {boolean} success - Whether execution succeeded
 * @property {number} executionTime - Time taken in milliseconds
 * @property {string} timestamp - When result was received
 */

/**
 * BotState - Current state of a bot instance
 * @typedef {Object} BotState
 * @property {string} id - Bot instance ID
 * @property {string} name - Bot display name
 * @property {string} engine - Model engine (e.g., 'claude-3-5-sonnet')
 * @property {Object} parameters - Model parameters (temperature, max_tokens, etc.)
 * @property {string[]} availableTools - List of available tool names
 * @property {ConversationNode} currentNode - Current conversation position
 * @property {BotMetrics} metrics - Performance metrics
 * @property {string} status - 'idle', 'thinking', 'executing_tool', 'error'
 */

/**
 * BotMetrics - Performance and usage metrics
 * @typedef {Object} BotMetrics
 * @property {number} totalMessages - Total messages processed
 * @property {number} totalToolCalls - Total tool invocations
 * @property {number} averageResponseTime - Average response time in ms
 * @property {number} tokenUsage - Total tokens consumed
 * @property {Object} toolUsageStats - Usage count per tool
 * @property {number} errorCount - Number of errors encountered
 */

/**
 * FunctionalPrompt - Represents a functional prompt workflow
 * @typedef {Object} FunctionalPrompt
 * @property {string} id - Unique identifier
 * @property {string} name - Display name
 * @property {string} type - 'chain', 'branch', 'prompt_while', etc.
 * @property {FunctionalPromptNode[]} nodes - Workflow nodes
 * @property {FunctionalPromptEdge[]} edges - Connections between nodes
 * @property {Object} parameters - Workflow parameters
 * @property {string} status - 'draft', 'running', 'completed', 'error'
 */

/**
 * FunctionalPromptNode - A node in a functional prompt workflow
 * @typedef {Object} FunctionalPromptNode
 * @property {string} id - Node identifier
 * @property {string} type - 'prompt', 'condition', 'tool', 'branch', 'merge'
 * @property {Object} config - Node-specific configuration
 * @property {Object} position - {x, y} coordinates for visualization
 */

/**
 * FunctionalPromptEdge - Connection between workflow nodes
 * @typedef {Object} FunctionalPromptEdge
 * @property {string} id - Edge identifier
 * @property {string} sourceId - Source node ID
 * @property {string} targetId - Target node ID
 * @property {string} type - 'sequence', 'condition', 'parallel'
 */

// ============================================================================
// API ENDPOINTS
// ============================================================================

export const API_ENDPOINTS = {
    // WebSocket connection for real-time updates
    WEBSOCKET: '/ws',
    
    // REST endpoints
    BOT_STATE: '/api/bot/state',
    CONVERSATION_TREE: '/api/conversation/tree',
    CONVERSATION_NODE: '/api/conversation/node/:id',
    TOOL_USAGE: '/api/tools/usage',
    FUNCTIONAL_PROMPTS: '/api/functional-prompts',
    METRICS: '/api/metrics'
};

// ============================================================================
// WEBSOCKET EVENTS
// ============================================================================

export const WS_EVENTS = {
    // Incoming events from bot system
    BOT_STATE_UPDATE: 'bot_state_update',
    NEW_MESSAGE: 'new_message',
    TOOL_CALL_START: 'tool_call_start',
    TOOL_CALL_COMPLETE: 'tool_call_complete',
    CONVERSATION_BRANCH: 'conversation_branch',
    FUNCTIONAL_PROMPT_UPDATE: 'functional_prompt_update',
    
    // Outgoing events to bot system
    SUBSCRIBE_BOT: 'subscribe_bot',
    SEND_MESSAGE: 'send_message',
    NAVIGATE_CONVERSATION: 'navigate_conversation',
    EXECUTE_FUNCTIONAL_PROMPT: 'execute_functional_prompt'
};
