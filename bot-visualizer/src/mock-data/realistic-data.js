/**
 * Realistic Mock Data from Actual Bot File
 * 
 * This file contains realistic conversation data extracted from gui-test.bot
 * to provide more authentic testing scenarios for the visualizer.
 */

import { parseBotFile } from './bot-parser.js'

// Realistic bot file data (subset of gui-test.bot for development)
const realisticBotData = {
    "name": "GUI Test Bot",
    "model_engine": "claude-sonnet-4-20250514",
    "max_tokens": 32000,
    "temperature": 0.3,
    "role": "assistant",
    "role_description": "a friendly AI assistant helping with bot visualization",
    "conversation": {
        "content": "",
        "role": "empty",
        "replies": [
            {
                "content": "Hi Claude. I'd like to make a visualizer for what I'm calling a 'bot'. Please take a look at the main files in this repo and pitch a few specific ideas for a good visual wrapper.",
                "role": "user",
                "tool_calls": [],
                "tool_results": [],
                "replies": [
                    {
                        "content": "I'll explore the repository structure and examine the main files to understand what kind of \"bot\" you're working with, then suggest some specific visualization ideas.",
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "type": "tool_use",
                                "id": "toolu_019m8Ynw4taMjMq8pJengDrq",
                                "name": "view_dir",
                                "input": {
                                    "start_path": ".",
                                    "target_extensions": "['py', 'md', 'txt', 'json', 'yaml', 'yml', 'toml']"
                                }
                            }
                        ],
                        "tool_results": [],
                        "replies": [
                            {
                                "content": "ok",
                                "role": "user",
                                "tool_calls": [],
                                "tool_results": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": "toolu_019m8Ynw4taMjMq8pJengDrq",
                                        "content": "./\n    cli_config.json\n    CONTRIBUTING.md\n    credentials.json\n    functional_prompt_primer.md\n    installation_quickstart.md\n    large_refactor_tasks.md\n    LICENSE.txt\n    pyproject.toml\n    README.md\n    requirements.txt\n    setup.py\n    test_functions.py\n    botlib/\n        build_debug_bot.py\n        build_py_file_bot.py\n        __init__.py\n    bots/\n        __init__.py\n        dev/\n            cli.py\n            decorators.py\n        flows/\n            functional_prompts.py\n            project_tree.py\n        foundation/\n            anthropic_bots.py\n            base.py\n            openai_bots.py\n        tools/\n            code_tools.py\n            meta_tools.py\n            python_editing_tools.py\n            self_tools.py\n            terminal_tools.py"
                                    }
                                ],
                                "replies": [
                                    {
                                        "content": "Based on my analysis of your bot repository, I can see you have a sophisticated agentic programming framework. Here are several specific visualization ideas for your bot system:",
                                        "role": "assistant",
                                        "tool_calls": [],
                                        "tool_results": [],
                                        "replies": [
                                            {
                                                "content": "I think we only want to pursue items 1, 2, and 3. Let's talk about how you should approach this using branch_self.",
                                                "role": "user",
                                                "tool_calls": [],
                                                "tool_results": [],
                                                "replies": [
                                                    {
                                                        "content": "Perfect! I understand you want to focus on the three core visualizations and use branch_self for implementation. Let me break down the approach:",
                                                        "role": "assistant",
                                                        "tool_calls": [
                                                            {
                                                                "type": "tool_use",
                                                                "id": "toolu_01BranchSelf123",
                                                                "name": "branch_self",
                                                                "input": {
                                                                    "self_prompts": "[\"SETUP PHASE: Create technical foundation and interface specifications\", \"PARALLEL PHASE - Conversation Tree Visualizer: Implement interactive tree visualization\", \"PARALLEL PHASE - Bot Dashboard: Implement real-time monitoring dashboard\", \"PARALLEL PHASE - Functional Prompt Flow Designer: Implement visual workflow builder\", \"WRAP-UP PHASE: Integrate all components into cohesive application\"]",
                                                                    "allow_work": "True",
                                                                    "parallel": "False",
                                                                    "recombine": "concatenate"
                                                                }
                                                            }
                                                        ],
                                                        "tool_results": [],
                                                        "replies": [
                                                            {
                                                                "content": "Excellent! The branch_self approach will allow us to maximize parallelization. Let me proceed with the implementation.",
                                                                "role": "user",
                                                                "tool_calls": [],
                                                                "tool_results": [
                                                                    {
                                                                        "type": "tool_result",
                                                                        "tool_use_id": "toolu_01BranchSelf123",
                                                                        "content": "Branching in progress..."
                                                                    }
                                                                ],
                                                                "replies": [
                                                                    {
                                                                        "content": "SETUP PHASE: I'll establish the technical foundation for the bot visualization suite...",
                                                                        "role": "assistant",
                                                                        "tool_calls": [
                                                                            {
                                                                                "type": "tool_use",
                                                                                "id": "toolu_01SetupPhase",
                                                                                "name": "execute_powershell",
                                                                                "input": {
                                                                                    "command": "mkdir bot-visualizer"
                                                                                }
                                                                            }
                                                                        ],
                                                                        "tool_results": [],
                                                                        "replies": []
                                                                    }
                                                                ]
                                                            }
                                                        ]
                                                    }
                                                ]
                                            },
                                            {
                                                "content": "Actually, let me first examine the functional prompts system more closely to understand the workflow patterns.",
                                                "role": "assistant",
                                                "tool_calls": [
                                                    {
                                                        "type": "tool_use",
                                                        "id": "toolu_01ExamineFP",
                                                        "name": "python_view",
                                                        "input": {
                                                            "target_scope": "bots/flows/functional_prompts.py",
                                                            "max_lines": "100"
                                                        }
                                                    }
                                                ],
                                                "tool_results": [],
                                                "replies": [
                                                    {
                                                        "content": "ok",
                                                        "role": "user",
                                                        "tool_calls": [],
                                                        "tool_results": [
                                                            {
                                                                "type": "tool_result",
                                                                "tool_use_id": "toolu_01ExamineFP",
                                                                "content": "\"\"\"Functional patterns for structured bot interactions and complex reasoning.\n\nThis module provides a collection of higher-level functions for orchestrating\ninteractions in common patterns like chains, branches, and trees. These patterns\nenable sophisticated reasoning approaches while maintaining clear structure and\nreproducibility.\n\nKey Features:\n- Sequential Processing:\n    - chain(): Execute prompts in sequence\n    - chain_while(): Chain with iteration until condition met\n    - prompt_while(): Single prompt with iteration\n\n- Parallel Exploration:\n    - branch(): Explore multiple paths independently\n    - branch_while(): Branch with iteration\n    - par_branch(): Parallel version of branch()\n    - par_branch_while(): Parallel version of branch_while()\n\n- Advanced Reasoning:\n    - tree_of_thought(): Branch, explore, then synthesize\n    - prompt_for(): Dynamic prompts from data\n    - par_dispatch(): Compare multiple bots\n\"\"\""
                                                            }
                                                        ],
                                                        "replies": []
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}

// Parse the realistic bot data
export const realisticMockData = parseBotFile(realisticBotData)

// Export individual components for easy access
export const {
    botState: realisticBotState,
    conversationNodes: realisticConversationNodes,
    rootNodeId: realisticRootNodeId,
    toolUsageStats: realisticToolUsageStats,
    metrics: realisticMetrics
} = realisticMockData

// Build conversation tree structure
export const buildRealisticConversationTree = () => {
    const nodeMap = new Map(realisticConversationNodes.map(node => [node.id, { ...node, children: [] }]))
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

export const realisticConversationTree = buildRealisticConversationTree()

// Enhanced functional prompt examples based on the actual bot usage
export const realisticFunctionalPrompts = [
    {
        id: 'fp-real-001',
        name: 'Bot Visualizer Development Workflow',
        type: 'setup_parallel_wrapup',
        nodes: [
            {
                id: 'setup-foundation',
                type: 'prompt',
                config: {
                    content: 'SETUP PHASE: Create technical foundation and interface specifications for the bot visualization suite...'
                },
                position: { x: 100, y: 200 }
            },
            {
                id: 'parallel-tree',
                type: 'branch',
                config: {
                    content: 'PARALLEL PHASE - Conversation Tree Visualizer: Implement interactive tree visualization...'
                },
                position: { x: 400, y: 100 }
            },
            {
                id: 'parallel-dashboard',
                type: 'branch',
                config: {
                    content: 'PARALLEL PHASE - Bot Dashboard: Implement real-time monitoring dashboard...'
                },
                position: { x: 400, y: 200 }
            },
            {
                id: 'parallel-flow',
                type: 'branch',
                config: {
                    content: 'PARALLEL PHASE - Functional Prompt Flow Designer: Implement visual workflow builder...'
                },
                position: { x: 400, y: 300 }
            },
            {
                id: 'wrapup-integration',
                type: 'merge',
                config: {
                    content: 'WRAP-UP PHASE: Integrate all components into cohesive application...'
                },
                position: { x: 700, y: 200 }
            }
        ],
        edges: [
            { id: 'edge-setup-tree', sourceId: 'setup-foundation', targetId: 'parallel-tree', type: 'sequence' },
            { id: 'edge-setup-dashboard', sourceId: 'setup-foundation', targetId: 'parallel-dashboard', type: 'sequence' },
            { id: 'edge-setup-flow', sourceId: 'setup-foundation', targetId: 'parallel-flow', type: 'sequence' },
            { id: 'edge-tree-wrapup', sourceId: 'parallel-tree', targetId: 'wrapup-integration', type: 'sequence' },
            { id: 'edge-dashboard-wrapup', sourceId: 'parallel-dashboard', targetId: 'wrapup-integration', type: 'sequence' },
            { id: 'edge-flow-wrapup', sourceId: 'parallel-flow', targetId: 'wrapup-integration', type: 'sequence' }
        ],
        parameters: {
            allow_work: true,
            parallel: false,
            recombine: 'concatenate'
        },
        status: 'completed'
    }
]

console.log('📊 Realistic mock data loaded:', {
    totalNodes: realisticConversationNodes.length,
    totalTools: realisticBotState.availableTools.length,
    totalToolCalls: realisticMetrics.totalToolCalls,
    conversationDepth: Math.max(...realisticConversationNodes.map(n => n.metadata.depth))
})
