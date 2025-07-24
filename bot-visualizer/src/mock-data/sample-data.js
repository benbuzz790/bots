/**
 * Mock Data for Bot Visualizer Development
 * 
 * Provides realistic sample data for testing all visualization components
 * without requiring a live bot system connection.
 */

export const mockBotState = {
    id: 'dev-bot-001',
    name: 'Development Bot',
    engine: 'claude-3-5-sonnet-20241022',
    parameters: {
        temperature: 0.7,
        max_tokens: 4000,
        top_p: 1.0
    },
    availableTools: [
        'python_edit',
        'view',
        'execute_powershell',
        'patch_edit',
        'branch_self',
        'add_tools'
    ],
    currentNode: 'node-005',
    metrics: {
        totalMessages: 12,
        totalToolCalls: 8,
        averageResponseTime: 1250,
        tokenUsage: 15420,
        errorCount: 1
    },
    status: 'idle'
}

export const mockConversationNodes = [
    {
        id: 'node-001',
        role: 'user',
        content: 'Hi Claude. I\'d like to make a visualizer for what I\'m calling a \'bot\'. Please take a look at the main files in this repo and pitch a few specific ideas for a good visual wrapper.',
        timestamp: '2025-01-23T23:00:00.000Z',
        parentId: null,
        childIds: ['node-002'],
        toolCalls: [],
        toolResults: [],
        metadata: {}
    },
    {
        id: 'node-002',
        role: 'assistant',
        content: 'I\'ll explore the repository structure and examine the main files to understand what kind of "bot" you\'re working with, then suggest some specific visualization ideas.',
        timestamp: '2025-01-23T23:00:15.000Z',
        parentId: 'node-001',
        childIds: ['node-003'],
        toolCalls: [
            {
                id: 'call-001',
                name: 'view_dir',
                parameters: {
                    start_path: '.',
                    target_extensions: "['py', 'md', 'txt', 'json', 'yaml', 'yml', 'toml']"
                },
                timestamp: '2025-01-23T23:00:16.000Z'
            }
        ],
        toolResults: [
            {
                callId: 'call-001',
                result: './\n    cli_config.json\n    CONTRIBUTING.md\n    credentials.json\n    ...',
                success: true,
                executionTime: 45,
                timestamp: '2025-01-23T23:00:16.045Z'
            }
        ],
        metadata: {}
    },
    {
        id: 'node-003',
        role: 'user',
        content: 'ok',
        timestamp: '2025-01-23T23:01:00.000Z',
        parentId: 'node-002',
        childIds: ['node-004', 'node-006'], // Branch point
        toolCalls: [],
        toolResults: [],
        metadata: {}
    },
    {
        id: 'node-004',
        role: 'assistant',
        content: 'Based on my analysis of your bot repository, I can see you have a sophisticated agentic programming framework. Here are several specific visualization ideas...',
        timestamp: '2025-01-23T23:01:30.000Z',
        parentId: 'node-003',
        childIds: ['node-005'],
        toolCalls: [],
        toolResults: [],
        metadata: { branch: 'main' }
    },
    {
        id: 'node-005',
        role: 'user',
        content: 'I think we only want to pursue items 1, 2, and 3. Let\'s talk about how you should approach this using branch_self.',
        timestamp: '2025-01-23T23:02:00.000Z',
        parentId: 'node-004',
        childIds: [],
        toolCalls: [],
        toolResults: [],
        metadata: { branch: 'main' }
    },
    {
        id: 'node-006',
        role: 'assistant',
        content: 'Alternative approach: Let me focus on the technical architecture first...',
        timestamp: '2025-01-23T23:01:35.000Z',
        parentId: 'node-003',
        childIds: [],
        toolCalls: [
            {
                id: 'call-002',
                name: 'python_view',
                parameters: {
                    target_scope: 'bots/foundation/base.py'
                },
                timestamp: '2025-01-23T23:01:36.000Z'
            }
        ],
        toolResults: [
            {
                callId: 'call-002',
                result: 'Core foundation classes for the bots framework...',
                success: true,
                executionTime: 120,
                timestamp: '2025-01-23T23:01:36.120Z'
            }
        ],
        metadata: { branch: 'alternative' }
    }
]

export const mockToolUsageStats = {
    'python_edit': 3,
    'view': 2,
    'execute_powershell': 1,
    'patch_edit': 2,
    'branch_self': 0,
    'add_tools': 0
}

export const mockFunctionalPrompts = [
    {
        id: 'fp-001',
        name: 'Setup → Parallel → Wrap-up',
        type: 'sequential_parallel',
        nodes: [
            {
                id: 'setup-node',
                type: 'prompt',
                config: {
                    content: 'SETUP PHASE: Create technical foundation...'
                },
                position: { x: 100, y: 100 }
            },
            {
                id: 'parallel-branch-1',
                type: 'branch',
                config: {
                    content: 'PARALLEL PHASE - Conversation Tree Visualizer...'
                },
                position: { x: 300, y: 50 }
            },
            {
                id: 'parallel-branch-2',
                type: 'branch',
                config: {
                    content: 'PARALLEL PHASE - Bot Dashboard...'
                },
                position: { x: 300, y: 100 }
            },
            {
                id: 'parallel-branch-3',
                type: 'branch',
                config: {
                    content: 'PARALLEL PHASE - Functional Prompt Flow Designer...'
                },
                position: { x: 300, y: 150 }
            },
            {
                id: 'wrapup-node',
                type: 'merge',
                config: {
                    content: 'WRAP-UP PHASE: Integrate all components...'
                },
                position: { x: 500, y: 100 }
            }
        ],
        edges: [
            { id: 'edge-1', sourceId: 'setup-node', targetId: 'parallel-branch-1', type: 'sequence' },
            { id: 'edge-2', sourceId: 'setup-node', targetId: 'parallel-branch-2', type: 'sequence' },
            { id: 'edge-3', sourceId: 'setup-node', targetId: 'parallel-branch-3', type: 'sequence' },
            { id: 'edge-4', sourceId: 'parallel-branch-1', targetId: 'wrapup-node', type: 'sequence' },
            { id: 'edge-5', sourceId: 'parallel-branch-2', targetId: 'wrapup-node', type: 'sequence' },
            { id: 'edge-6', sourceId: 'parallel-branch-3', targetId: 'wrapup-node', type: 'sequence' }
        ],
        parameters: {
            allow_work: true,
            parallel: false,
            recombine: 'concatenate'
        },
        status: 'running'
    }
]

// Helper function to build conversation tree from flat nodes
export const buildConversationTree = (nodes) => {
    const nodeMap = new Map(nodes.map(node => [node.id, { ...node, children: [] }]))
    let root = null
    
    for (const node of nodeMap.values()) {
        if (node.parentId) {
            const parent = nodeMap.get(node.parentId)
            if (parent) {
                parent.children.push(node)
            }
        } else {
            root = node
        }
    }
    
    return root
}

export const mockConversationTree = buildConversationTree(mockConversationNodes)
