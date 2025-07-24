/**
 * Shared State Management for Bot Visualizer
 * 
 * Centralized state store using Pinia for managing bot data, conversation trees,
 * and functional prompts across all visualization components.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { connectWebSocket } from '../api/websocket.js'
import { WS_EVENTS } from '../api/interfaces.js'
import { realisticMockData } from '../mock-data/realistic-data.js'

export const useBotStore = defineStore('bot', () => {
    // ============================================================================
    // STATE
    // ============================================================================
    
    // Bot state
    const botState = ref(null)
    const connectionStatus = ref('disconnected') // 'disconnected', 'connecting', 'connected', 'error'
    
    // Conversation tree
    const conversationNodes = ref(new Map()) // Map<nodeId, ConversationNode>
    const rootNodeId = ref(null)
    const currentNodeId = ref(null)
    
    // Tools and metrics
    const availableTools = ref([])
    const toolUsageStats = ref({})
    const botMetrics = ref({
        totalMessages: 0,
        totalToolCalls: 0,
        averageResponseTime: 0,
        tokenUsage: 0,
        errorCount: 0
    })
    
    // Functional prompts
    const functionalPrompts = ref(new Map()) // Map<promptId, FunctionalPrompt>
    const activeFunctionalPrompt = ref(null)
    
    // WebSocket connection
    let wsConnection = null
    // Integration monitoring
    const integrationStatus = ref('healthy')
    const lastSyncTime = ref(null)

    
    // ============================================================================
    // GETTERS
    // ============================================================================
    
    const currentNode = computed(() => {
        return currentNodeId.value ? conversationNodes.value.get(currentNodeId.value) : null
    })
    
    const conversationTree = computed(() => {
        if (!rootNodeId.value) return null
        
        const buildTree = (nodeId) => {
            const node = conversationNodes.value.get(nodeId)
            if (!node) return null
            
            return {
                ...node,
                children: node.childIds.map(buildTree).filter(Boolean)
            }
        }
        
        return buildTree(rootNodeId.value)
    })
    
    const conversationPath = computed(() => {
        if (!currentNodeId.value) return []
        
        const path = []
        let nodeId = currentNodeId.value
        
        while (nodeId) {
            const node = conversationNodes.value.get(nodeId)
            if (!node) break
            path.unshift(node)
            nodeId = node.parentId
        }
        
        return path
    })
    
    // ============================================================================
    // ACTIONS
    // ============================================================================
    const loadRealisticData = () => {
        // Load realistic conversation data
        botState.value = realisticMockData.botState
        availableTools.value = realisticMockData.botState.availableTools
        toolUsageStats.value = realisticMockData.toolUsageStats
        botMetrics.value = realisticMockData.metrics
        
        // Load conversation nodes
        conversationNodes.value.clear()
        realisticMockData.conversationNodes.forEach(node => {
            conversationNodes.value.set(node.id, node)
        })
        
        rootNodeId.value = realisticMockData.rootNodeId
        currentNodeId.value = realisticMockData.rootNodeId
        
        console.log('📊 Loaded realistic bot data:', {
            totalNodes: conversationNodes.value.size,
            rootNode: rootNodeId.value,
            availableTools: availableTools.value.length
        })
    }
    
            // Load realistic data first
            loadRealisticData()
            
    
    const connect = async (botId = 'default') => {
        try {
            connectionStatus.value = 'connecting'
            
            wsConnection = await connectWebSocket()
            
            // Set up event listeners
            wsConnection.on(WS_EVENTS.BOT_STATE_UPDATE, handleBotStateUpdate)
            wsConnection.on(WS_EVENTS.NEW_MESSAGE, handleNewMessage)
            wsConnection.on(WS_EVENTS.TOOL_CALL_START, handleToolCallStart)
            wsConnection.on(WS_EVENTS.TOOL_CALL_COMPLETE, handleToolCallComplete)
            wsConnection.on(WS_EVENTS.CONVERSATION_BRANCH, handleConversationBranch)
            wsConnection.on(WS_EVENTS.FUNCTIONAL_PROMPT_UPDATE, handleFunctionalPromptUpdate)
            
            // Subscribe to bot updates
            wsConnection.emit(WS_EVENTS.SUBSCRIBE_BOT, { botId })
            
            connectionStatus.value = 'connected'
        } catch (error) {
            console.error('Failed to connect to bot system:', error)
            connectionStatus.value = 'error'
        }
    }
    
    const disconnect = () => {
        if (wsConnection) {
            wsConnection.disconnect()
            wsConnection = null
        }
        connectionStatus.value = 'disconnected'
    }
    
    const sendMessage = (content) => {
        if (wsConnection && connectionStatus.value === 'connected') {
            wsConnection.emit(WS_EVENTS.SEND_MESSAGE, {
                content,
                parentNodeId: currentNodeId.value
            })
        }
    }
    
    const navigateToNode = (nodeId) => {
        if (conversationNodes.value.has(nodeId)) {
            currentNodeId.value = nodeId
            if (wsConnection) {
                wsConnection.emit(WS_EVENTS.NAVIGATE_CONVERSATION, { nodeId })
            }
        }
    }
    
    const addConversationNode = (node) => {
        conversationNodes.value.set(node.id, node)
        
        // Update parent's children list
        if (node.parentId) {
            const parent = conversationNodes.value.get(node.parentId)
            if (parent && !parent.childIds.includes(node.id)) {
                parent.childIds.push(node.id)
            }
        } else {
            // This is a root node
            rootNodeId.value = node.id
        }
    }
    
    const updateToolUsageStats = (toolName) => {
        toolUsageStats.value[toolName] = (toolUsageStats.value[toolName] || 0) + 1
        botMetrics.value.totalToolCalls++
    }
    const updateIntegrationStatus = (status) => {
        integrationStatus.value = status
        lastSyncTime.value = new Date().toISOString()
    }

    const getIntegrationHealth = () => {
        return {
            status: integrationStatus.value,
            lastSync: lastSyncTime.value,
            nodeCount: conversationNodes.value.size,
            hasActiveConnection: connectionStatus.value === 'connected',
            toolCount: availableTools.value.length
        }
    }

    
    // ============================================================================
    // EVENT HANDLERS
    // ============================================================================
    
    const handleBotStateUpdate = (data) => {
        botState.value = data.botState
        availableTools.value = data.botState.availableTools || []
        if (data.botState.metrics) {
            botMetrics.value = { ...botMetrics.value, ...data.botState.metrics }
        }
    }
    
    const handleNewMessage = (data) => {
        addConversationNode(data.node)
        currentNodeId.value = data.node.id
        botMetrics.value.totalMessages++
    }
    
    const handleToolCallStart = (data) => {
        // Update the node with tool call information
        const node = conversationNodes.value.get(data.nodeId)
        if (node) {
            node.toolCalls = node.toolCalls || []
            node.toolCalls.push(data.toolCall)
        }
    }
    
    const handleToolCallComplete = (data) => {
        // Update the node with tool result
        const node = conversationNodes.value.get(data.nodeId)
        if (node) {
            node.toolResults = node.toolResults || []
            node.toolResults.push(data.toolResult)
            updateToolUsageStats(data.toolResult.toolName)
        }
    }
    
    const handleConversationBranch = (data) => {
        // Handle conversation branching
        addConversationNode(data.newBranch)
    }
    
    const handleFunctionalPromptUpdate = (data) => {
        functionalPrompts.value.set(data.prompt.id, data.prompt)
        if (data.isActive) {
            activeFunctionalPrompt.value = data.prompt
        }
    }
    
    // ============================================================================
    // RETURN PUBLIC API
    // ============================================================================
    
    return {
        // State
        botState,
        connectionStatus,
        conversationNodes,
        currentNodeId,
        availableTools,
        toolUsageStats,
        botMetrics,
        functionalPrompts,
        activeFunctionalPrompt,
        
        // Getters
        currentNode,
        conversationTree,
        conversationPath,
        
        // Actions
        connect,
        disconnect,
        loadRealisticData,
        sendMessage,
        navigateToNode,
        addConversationNode,
        updateToolUsageStats,
        updateIntegrationStatus,
        getIntegrationHealth,

        // Integration monitoring
        integrationStatus,
        lastSyncTime
    }
})
