<template>
  <div class="conversation-tree-view">
    <div class="view-header mb-md">
      <h2 class="text-2xl">Interactive Conversation Tree</h2>
      <p class="text-muted">
        Visualizing {{ totalNodes }} conversation nodes with {{ totalBranches }} branches
      </p>
    </div>

    <!-- View Toggle and Controls -->
    <div class="tree-controls mb-md">
      <div class="flex gap-md items-center">
        <button 
          @click="viewMode = 'tree'" 
          :class="['btn', viewMode === 'tree' ? 'btn-primary' : 'btn-secondary']"
        >
          Tree View
        </button>
        <button 
          @click="viewMode = 'list'" 
          :class="['btn', viewMode === 'list' ? 'btn-primary' : 'btn-secondary']"
        >
          List View
        </button>
        
        <div class="separator"></div>
        
        <button v-if="viewMode === 'tree'" @click="centerTree" class="btn btn-secondary">Center View</button>
        <button v-if="viewMode === 'list'" @click="expandAll" class="btn btn-secondary">Expand All</button>
        <button v-if="viewMode === 'list'" @click="collapseAll" class="btn btn-secondary">Collapse All</button>
        <button v-if="viewMode === 'list'" @click="focusCurrentNode" class="btn btn-primary">Focus Current</button>
        
        <div class="current-path text-sm text-muted">
          Path: {{ conversationPath.length }} nodes deep
        </div>
      </div>
    </div>

    <!-- Tree View (D3.js) -->
    <div v-if="viewMode === 'tree'" class="tree-container" ref="treeContainer">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading conversation data...</p>
      </div>
      <svg v-else ref="treeSvg" class="tree-svg"></svg>
    </div>

    <!-- List View (Hierarchical) -->
    <div v-else-if="viewMode === 'list'" class="card tree-container">
      <div v-if="conversationTree" class="tree-visualization">
        <ConversationNode
          :node="conversationTree"
          :current-node-id="currentNodeId"
          :expanded-nodes="expandedNodes"
          @node-click="handleNodeClick"
          @toggle-expand="handleToggleExpand"
        />
      </div>
      <div v-else class="no-data">
        <p class="text-muted">No conversation data available</p>
      </div>
    </div>

    <!-- Node Details Panel (Draggable) -->
    <div 
      v-if="selectedNode" 
      class="node-details-panel draggable-panel" 
      :class="{ dragging: isDraggingPanel }"
      ref="detailsPanel"
      :style="{ 
        position: 'fixed',
        left: detailsPanelPosition.x + 'px',
        top: detailsPanelPosition.y + 'px',
        zIndex: 1000
      }"
    >
      <div 
        class="panel-header draggable-header" 
        @mousedown="startDragPanel" 
        @selectstart.prevent
      >
        <h3>Node Details</h3>
        <button @click="closeDetailsPanel" class="close-btn" @mousedown.stop>&times;</button>
      </div>

      <div class="panel-content">
        <div class="node-info">
          <div class="info-row">
            <span class="label">Role:</span>
            <span :class="['role-badge', `role-${selectedNode.role}`]">{{ getRoleDisplayName(selectedNode.role) }}</span>
          </div>
          <div class="info-row">
            <span class="label">Timestamp:</span>
            <span class="timestamp">{{ formatTimestamp(selectedNode.timestamp) }}</span>
          </div>
          <div v-if="selectedNode.childIds?.length > 1" class="info-row">
            <span class="label">Branches:</span>
                <span class="branch-count">{{ selectedNode.childIds.length }} paths</span>
              </div>
            </div>

            <div class="content-section">
              <h4>Content</h4>
              <div class="content-preview">{{ selectedNode.content }}</div>
            </div>

            <div v-if="selectedNode.toolCalls?.length > 0" class="tool-calls-section">
              <h4>Tool Calls ({{ selectedNode.toolCalls.length }})</h4>
              <div v-for="(call, index) in selectedNode.toolCalls" :key="index" class="tool-call">
                <div class="tool-header">
                  <span class="tool-name">{{ call.function?.name || call.name }}</span>
                  <span v-if="call.executionTime" class="execution-time">{{ call.executionTime }}ms</span>
                </div>
                <div v-if="call.function?.arguments || call.parameters" class="tool-params">
                  <pre>{{ formatToolParams(call.function?.arguments || call.parameters) }}</pre>
                </div>
              </div>
            </div>

            <div v-if="selectedNode.toolResults?.length > 0" class="tool-results-section">
              <h4>Tool Results ({{ selectedNode.toolResults.length }})</h4>
              <div v-for="(result, index) in selectedNode.toolResults" :key="index" class="tool-result">
                <div class="result-header">
                  <span class="tool-name">{{ result.toolCallId || `Result ${index + 1}` }}</span>
                  <span :class="['status-badge', result.isError ? 'error' : 'success']">
                    {{ result.isError ? 'Error' : 'Success' }}
                  </span>
                </div>
                <div class="result-content">{{ truncateText(result.content, 500) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <script>
    import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
    import { useBotStore } from '../shared/store.js'
    import ConversationNode from './ConversationNode.vue'
    import * as d3 from 'd3'

    export default {
      name: 'ConversationTreeView',
      components: {
        ConversationNode
      },
      setup() {
        const botStore = useBotStore()
    
        // Reactive references
        const selectedNode = ref(null)
        const expandedNodes = ref(new Set())
        const showBranchComparison = ref(false)
        const viewMode = ref('tree') // 'tree' or 'list'
    
        // D3.js Tree View references
        const treeContainer = ref(null)
        const treeSvg = ref(null)
        const svg = ref(null)
        const zoom = ref(null)
    
        // Draggable panel state
        const isDraggingPanel = ref(false)
        const dragOffset = ref({ x: 0, y: 0 })
        const detailsPanel = ref(null)
        const detailsPanelPosition = ref({ x: 50, y: 50 })

        // Computed properties
        const conversationTree = computed(() => botStore.conversationTree)
        const currentNodeId = computed(() => botStore.currentNodeId)
        const conversationPath = computed(() => botStore.conversationPath)

        const totalNodes = computed(() => botStore.conversationNodes.size)
        const totalBranches = computed(() => {
          let branches = 0
          for (const node of botStore.conversationNodes.values()) {
            if (node.childIds.length > 1) branches += node.childIds.length - 1
          }
          return branches
        })

        const isLoading = computed(() => {
          return !botStore.conversationTree || botStore.conversationNodes.size === 0
        })

        // List view methods
        const expandAll = () => {
          expandedNodes.value.clear()
          for (const node of botStore.conversationNodes.values()) {
            expandedNodes.value.add(node.id)
          }
        }

        const collapseAll = () => {
          expandedNodes.value.clear()
        }

        const focusCurrentNode = () => {
          if (currentNodeId.value) {
            expandedNodes.value.clear()
            // Expand path to current node
            const path = conversationPath.value
            path.forEach(node => expandedNodes.value.add(node.id))
          }
        }

        const handleNodeClick = (node) => {
          selectedNode.value = node
          // Position panel near the clicked node if possible
          detailsPanelPosition.value = { x: 100, y: 100 }
        }

        const handleToggleExpand = (nodeId) => {
          if (expandedNodes.value.has(nodeId)) {
            expandedNodes.value.delete(nodeId)
          } else {
            expandedNodes.value.add(nodeId)
          }
        }

        // D3.js methods will be added next
    
const initializeD3Tree = () => {
  if (!treeContainer.value || !treeSvg.value) return
      
  const containerRect = treeContainer.value.getBoundingClientRect()
  const width = containerRect.width
  const height = Math.max(containerRect.height, 600)
      
  // Clear any existing content
  d3.select(treeSvg.value).selectAll("*").remove()
      
  svg.value = d3.select(treeSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('display', 'block')
      
  // Create zoom behavior
  zoom.value = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      svg.value.select('g').attr('transform', event.transform)
    })
      
  svg.value.call(zoom.value)
      
  // Create main group for content
  svg.value.append('g')
      
  renderD3Tree()
}

const renderD3Tree = () => {
  if (!svg.value || !botStore.conversationTree) return
      
  const containerRect = treeContainer.value.getBoundingClientRect()
  const width = containerRect.width
  const height = Math.max(containerRect.height, 600)
      
  // Convert conversation tree to D3 hierarchy
  const root = d3.hierarchy(botStore.conversationTree, d => {
    return d.childIds?.map(id => botStore.conversationNodes.get(id)).filter(Boolean) || []
  })
      
  // Create tree layout
  const treeLayout = d3.tree()
    .size([height - 100, width - 200])
    .separation((a, b) => (a.parent === b.parent ? 1 : 2) / a.depth)
      
  treeLayout(root)
      
  const g = svg.value.select('g')
      
  // Clear existing content
  g.selectAll('*').remove()
      
  // Draw links
  g.selectAll('.link')
    .data(root.links())
    .enter()
    .append('path')
    .attr('class', 'link')
    .attr('d', d3.linkHorizontal()
      .x(d => d.y + 100)
      .y(d => d.x + 50)
    )
    .style('fill', 'none')
    .style('stroke', 'var(--border-color)')
    .style('stroke-width', '2px')
      
  // Draw nodes
  const nodes = g.selectAll('.node')
    .data(root.descendants())
    .enter()
    .append('g')
    .attr('class', 'node')
    .attr('transform', d => `translate(${d.y + 100},${d.x + 50})`)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      handleNodeClick(d.data)
    const [x, y] = d3.pointer(event, treeContainer.value)
    detailsPanelPosition.value = {
      x: Math.min(x + 20, treeContainer.value.clientWidth - 300),
      y: Math.max(y - 100, 20)
    }
    .on('mouseover', (event, d) => {
      d3.select(event.currentTarget).select('circle').attr('r', 30)
    })
    .on('mouseout', (event, d) => {
      d3.select(event.currentTarget).select('circle').attr('r', 25)
    })
    })
      
  // Add circles for nodes
  nodes.append('circle')
  .attr('r', 25)
    .style('fill', d => {
      const role = d.data.role
      if (role === 'user') return 'var(--color-primary)'
      if (role === 'assistant') return 'var(--color-success)'
      if (role === 'system') return 'var(--color-warning)'
      if (role === 'tool') return 'var(--color-danger)'
      return 'var(--text-muted)'
    })
    .style('stroke', 'var(--bg-primary)')
    .style('stroke-width', '2px')
  // Hide circles for user/assistant nodes (emojis will show instead)
  nodes.select('circle')
    .style('opacity', d => (d.data.role === 'user' || d.data.role === 'assistant') ? 0 : 1)


  // Add emoji faces for user and assistant nodes
  nodes.filter(d => d.data.role === 'user' || d.data.role === 'assistant')
    .append('text')
    .attr('class', 'emoji-face')
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .style('font-size', '30px')
    .style('pointer-events', 'none')
    .text(d => {
      return d.data.role === 'user' ? '😊' : '🤖'
    })

  // Add tool indicators
  nodes.filter(d => d.data.toolCalls && d.data.toolCalls.length > 0)
    .append('circle')
    .attr('class', 'tool-indicator')
    .attr('r', 8)
    .attr('cx', 15)
    .attr('cy', -15)
    .style('fill', '#ff6b35')
    .style('stroke', '#fff')
    .style('stroke-width', 1)
  // Add tool count labels
  nodes.filter(d => d.data.toolCalls && d.data.toolCalls.length > 0)
    .append('text')
    .attr('class', 'tool-count')
    .attr('x', 15)
    .attr('y', -15)
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .style('font-size', '10px')
    .style('font-weight', 'bold')
    .style('fill', '#fff')
    .style('pointer-events', 'none')
    .text(d => d.data.toolCalls.length)


      
  // Add text labels
  nodes.filter(d => d.data.role === 'system' || d.data.role === 'tool')
    .append('text')
    .attr('dy', '0.31em')
    .attr('x', 0)
    .style('text-anchor', 'middle')
    .style('font-weight', 'bold')
    .style('fill', '#fff')
    .style('font-size', '12px')
    .style('fill', 'var(--text-primary)')
    .text(d => {
      const role = d.data.role
      const abbrevs = { user: 'U', assistant: 'A', system: 'S', tool: 'T' }
      return abbrevs[role] || '?'
    })
}

    const centerTree = () => {
      if (!svg.value || !botStore.conversationTree) return
      
      const containerRect = treeContainer.value.getBoundingClientRect()
      const svgWidth = containerRect.width
      const svgHeight = containerRect.height
      
      // Get the bounding box of all nodes in the tree
      const g = svg.value.select('g')
      const bounds = g.node()?.getBBox()
      
      if (!bounds) {
        // Fallback if no bounds available - just reset to origin
        svg.value.transition()
          .duration(750)
          .call(zoom.value.transform, d3.zoomIdentity)
        return
      }
      
      // Calculate the center of the tree content
      const treeCenterX = bounds.x + bounds.width / 2
      const treeCenterY = bounds.y + bounds.height / 2
      
      // Calculate the center of the viewport
      const viewportCenterX = svgWidth / 2
      const viewportCenterY = svgHeight / 2
      
      // Calculate the translation needed to center the tree
      const translateX = viewportCenterX - treeCenterX
      const translateY = viewportCenterY - treeCenterY
      
      svg.value.transition()
        .duration(750)
        .call(zoom.value.transform, d3.zoomIdentity.translate(translateX, translateY).scale(1))
    }

    // Draggable panel methods
    const startDragPanel = (event) => {
      isDraggingPanel.value = true
      const rect = detailsPanel.value.getBoundingClientRect()
      dragOffset.value = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      }
      document.addEventListener('mousemove', dragPanel)
      document.addEventListener('mouseup', stopDragPanel)
    }

    const dragPanel = (event) => {
      if (!isDraggingPanel.value) return
      
      const containerRect = treeContainer.value.getBoundingClientRect()
      const panelRect = detailsPanel.value.getBoundingClientRect()
      const panelWidth = panelRect.width
      const panelHeight = panelRect.height
      
      let newX = event.clientX - dragOffset.value.x
      let newY = event.clientY - dragOffset.value.y
      
      // Constrain to viewport bounds
      newX = Math.max(0, Math.min(newX, containerRect.width - panelWidth))
      newY = Math.max(0, Math.min(newY, containerRect.height - panelHeight))
      
      detailsPanelPosition.value = { x: newX, y: newY }
    }

    const stopDragPanel = () => {
      isDraggingPanel.value = false
      document.removeEventListener('mousemove', dragPanel)
      document.removeEventListener('mouseup', stopDragPanel)
    }
    
    const closeDetailsPanel = () => {
      selectedNode.value = null
    }

    // Utility methods
    const getRoleDisplayName = (role) => {
      const names = {
        user: 'User',
        assistant: 'Assistant',
        system: 'System',
        tool: 'Tool'
      }
      return names[role] || 'Unknown'
    }

    const formatTimestamp = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }

    const formatToolParams = (params) => {
      return JSON.stringify(params, null, 2)
    }

    const truncateText = (text, maxLength) => {
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    // Watch for view mode changes
    watch(viewMode, (newMode) => {
      if (newMode === 'tree') {
        nextTick(() => initializeD3Tree())
      }
    })

    // Lifecycle hooks
    onMounted(() => {
      // Load realistic test data
      if (!botStore.conversationTree || botStore.conversationNodes.size === 0) {
        botStore.loadRealisticTestData()
      }
      
      nextTick(() => {
        if (viewMode.value === 'tree') {
          initializeD3Tree()
        }
      })
      
      // Handle window resize
      window.addEventListener('resize', () => {
        if (viewMode.value === 'tree') {
          nextTick(() => initializeD3Tree())
        }
      })
    })

    onUnmounted(() => {
      document.removeEventListener('mousemove', dragPanel)
      document.removeEventListener('mouseup', stopDragPanel)
    })

    return {
      // Data
      conversationTree,
      currentNodeId,
      conversationPath,
      totalNodes,
      totalBranches,
      selectedNode,
      expandedNodes,
      viewMode,
      treeSvg,
      treeContainer,
      isLoading,
      
      // Draggable panel
      isDraggingPanel,
      detailsPanel,
      detailsPanelPosition,
      
      // Methods
      expandAll,
      collapseAll,
      focusCurrentNode,
      handleNodeClick,
      handleToggleExpand,
      centerTree,
      startDragPanel,
      closeDetailsPanel,
      
      // Utility methods
      getRoleDisplayName,
      formatTimestamp,
      formatToolParams,
      truncateText
    }
  }
}
</script>

<style scoped>
/* View Toggle and Controls */
.tree-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.separator {
  width: 1px;
  height: 24px;
  background: var(--border-color);
  margin: 0 var(--spacing-sm);
}

/* Tree Container */
.tree-container {
  height: calc(100vh - 200px);
  min-height: 600px;
  position: relative;
  overflow: hidden;
}

/* D3.js Tree View */
.tree-svg {
  width: 100%;
  height: 100%;
  display: block;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--spacing-md);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top: 4px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Draggable Node Details Panel */
.node-details-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-lg);
  width: 400px;
  max-height: 80vh;
  overflow-y: auto;
  backdrop-filter: blur(4px);
  opacity: 0.98;
  user-select: none;
}

.draggable-panel.dragging {
  pointer-events: none;
}

.draggable-header {
  cursor: move;
  user-select: none;
}

.draggable-header:active {
  cursor: grabbing;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  border-radius: var(--border-radius) var(--border-radius) 0 0;
}

.panel-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-muted);
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.panel-content {
  padding: var(--spacing-md);
}

/* Node Info Styles */
.node-info {
  margin-bottom: var(--spacing-md);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.label {
  font-weight: 600;
  color: var(--text-secondary);
}

.role-badge {
  padding: 2px 8px;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.role-user { background: var(--color-primary-light); color: var(--color-primary); }
.role-assistant { background: var(--color-success-light); color: var(--color-success); }
.role-system { background: var(--color-warning-light); color: var(--color-warning); }
.role-tool { background: var(--color-danger-light); color: var(--color-danger); }

.timestamp {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.branch-count {
  font-weight: 600;
  color: var(--color-primary);
}

/* Content Sections */
.content-section,
.tool-calls-section,
.tool-results-section {
  margin-bottom: var(--spacing-md);
}

.content-section h4,
.tool-calls-section h4,
.tool-results-section h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.content-preview {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}
</style>
