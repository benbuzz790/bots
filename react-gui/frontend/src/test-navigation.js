// Simple test to verify navigation integration
console.log('Testing navigation integration...');

// Test 1: Check if GitTreeVisualization component exists
try {
  const { GitTreeVisualization } = require('./components/GitTreeVisualization.tsx');
  console.log('✅ GitTreeVisualization component found');
} catch (error) {
  console.log('❌ GitTreeVisualization component not found:', error.message);
}

// Test 2: Check if ChatInterface imports GitTreeVisualization
try {
  const fs = require('fs');
  const chatInterfaceContent = fs.readFileSync('./src/components/ChatInterface.tsx', 'utf8');
  
  if (chatInterfaceContent.includes('GitTreeVisualization')) {
    console.log('✅ ChatInterface imports GitTreeVisualization');
  } else {
    console.log('❌ ChatInterface does not import GitTreeVisualization');
  }
} catch (error) {
  console.log('❌ Could not read ChatInterface:', error.message);
}

console.log('Navigation integration test complete!');
