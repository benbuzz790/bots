/**
 * Bot File Parser for Realistic Test Data
 * 
 * Parses actual .bot files to extract conversation trees and create
 * realistic mock data for the visualizer components.
 */

/**
 * Parse a bot file conversation tree into our standardized format
 * @param {Object} botData - Raw bot file data
 * @returns {Object} Parsed bot data with conversation nodes
 */
export const parseBotFile = (botData) => {
    const nodes = new Map()
    let nodeCounter = 1
    
    // Extract bot metadata
    const botState = {
        id: botData.name || 'parsed-bot',
        name: botData.name || 'Parsed Bot',
        engine: botData.model_engine || 'claude-3-5-sonnet',
        parameters: {
            temperature: botData.temperature || 0.7,
            max_tokens: botData.max_tokens || 4000,
            role: botData.role || 'assistant',
            role_description: botData.role_description || 'AI assistant'
        },
        availableTools: extractToolsFromConversation(botData.conversation),
        status: 'idle'
    }
    
    // Parse conversation tree recursively
    const parseNode = (node, parentId = null, depth = 0) => {
        const nodeId = `node-${nodeCounter++}`
        const timestamp = new Date(Date.now() - (nodeCounter * 60000)).toISOString() // Simulate timestamps
        
        // Extract tool calls and results
        const toolCalls = (node.tool_calls || []).map((call, index) => ({
            id: call.id || `call-${nodeId}-${index}`,
            name: call.name || call.function?.name || 'unknown_tool',
            parameters: call.input || call.function?.arguments || {},
            timestamp: timestamp
        }))
        
        const toolResults = (node.tool_results || []).map((result, index) => ({
            callId: result.tool_use_id || `call-${nodeId}-${index}`,
            result: typeof result.content === 'string' ? result.content : JSON.stringify(result.content),
            success: !result.content?.includes('Error'),
            executionTime: Math.floor(Math.random() * 2000) + 100, // Simulate execution time
            timestamp: new Date(new Date(timestamp).getTime() + 1000).toISOString()
        }))
        
        // Create standardized node
        const parsedNode = {
            id: nodeId,
            role: node.role || 'unknown',
            content: node.content || '',
            timestamp: timestamp,
            parentId: parentId,
            childIds: [],
            toolCalls: toolCalls,
            toolResults: toolResults,
            metadata: {
                depth: depth,
                nodeClass: node.node_class || 'ConversationNode',
                hasTools: toolCalls.length > 0 || toolResults.length > 0
            }
        }
        
        nodes.set(nodeId, parsedNode)
        
        // Process child nodes
        if (node.replies && node.replies.length > 0) {
            for (const reply of node.replies) {
                const childId = parseNode(reply, nodeId, depth + 1)
                parsedNode.childIds.push(childId)
            }
        }
        
        return nodeId
    }
    
    // Start parsing from root (skip empty root if present)
    let rootNodeId = null
    if (botData.conversation) {
        if (botData.conversation.role === 'empty' && botData.conversation.replies) {
            // Skip empty root, start with first real conversation
            for (const reply of botData.conversation.replies) {
                rootNodeId = parseNode(reply, null, 0)
                break // Take first conversation thread
            }
        } else {
            rootNodeId = parseNode(botData.conversation, null, 0)
        }
    }
    
    return {
        botState,
        conversationNodes: Array.from(nodes.values()),
        rootNodeId,
        toolUsageStats: calculateToolUsage(nodes),
        metrics: calculateMetrics(nodes)
    }
}

const extractToolsFromConversation = (conversation) => {
    const tools = new Set()
    
    const extractFromNode = (node) => {
        if (node.tool_calls) {
            node.tool_calls.forEach(call => {
                tools.add(call.name || call.function?.name || 'unknown_tool')
            })
        }
        if (node.replies) {
            node.replies.forEach(extractFromNode)
        }
    }
    
    extractFromNode(conversation)
    return Array.from(tools)
}

const calculateToolUsage = (nodes) => {
    const usage = {}
    for (const node of nodes.values()) {
        for (const toolCall of node.toolCalls) {
            usage[toolCall.name] = (usage[toolCall.name] || 0) + 1
        }
    }
    return usage
}

const calculateMetrics = (nodes) => {
    const nodeArray = Array.from(nodes.values())
    const totalMessages = nodeArray.length
    const totalToolCalls = nodeArray.reduce((sum, node) => sum + node.toolCalls.length, 0)
    const toolResults = nodeArray.flatMap(node => node.toolResults)
    const averageResponseTime = toolResults.length > 0 
        ? toolResults.reduce((sum, result) => sum + result.executionTime, 0) / toolResults.length 
        : 0
    const errorCount = toolResults.filter(result => !result.success).length
    
    return {
        totalMessages,
        totalToolCalls,
        averageResponseTime: Math.round(averageResponseTime),
        tokenUsage: totalMessages * 150, // Rough estimate
        errorCount
    }
}
