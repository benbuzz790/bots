<template>
  <div class="bot-dashboard-view">
    <div class="view-header mb-md">
      <h2 class="text-2xl">Bot Dashboard</h2>
      <p class="text-muted">Real-time monitoring of bot state and performance metrics</p>
    </div>
    <!-- Connection Status -->
    <div class="connection-status mb-md">
      <div class="status-indicator" :class="connectionStatus">
        <div class="status-dot"></div>
        <span class="status-text">{{ connectionStatusText }}</span>
      </div>
    </div>
    <div class="dashboard-grid">
      <!-- Bot State Panel -->
      <div class="dashboard-card bot-state-card">
        <div class="card-header">
          <h3>Bot State</h3>
          <div class="bot-status-badge" :class="botState?.status || 'unknown'">
            {{ (botState?.status || 'unknown').toUpperCase() }}
          </div>
        </div>
        <div class="card-content">
          <div class="bot-info" v-if="botState">
            <div class="info-row">
              <span class="label">Name:</span>
              <span class="value">{{ botState.name }}</span>
            </div>
            <div class="info-row">
              <span class="label">Engine:</span>
              <span class="value">{{ botState.engine }}</span>
            </div>
            <div class="info-row">
              <span class="label">Current Node:</span>
              <span class="value">{{ botState.currentNode || 'None' }}</span>
            </div>
          </div>
          <div class="no-data" v-else>
            <span>No bot data available</span>
          </div>
        </div>
      </div>
      <!-- Performance Metrics Panel -->
      <div class="dashboard-card metrics-card">
        <div class="card-header">
          <h3>Performance Metrics</h3>
        </div>
        <div class="card-content">
          <div class="metrics-grid">
            <div class="metric-item">
              <div class="metric-value">{{ botMetrics.totalMessages }}</div>
              <div class="metric-label">Total Messages</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ botMetrics.totalToolCalls }}</div>
              <div class="metric-label">Tool Calls</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ formatResponseTime(botMetrics.averageResponseTime) }}</div>
              <div class="metric-label">Avg Response</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ formatTokens(botMetrics.tokenUsage) }}</div>
              <div class="metric-label">Token Usage</div>
            </div>
            <div class="metric-item">
              <div class="metric-value error-count">{{ botMetrics.errorCount }}</div>
              <div class="metric-label">Errors</div>
            </div>
          </div>
        </div>
      </div>
      <!-- Tool Usage Panel -->
      <div class="dashboard-card tool-usage-card">
        <div class="card-header">
          <h3>Tool Usage Statistics</h3>
        </div>
        <div class="card-content">
          <div class="tool-list">
            <div 
              v-for="tool in availableTools" 
              :key="tool"
              class="tool-item"
            >
              <div class="tool-info">
                <span class="tool-name">{{ tool }}</span>
                <span class="tool-count">{{ toolUsageStats[tool] || 0 }}</span>
              </div>
              <div class="tool-usage-bar">
                <div 
                  class="usage-fill" 
                  :style="{ width: getToolUsagePercentage(tool) + '%' }"
                ></div>
              </div>
            </div>
          </div>
          <div class="no-tools" v-if="availableTools.length === 0">
            <span>No tools available</span>
          </div>
        </div>
      </div>
      <!-- Model Parameters Panel -->
      <div class="dashboard-card parameters-card">
        <div class="card-header">
          <h3>Model Parameters</h3>
        </div>
        <div class="card-content">
          <div class="parameter-controls" v-if="botState?.parameters">
            <div class="parameter-item">
              <label>Temperature</label>
              <div class="parameter-control">
                <input 
                  type="range" 
                  min="0" 
                  max="2" 
                  step="0.1"
                  :value="botState.parameters.temperature"
                  @input="updateParameter('temperature', $event.target.value)"
                  class="parameter-slider"
                />
                <span class="parameter-value">{{ botState.parameters.temperature }}</span>
              </div>
            </div>
            <div class="parameter-item">
              <label>Max Tokens</label>
              <div class="parameter-control">
                <input 
                  type="range" 
                  min="100" 
                  max="8000" 
                  step="100"
                  :value="botState.parameters.max_tokens"
                  @input="updateParameter('max_tokens', $event.target.value)"
                  class="parameter-slider"
                />
                <span class="parameter-value">{{ botState.parameters.max_tokens }}</span>
              </div>
            </div>
            <div class="parameter-item">
              <label>Top P</label>
              <div class="parameter-control">
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.05"
                  :value="botState.parameters.top_p"
                  @input="updateParameter('top_p', $event.target.value)"
                  class="parameter-slider"
                />
                <span class="parameter-value">{{ botState.parameters.top_p }}</span>
              </div>
            </div>
          </div>
          <div class="no-data" v-else>
            <span>No parameter data available</span>
          </div>
        </div>
      </div>
      <!-- Real-time Activity Feed -->
      <div class="dashboard-card activity-feed-card">
        <div class="card-header">
          <h3>Real-time Activity</h3>
          <button @click="clearActivityFeed" class="clear-button">Clear</button>
        </div>
        <div class="card-content">
          <div class="activity-feed" ref="activityFeed">
            <div 
              v-for="activity in recentActivity" 
              :key="activity.id"
              class="activity-item"
              :class="activity.type"
            >
              <div class="activity-timestamp">{{ formatTime(activity.timestamp) }}</div>
              <div class="activity-content">{{ activity.message }}</div>
            </div>
          </div>
          <div class="no-activity" v-if="recentActivity.length === 0">
            <span>No recent activity</span>
          </div>
        </div>
      </div>
      <!-- Conversation Status Panel -->
      <div class="dashboard-card conversation-status-card">
        <div class="card-header">
          <h3>Conversation Status</h3>
        </div>
        <div class="card-content">
          <div class="conversation-info" v-if="currentNode">
            <div class="info-row">
              <span class="label">Current Node:</span>
              <span class="value">{{ currentNode.id }}</span>
            </div>
            <div class="info-row">
              <span class="label">Role:</span>
              <span class="value role-badge" :class="currentNode.role">{{ currentNode.role }}</span>
            </div>
            <div class="info-row">
              <span class="label">Path Length:</span>
              <span class="value">{{ conversationPath.length }}</span>
            </div>
            <div class="info-row">
              <span class="label">Total Nodes:</span>
              <span class="value">{{ conversationNodes.size }}</span>
            </div>
          </div>
          <div class="no-data" v-else>
            <span>No active conversation</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useBotStore } from '../shared/store.js'
import { mockBotState, mockToolUsageStats } from '../mock-data/sample-data.js'
export default {
  name: 'BotDashboardView',
  setup() {
    const store = useBotStore()
    const recentActivity = ref([])
    const activityFeed = ref(null)
    let activityIdCounter = 0
    // Use mock data for development
    const useMockData = computed(() => store.connectionStatus !== 'connected')
    const botState = computed(() => 
      useMockData.value ? mockBotState : store.botState
    )
    const botMetrics = computed(() => 
      useMockData.value ? mockBotState.metrics : store.botMetrics
    )
    const toolUsageStats = computed(() => 
      useMockData.value ? mockToolUsageStats : store.toolUsageStats
    )
    const availableTools = computed(() => 
      useMockData.value ? mockBotState.availableTools : store.availableTools
    )
    const connectionStatus = computed(() => store.connectionStatus)
    const currentNode = computed(() => store.currentNode)
    const conversationPath = computed(() => store.conversationPath)
    const conversationNodes = computed(() => store.conversationNodes)
    const connectionStatusText = computed(() => {
      const status = connectionStatus.value
      return {
        'disconnected': 'Disconnected',
        'connecting': 'Connecting...',
        'connected': 'Connected',
        'error': 'Connection Error'
      }[status] || 'Unknown'
    })
    // Utility functions
    const formatResponseTime = (ms) => {
      if (ms < 1000) return `${ms}ms`
      return `${(ms / 1000).toFixed(1)}s`
    }
    const formatTokens = (tokens) => {
      if (tokens < 1000) return tokens.toString()
      return `${(tokens / 1000).toFixed(1)}k`
    }
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }
    const getToolUsagePercentage = (toolName) => {
      const usage = toolUsageStats.value[toolName] || 0
      const maxUsage = Math.max(...Object.values(toolUsageStats.value), 1)
      return (usage / maxUsage) * 100
    }
    const addActivity = (type, message) => {
      const activity = {
        id: ++activityIdCounter,
        type,
        message,
        timestamp: new Date().toISOString()
      }
      recentActivity.value.unshift(activity)
      // Keep only last 50 activities
      if (recentActivity.value.length > 50) {
        recentActivity.value = recentActivity.value.slice(0, 50)
      }
      // Auto-scroll to top
      nextTick(() => {
        if (activityFeed.value) {
          activityFeed.value.scrollTop = 0
        }
      })
    }
    const clearActivityFeed = () => {
      recentActivity.value = []
    }
    const updateParameter = (paramName, value) => {
      // In a real implementation, this would send the update to the bot system
      console.log(`Updating ${paramName} to ${value}`)
      addActivity('parameter', `Updated ${paramName} to ${value}`)
      // For mock data, update locally
      if (useMockData.value && mockBotState.parameters) {
        mockBotState.parameters[paramName] = parseFloat(value)
      }
    }
    // Simulate real-time activity for development
    const simulateActivity = () => {
      if (useMockData.value) {
        const activities = [
          { type: 'message', message: 'New user message received' },
          { type: 'tool', message: 'Tool call: python_edit executed successfully' },
          { type: 'response', message: 'Bot response generated (1.2s)' },
          { type: 'branch', message: 'Conversation branched at node-003' },
          { type: 'error', message: 'Tool execution failed: timeout' }
        ]
        const randomActivity = activities[Math.floor(Math.random() * activities.length)]
        addActivity(randomActivity.type, randomActivity.message)
      }
    }
    let activityInterval = null
    onMounted(() => {
      // Connect to bot system
      store.connect()
      // Simulate activity for development
      if (useMockData.value) {
        activityInterval = setInterval(simulateActivity, 3000)
      }
      // Add initial activity
      addActivity('system', 'Dashboard initialized')
    })
    onUnmounted(() => {
      if (activityInterval) {
        clearInterval(activityInterval)
      }
    })
    return {
      // State
      botState,
      botMetrics,
      toolUsageStats,
      availableTools,
      connectionStatus,
      connectionStatusText,
      currentNode,
      conversationPath,
      conversationNodes,
      recentActivity,
      activityFeed,
      // Methods
      formatResponseTime,
      formatTokens,
      formatTime,
      getToolUsagePercentage,
      clearActivityFeed,
      updateParameter
    }
  }
}
</script>
<style scoped>
.bot-dashboard-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-md);
}
.connection-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: 500;
}
.status-indicator.connected {
  background: var(--color-success-light);
  color: var(--color-success-dark);
}
.status-indicator.connecting {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}
.status-indicator.disconnected,
.status-indicator.error {
  background: var(--color-error-light);
  color: var(--color-error-dark);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
  flex: 1;
}
.dashboard-card {
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.card-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  background: var(--color-background-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 600;
}
.card-content {
  padding: var(--spacing-md);
  flex: 1;
  overflow: auto;
}
.bot-status-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 600;
}
.bot-status-badge.idle {
  background: var(--color-success-light);
  color: var(--color-success-dark);
}
.bot-status-badge.thinking {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}
.bot-status-badge.executing_tool {
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
}
.bot-status-badge.error {
  background: var(--color-error-light);
  color: var(--color-error-dark);
}
.bot-info,
.conversation-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.label {
  font-weight: 500;
  color: var(--text-secondary);
}
.value {
  font-weight: 600;
}
.role-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
}
.role-badge.user {
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
}
.role-badge.assistant {
  background: var(--color-secondary-light);
  color: var(--color-secondary-dark);
}
.role-badge.system {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-md);
}
.metric-item {
  text-align: center;
}
.metric-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}
.metric-value.error-count {
  color: var(--color-error);
}
.metric-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.tool-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.tool-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.tool-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tool-name {
  font-weight: 500;
  font-family: var(--font-mono);
}
.tool-count {
  font-weight: 600;
  color: var(--color-primary);
}
.tool-usage-bar {
  height: 4px;
  background: var(--color-background);
  border-radius: 2px;
  overflow: hidden;
}
.usage-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}
.parameter-controls {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
.parameter-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.parameter-item label {
  font-weight: 500;
  color: var(--text-secondary);
}
.parameter-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.parameter-slider {
  flex: 1;
  height: 4px;
  background: var(--color-background);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.parameter-value {
  font-weight: 600;
  font-family: var(--font-mono);
  min-width: 60px;
  text-align: right;
}
.activity-feed {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.activity-item {
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  border-left: 3px solid var(--color-primary);
}
.activity-item.message {
  border-left-color: var(--color-primary);
  background: var(--color-primary-light);
}
.activity-item.tool {
  border-left-color: var(--color-secondary);
  background: var(--color-secondary-light);
}
.activity-item.response {
  border-left-color: var(--color-success);
  background: var(--color-success-light);
}
.activity-item.error {
  border-left-color: var(--color-error);
  background: var(--color-error-light);
}
.activity-item.system {
  border-left-color: var(--color-warning);
  background: var(--color-warning-light);
}
.activity-timestamp {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}
.activity-content {
  font-size: var(--font-size-sm);
}
.clear-button {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-background);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  font-size: var(--font-size-xs);
}
.clear-button:hover {
  background: var(--color-background-dark);
}
.no-data,
.no-tools,
.no-activity {
  text-align: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: var(--spacing-lg);
}
/* Responsive adjustments */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
