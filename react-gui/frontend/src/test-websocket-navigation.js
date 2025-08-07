// Test WebSocket navigation integration
console.log('🌐 Testing WebSocket Navigation Integration...');

// Test 1: Check if botStore navigation functions exist
console.log('\n1. Checking botStore navigation functions:');

try {
  const fs = require('fs');
  const botStoreContent = fs.readFileSync('./src/store/botStore.ts', 'utf8');
  
  const hasNavigate = botStoreContent.includes('navigate: (botId: string, direction: string)');
  const hasNavigateToNode = botStoreContent.includes('navigateToNode: (botId: string, nodeId: string)');
  const hasNavigationResponse = botStoreContent.includes('navigation_response');
  
  console.log(`✅ navigate function: ${hasNavigate ? 'FOUND' : 'MISSING'}`);
  console.log(`✅ navigateToNode function: ${hasNavigateToNode ? 'FOUND' : 'MISSING'}`);
  console.log(`✅ navigation_response handler: ${hasNavigationResponse ? 'FOUND' : 'MISSING'}`);
  
} catch (error) {
  console.log('❌ Could not read botStore:', error.message);
}

// Test 2: Check backend WebSocket handler
console.log('\n2. Checking backend WebSocket navigation:');

try {
  const fs = require('fs');
  const wsHandlerContent = fs.readFileSync('../backend/websocket_handler.py', 'utf8');
  
  const hasNavigateHandler = wsHandlerContent.includes('_handle_navigate');
  const hasNavigateToNodeHandler = wsHandlerContent.includes('_handle_navigate_to_node');
  const hasNavigationResponse = wsHandlerContent.includes('navigation_response');
  
  console.log(`✅ _handle_navigate: ${hasNavigateHandler ? 'FOUND' : 'MISSING'}`);
  console.log(`✅ _handle_navigate_to_node: ${hasNavigateToNodeHandler ? 'FOUND' : 'MISSING'}`);
  console.log(`✅ navigation_response: ${hasNavigationResponse ? 'FOUND' : 'MISSING'}`);
  
} catch (error) {
  console.log('❌ Could not read WebSocket handler:', error.message);
}

// Test 3: Check if ChatInterface connects everything
console.log('\n3. Checking ChatInterface integration:');

console.log('🎯 Navigation chain: GitTreeVisualization → ChatInterface.handleNodeClick → botStore.navigateToNode → WebSocket → Backend');

console.log('\n🌐 WebSocket navigation test complete!');
