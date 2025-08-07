// Test to diagnose WebSocket navigation bug
console.log('🐛 Diagnosing WebSocket Navigation Bug...');

const fs = require('fs');

// Check WebSocket handler structure
console.log('\n1. Checking WebSocket handler methods:');

try {
  const wsContent = fs.readFileSync('../backend/websocket_handler.py', 'utf8');
  
  // Check if methods are properly indented (part of the class)
  const handleNavigateMatch = wsContent.match(/(\s*)async def _handle_navigate\(/);
  const handleNavigateToNodeMatch = wsContent.match(/(\s*)async def _handle_navigate_to_node\(/);
  
  if (handleNavigateMatch) {
    const indentation = handleNavigateMatch[1].length;
    console.log(`✅ _handle_navigate found with ${indentation} spaces indentation`);
    console.log(`   ${indentation === 4 ? '✅ Correct class method indentation' : '❌ Wrong indentation - not a class method!'}`);
  } else {
    console.log('❌ _handle_navigate not found');
  }
  
  if (handleNavigateToNodeMatch) {
    const indentation = handleNavigateToNodeMatch[1].length;
    console.log(`✅ _handle_navigate_to_node found with ${indentation} spaces indentation`);
    console.log(`   ${indentation === 4 ? '✅ Correct class method indentation' : '❌ Wrong indentation - not a class method!'}`);
  } else {
    console.log('❌ _handle_navigate_to_node not found');
  }
  
} catch (error) {
  console.log('❌ Could not read WebSocket handler:', error.message);
}

console.log('\n🐛 Bug diagnosis complete!');
