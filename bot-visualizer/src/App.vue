<template>
  <div id="app">
    <!-- Header Navigation -->
    <header class="app-header">
      <div class="container flex items-center justify-between py-md">
        <div class="flex items-center gap-md">
          <h1 class="text-xl font-bold">Bot Visualizer</h1>
          <div class="connection-status">
            <span 
              :class="['status-indicator', connectionStatus]"
              :title="`Connection: ${connectionStatus}`"
            ></span>
            <span class="text-sm text-muted">{{ connectionStatus }}</span>
          </div>
        </div>
        
        <nav class="main-nav">
          <button
            v-if="isDevelopment"
            @click="runIntegrationTests"
            class="test-button"
            title="Run Integration Tests"
          >
            🧪 Test
          </button>
          <router-link 
            v-for="route in routes" 
            :key="route.name"
            :to="route.path" 
            class="nav-link"
            :class="{ active: $route.name === route.name }"
          >
            {{ route.label }}
          </router-link>
        </nav>
      </div>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <div class="container h-full">
        <router-view />
      </div>
    </main>

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>Connecting to bot system...</p>
      </div>
    </div>
  </div>
</template>
<script>
import { computed, onMounted, onUnmounted } from 'vue'
import { useBotStore } from './shared/store.js'

import { runIntegrationTests } from './test-harness.js'
export default {
  name: 'App',
  setup() {
    const botStore = useBotStore()
    
    const routes = [
      { name: 'ConversationTree', path: '/conversation-tree', label: 'Conversation Tree' },
      { name: 'Dashboard', path: '/dashboard', label: 'Dashboard' },
      { name: 'FunctionalPrompts', path: '/functional-prompts', label: 'Functional Prompts' }
    ]
    
    const connectionStatus = computed(() => botStore.connectionStatus)
    const isLoading = computed(() => connectionStatus.value === 'connecting')
    const isDevelopment = computed(() => import.meta.env.DEV)
    
    onMounted(async () => {
      try {
        await botStore.connect()
      } catch (error) {
        console.error('Failed to connect to bot system:', error)
      }
    })
    
    onUnmounted(() => {
      botStore.disconnect()
    })
    const runIntegrationTestsHandler = async () => {
      console.log('🔗 Running integration tests from App component...')
      try {
        const results = await runIntegrationTests()
        console.log('Integration tests completed:', results)
      } catch (error) {
        console.error('Integration tests failed:', error)
      }
    }

    
    return {
      routes,
      connectionStatus,
      isLoading,
      isDevelopment,
      runIntegrationTests: runIntegrationTestsHandler
    }
  }
}
</script>
<style scoped>
.app-header {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
}

.status-indicator.connected {
  background: var(--color-secondary);
}

.status-indicator.connecting {
  background: var(--color-warning);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.main-nav {
  display: flex;
  gap: var(--spacing-md);
}
.test-button {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-secondary);
  border-radius: var(--border-radius-sm);
  background: var(--color-secondary);
  color: white;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.test-button:hover {
  background: var(--color-primary);
}


.nav-link {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-sm);
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.nav-link.active {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.app-main {
  flex: 1;
  padding: var(--spacing-lg) 0;
  min-height: 0; /* Allow flex child to shrink */
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  background: var(--bg-card);
  padding: var(--spacing-xl);
  border-radius: var(--border-radius-lg);
  text-align: center;
  box-shadow: var(--shadow-lg);
}

.loading-content p {
  margin-top: var(--spacing-md);
  color: var(--text-secondary);
}
</style>
