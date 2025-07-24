/**
 * WebSocket Connection Handler
 * 
 * Manages real-time communication with the bot system.
 * Includes reconnection logic and error handling.
 */

import { io } from 'socket.io-client'
import { API_ENDPOINTS } from './interfaces.js'

let socket = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 2000

export const connectWebSocket = () => {
    return new Promise((resolve, reject) => {
        try {
            // For development, we'll use a mock WebSocket that simulates the bot system
            if (process.env.NODE_ENV === 'development' || !window.location.host.includes('bot-system')) {
                socket = createMockWebSocket()
                resolve(socket)
                return
            }
            
            // Production WebSocket connection
            socket = io(API_ENDPOINTS.WEBSOCKET, {
                transports: ['websocket', 'polling'],
                timeout: 10000
            })
            
            socket.on('connect', () => {
                console.log('Connected to bot system')
                reconnectAttempts = 0
                resolve(socket)
            })
            
            socket.on('disconnect', () => {
                console.log('Disconnected from bot system')
                attemptReconnect()
            })
            
            socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error)
                reject(error)
            })
            
        } catch (error) {
            reject(error)
        }
    })
}

const attemptReconnect = () => {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++
        console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`)
        setTimeout(() => connectWebSocket(), RECONNECT_DELAY * reconnectAttempts)
    }
}

// Mock WebSocket for development
const createMockWebSocket = () => {
    const mockSocket = {
        connected: true,
        listeners: {},
        
        on(event, callback) {
            this.listeners[event] = this.listeners[event] || []
            this.listeners[event].push(callback)
        },
        
        emit(event, data) {
            console.log(`Mock WebSocket emit: ${event}`, data)
            // Simulate responses for development
            setTimeout(() => {
                this.simulateResponse(event, data)
            }, 100)
        },
        
        disconnect() {
            this.connected = false
            console.log('Mock WebSocket disconnected')
        },
        
        simulateResponse(event, data) {
            // Simulate bot system responses based on the event
            switch (event) {
                case 'subscribe_bot':
                    this.trigger('bot_state_update', {
                        botState: {
                            id: 'mock-bot',
                            name: 'Mock Bot',
                            engine: 'claude-3-5-sonnet',
                            status: 'idle',
                            availableTools: ['python_edit', 'view', 'execute_powershell'],
                            parameters: { temperature: 0.7, max_tokens: 4000 }
                        }
                    })
                    break
                    
                case 'send_message':
                    // Simulate a conversation
                    const userNodeId = `node-${Date.now()}`
                    const assistantNodeId = `node-${Date.now() + 1}`
                    
                    this.trigger('new_message', {
                        node: {
                            id: userNodeId,
                            role: 'user',
                            content: data.content,
                            timestamp: new Date().toISOString(),
                            parentId: data.parentNodeId,
                            childIds: [assistantNodeId],
                            toolCalls: [],
                            toolResults: []
                        }
                    })
                    
                    setTimeout(() => {
                        this.trigger('new_message', {
                            node: {
                                id: assistantNodeId,
                                role: 'assistant',
                                content: `Mock response to: "${data.content}"`,
                                timestamp: new Date().toISOString(),
                                parentId: userNodeId,
                                childIds: [],
                                toolCalls: [],
                                toolResults: []
                            }
                        })
                    }, 1000)
                    break
            }
        },
        
        trigger(event, data) {
            if (this.listeners[event]) {
                this.listeners[event].forEach(callback => callback(data))
            }
        }
    }
    
    return mockSocket
}

export const getSocket = () => socket
