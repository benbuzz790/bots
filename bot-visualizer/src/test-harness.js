/**
 * Test Harness for Bot Visualizer Setup
 * 
 * Validates that all core systems are working correctly before parallel development.
 * Run this in browser console to verify setup integrity.
 */

import { useBotStore } from './shared/store.js'
import { mockBotState, mockConversationNodes, mockConversationTree } from './mock-data/sample-data.js'
import { connectWebSocket } from './api/websocket.js'

export const runSetupTests = async () => {
    console.log('🧪 Running Bot Visualizer Setup Tests...\n')
    
    const results = {
        passed: 0,
        failed: 0,
        tests: []
    }
    
    const test = (name, condition, details = '') => {
        const passed = condition
        results.tests.push({ name, passed, details })
        if (passed) {
            results.passed++
            console.log(`✅ ${name}`)
        } else {
            results.failed++
            console.log(`❌ ${name}${details ? ': ' + details : ''}`)
        }
    }
    
    // Test 1: Mock Data Integrity
    test(
        'Mock data structure is valid',
        mockBotState && mockBotState.id && mockConversationNodes.length > 0,
        'Mock bot state and conversation nodes should be properly defined'
    )
    
    // Test 2: Conversation Tree Building
    test(
        'Conversation tree builds correctly',
        mockConversationTree && mockConversationTree.children && mockConversationTree.children.length > 0,
        'Tree structure should have root node with children'
    )
    
    // Test 3: Store Initialization
    const store = useBotStore()
    test(
        'Pinia store initializes',
        store && typeof store.connect === 'function',
        'Store should have required methods'
    )
    
    // Test 4: WebSocket Mock Connection
    try {
        const socket = await connectWebSocket()
        test(
            'Mock WebSocket connects',
            socket && socket.connected,
            'Mock WebSocket should simulate connection'
        )
        
        // Test 5: WebSocket Event Handling
        let eventReceived = false
        socket.on('test_event', () => { eventReceived = true })
        socket.emit('test_event')
        
        setTimeout(() => {
            test(
                'WebSocket event system works',
                eventReceived,
                'Mock socket should handle events'
            )
        }, 50)
        
    } catch (error) {
        test('Mock WebSocket connects', false, error.message)
    }
    
    // Test 6: CSS Design System
    test(
        'CSS custom properties loaded',
        getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() !== '',
        'CSS variables should be available'
    )
    
    // Summary
    setTimeout(() => {
        console.log(`\n📊 Test Results: ${results.passed} passed, ${results.failed} failed`)
        
        if (results.failed === 0) {
            console.log('🎉 All tests passed! Setup is ready for parallel development.')
            console.log('\n📋 Next Steps:')
            console.log('1. Implement Conversation Tree Visualizer')
            console.log('2. Implement Bot Dashboard')
            console.log('3. Implement Functional Prompt Flow Designer')
        } else {
            console.log('⚠️  Some tests failed. Please review the setup before proceeding.')
        }
        
        return results
    }, 100)
}
// Integration Test Suite for Wrap-up Phase
export class IntegrationTestHarness {
    constructor() {
        this.botStore = null
        this.testResults = []
    }

    async runIntegrationTests() {
        console.log('🔗 Starting Integration Tests...\n')
        
        // Initialize store
        this.botStore = useBotStore()
        
        // Run test suite
        await this.testStoreIntegration()
        await this.testCrossComponentCommunication()
        await this.testDataSynchronization()
        await this.testNavigationIntegration()
        
        // Report results
        this.reportResults()
        return this.testResults
    }

    async testStoreIntegration() {
        try {
            console.log('Testing store integration...')
            
            // Load mock data
            this.botStore.botState = mockBotState
            
            // Add conversation nodes
            if (mockConversationTree) {
                const addNodeRecursively = (node) => {
                    this.botStore.addConversationNode(node)
                    if (node.children) {
                        node.children.forEach(addNodeRecursively)
                    }
                }
                addNodeRecursively(mockConversationTree)
            }
            
            this.addTestResult('Store Integration', 'PASS', 'Store properly integrated with mock data')
        } catch (error) {
            this.addTestResult('Store Integration', 'FAIL', error.message)
        }
    }

    async testCrossComponentCommunication() {
        try {
            console.log('Testing cross-component communication...')
            
            // Test navigation between components
            this.botStore.navigateToNode('node-003')
            
            if (this.botStore.currentNodeId === 'node-003') {
                this.addTestResult('Navigation', 'PASS', 'Node navigation working across components')
            } else {
                this.addTestResult('Navigation', 'FAIL', 'Node navigation failed')
            }
            
            // Test tool usage updates
            const initialToolCalls = this.botStore.botMetrics.totalToolCalls
            this.botStore.updateToolUsageStats('python_edit')
            
            if (this.botStore.botMetrics.totalToolCalls > initialToolCalls) {
                this.addTestResult('Tool Usage Updates', 'PASS', 'Tool usage stats updating correctly')
            } else {
                this.addTestResult('Tool Usage Updates', 'FAIL', 'Tool usage stats not updating')
            }
            
        } catch (error) {
            this.addTestResult('Cross-Component Communication', 'FAIL', error.message)
        }
    }

    async testDataSynchronization() {
        try {
            console.log('Testing data synchronization...')
            
            // Test conversation tree building
            const tree = this.botStore.conversationTree
            if (tree && tree.id === 'node-001') {
                this.addTestResult('Conversation Tree Sync', 'PASS', 'Tree structure synchronized correctly')
            } else {
                this.addTestResult('Conversation Tree Sync', 'FAIL', 'Tree structure not synchronized')
            }
            
            // Test conversation path calculation
            const path = this.botStore.conversationPath
            if (path && path.length > 0) {
                this.addTestResult('Conversation Path Sync', 'PASS', `Path synchronized: ${path.length} nodes`)
            } else {
                this.addTestResult('Conversation Path Sync', 'FAIL', 'Path synchronization failed')
            }
            
        } catch (error) {
            this.addTestResult('Data Synchronization', 'FAIL', error.message)
        }
    }

    async testNavigationIntegration() {
        try {
            console.log('Testing navigation integration...')
            
            // Test current node tracking
            const currentNode = this.botStore.currentNode
            if (currentNode && currentNode.id === this.botStore.currentNodeId) {
                this.addTestResult('Current Node Tracking', 'PASS', 'Current node properly tracked across components')
            } else {
                this.addTestResult('Current Node Tracking', 'FAIL', 'Current node tracking failed')
            }
            
        } catch (error) {
            this.addTestResult('Navigation Integration', 'FAIL', error.message)
        }
    }

    addTestResult(testName, status, message) {
        const result = { testName, status, message, timestamp: new Date().toISOString() }
        this.testResults.push(result)
        console.log(`${status === 'PASS' ? '✅' : '❌'} ${testName}: ${message}`)
    }

    reportResults() {
        const passed = this.testResults.filter(r => r.status === 'PASS').length
        const failed = this.testResults.filter(r => r.status === 'FAIL').length
        
        console.log('\n📊 Integration Test Results:')
        console.log(`✅ Passed: ${passed}`)
        console.log(`❌ Failed: ${failed}`)
        console.log(`📈 Success Rate: ${((passed / this.testResults.length) * 100).toFixed(1)}%`)
        
        if (failed > 0) {
            console.log('\n🔍 Failed Tests:')
            this.testResults
                .filter(r => r.status === 'FAIL')
                .forEach(r => console.log(`  - ${r.testName}: ${r.message}`))
        }
        
        if (failed === 0) {
            console.log('\n🎉 All integration tests passed! Components are properly integrated.')
        } else {
            console.log('\n⚠️  Integration issues detected. Please review failed tests.')
        }
    }
}

// Export integration test runner
export const runIntegrationTests = async () => {
    const harness = new IntegrationTestHarness()
    return await harness.runIntegrationTests()
}


// Auto-run tests if in development mode
if (import.meta.env.DEV) {
    console.log('🔧 Development mode detected. Test harness available.')
    console.log('Run runSetupTests() in console to validate setup.')
    
    // Make available globally for console access
    window.runSetupTests = runSetupTests
    window.runIntegrationTests = runIntegrationTests
}
