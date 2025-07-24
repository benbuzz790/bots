/**
 * Main Application Entry Point
 * 
 * Initializes Vue app with router, state management, and global components.
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import routes
import ConversationTreeView from './components/ConversationTreeView.vue'
import BotDashboardView from './components/BotDashboardView.vue'
import FunctionalPromptView from './components/FunctionalPromptView.vue'

// Create router
const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', redirect: '/conversation-tree' },
        { path: '/conversation-tree', component: ConversationTreeView, name: 'ConversationTree' },
        { path: '/dashboard', component: BotDashboardView, name: 'Dashboard' },
        { path: '/functional-prompts', component: FunctionalPromptView, name: 'FunctionalPrompts' }
    ]
})

// Create and configure app
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')
