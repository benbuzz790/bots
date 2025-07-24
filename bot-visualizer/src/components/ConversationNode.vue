<template>
  <div class="conversation-node">
    <div 
      :class="[
        'node-content',
        `role-${node.role}`,
        { 'current': node.id === currentNodeId },
        { 'has-tools': node.toolCalls?.length > 0 || node.toolResults?.length > 0 }
      ]"
      @click="$emit('node-click', node)"
    >
      <!-- Node Header -->
      <div class="node-header">
        <div class="node-role">{{ node.role }}</div>
        <div class="node-meta">
          <span v-if="node.toolCalls?.length > 0" class="tool-indicator" title="Has tool calls">
            🔧 {{ node.toolCalls.length }}
          </span>
          <span v-if="node.childIds?.length > 1" class="branch-indicator" title="Conversation branch">
            🌿 {{ node.childIds.length }}
          </span>
        </div>
      </div>
      
      <!-- Node Content Preview -->
      <div class="node-text">
        {{ truncateContent(node.content) }}
      </div>
      
      <!-- Expand/Collapse Button -->
      <button 
        v-if="node.children?.length > 0"
        @click.stop="$emit('toggle-expand', node.id)"
        class="expand-button"
        :class="{ expanded: expandedNodes.has(node.id) }"
      >
        {{ expandedNodes.has(node.id) ? '−' : '+' }}
      </button>
    </div>
    
    <!-- Child Nodes -->
    <div v-if="node.children?.length > 0 && expandedNodes.has(node.id)" class="children">
      <div 
        v-for="(child, index) in node.children" 
        :key="child.id"
        class="child-node"
        :class="{ 'branch-child': node.children.length > 1 }"
      >
        <div v-if="node.children.length > 1" class="branch-label">
          Branch {{ index + 1 }}
        </div>
        <ConversationNode
          :node="child"
          :current-node-id="currentNodeId"
          :expanded-nodes="expandedNodes"
          @node-click="$emit('node-click', $event)"
          @toggle-expand="$emit('toggle-expand', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConversationNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    currentNodeId: {
      type: String,
      default: null
    },
    expandedNodes: {
      type: Set,
      required: true
    }
  },
  emits: ['node-click', 'toggle-expand'],
  methods: {
    truncateContent(content) {
      if (!content) return '(empty)'
      return content.length > 100 ? content.substring(0, 100) + '...' : content
    }
  }
}
</script>

<style scoped>
.conversation-node {
  margin-bottom: var(--spacing-sm);
}

.node-content {
  position: relative;
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  border: 2px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--bg-card);
}

.node-content:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.node-content.current {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.node-content.has-tools {
  border-left: 4px solid var(--color-tool);
}

.node-content.role-user { background: var(--bg-role-user); }
.node-content.role-assistant { background: var(--bg-role-assistant); }
.node-content.role-system { background: var(--bg-role-system); }
.node-content.role-tool { background: var(--bg-role-tool); }

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.node-role {
  font-weight: 500;
  font-size: var(--font-size-sm);
  text-transform: capitalize;
}

.node-meta {
  display: flex;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
}

.tool-indicator, .branch-indicator {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--border-radius-sm);
}

.node-text {
  font-size: var(--font-size-sm);
  line-height: 1.4;
  color: var(--text-secondary);
}

.expand-button {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  font-size: var(--font-size-xs);
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.expand-button:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.children {
  margin-left: var(--spacing-lg);
  margin-top: var(--spacing-md);
  border-left: 2px solid var(--border-color);
  padding-left: var(--spacing-md);
}

.child-node {
  position: relative;
}

.child-node.branch-child {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  background: color-mix(in srgb, var(--color-accent) 5%, transparent);
}

.branch-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--color-accent);
  margin-bottom: var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.child-node.branch-child::before {
  content: '';
  position: absolute;
  left: -18px;
  top: 20px;
  width: 12px;
  height: 2px;
  background: var(--border-color);
}
</style>
