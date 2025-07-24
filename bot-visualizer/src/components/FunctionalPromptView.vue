<template>
  <div class="functional-prompt-view">
    <div class="view-header mb-md">
      <h2 class="text-2xl">Functional Prompt Flow Designer</h2>
      <p class="text-muted">Visual workflow builder for creating and editing functional prompts</p>
    </div>

    <div class="card">
      <div class="placeholder-content">
        <div class="placeholder-icon">🔄</div>
        <h3>Functional Prompt Flow Designer</h3>
        <p class="text-muted">
          This component will enable visual workflow creation with:
        </p>
        <ul class="feature-list">
          <li>Drag-and-drop workflow builder</li>
          <li>Node-based editing (chain, branch, conditions)</li>
          <li>Live execution visualization</li>
          <li>Template library for common patterns</li>
          <li>Real-time workflow validation</li>
        </ul>
        <div class="status-badge">Ready for Implementation</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalPromptView'
}
</script>

<style scoped>
.functional-prompt-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.placeholder-content {
  text-align: center;
  padding: var(--spacing-2xl);
}

.placeholder-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-md);
}

.feature-list {
  text-align: left;
  max-width: 400px;
  margin: var(--spacing-lg) auto;
}

.feature-list li {
  margin-bottom: var(--spacing-sm);
  color: var(--text-secondary);
}

.status-badge {
  display: inline-block;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-secondary);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: 500;
  margin-top: var(--spacing-lg);
}
</style>
