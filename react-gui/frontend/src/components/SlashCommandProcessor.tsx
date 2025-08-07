import { useCallback } from 'react';
// Slash command types
export interface SlashCommand {
  command: string;
  args: string[];
  rawInput: string;
}
export interface SlashCommandHandlers {
  onNavigate: (direction: 'up' | 'down' | 'left' | 'right' | 'root') => void;
  onSave: () => void;
  onLoad: () => void;
  onHelp: () => void;
  onAuto: () => void;
  onFunctionalPrompt: () => void;
  onSystemMessage: (message: string) => void;
}
/**
 * Parse slash command from input string with defensive validation
 */
export function parseSlashCommand(input: string): SlashCommand | null {
  // Input validation
  if (!input || typeof input !== 'string') {
    throw new Error('Input must be a non-empty string');
  }
  const trimmed = input.trim();
  if (!trimmed.startsWith('/')) {
    return null; // Not a slash command
  }
  // Remove leading slash and split by spaces
  const parts = trimmed.slice(1).split(/\s+/).filter(part => part.length > 0);
  if (parts.length === 0) {
    throw new Error('Empty slash command');
  }
  const command = parts[0].toLowerCase();
  const args = parts.slice(1);
  // Validate command format
  if (!/^[a-z_]+$/.test(command)) {
    throw new Error(`Invalid command format: ${command}`);
  }
  return {
    command,
    args,
    rawInput: trimmed
  };
}
/**
 * Validate slash command handlers
 */
function validateHandlers(handlers: SlashCommandHandlers): void {
  if (!handlers || typeof handlers !== 'object') {
    throw new Error('Handlers must be an object');
  }
  const requiredHandlers = [
    'onNavigate', 'onSave', 'onLoad', 'onHelp', 
    'onAuto', 'onFunctionalPrompt', 'onSystemMessage'
  ];
  for (const handler of requiredHandlers) {
    if (typeof handlers[handler as keyof SlashCommandHandlers] !== 'function') {
      throw new Error(`Handler ${handler} must be a function`);
    }
  }
}
/**
 * Hook for processing slash commands
 */
export function useSlashCommandProcessor(handlers: SlashCommandHandlers) {
  // Validate handlers on initialization
  try {
    validateHandlers(handlers);
  } catch (error) {
    console.error('Invalid slash command handlers:', error);
    throw error;
  }
  const processCommand = useCallback((input: string): boolean => {
    try {
      const command = parseSlashCommand(input);
      if (!command) {
        return false; // Not a slash command
      }
      // Process the command
      switch (command.command) {
        case 'up':
          handlers.onNavigate('up');
          handlers.onSystemMessage('Navigated up in conversation tree');
          break;
        case 'down':
          handlers.onNavigate('down');
          handlers.onSystemMessage('Navigated down in conversation tree');
          break;
        case 'left':
          handlers.onNavigate('left');
          handlers.onSystemMessage('Navigated left to sibling');
          break;
        case 'right':
          handlers.onNavigate('right');
          handlers.onSystemMessage('Navigated right to sibling');
          break;
        case 'root':
          handlers.onNavigate('root');
          handlers.onSystemMessage('Navigated to root of conversation tree');
          break;
        case 'save':
          handlers.onSave();
          break;
        case 'load':
          handlers.onLoad();
          break;
        case 'help':
          handlers.onHelp();
          break;
        case 'auto':
          handlers.onAuto();
          break;
        case 'fp':
        case 'functional_prompt':
          handlers.onFunctionalPrompt();
          break;
        default:
          handlers.onSystemMessage(`Unknown command: /${command.command}. Type /help for available commands.`);
          break;
      }
      return true; // Command was processed
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      handlers.onSystemMessage(`Command error: ${errorMessage}`);
      console.error('Slash command processing error:', error);
      return true; // Still consumed the input
    }
  }, [handlers]);
  return { processCommand };
}
/**
 * Get help text for slash commands
 */
export function getSlashCommandHelp(): string {
  return `Available Commands:
Navigation:
  /up - Move up in conversation tree (to parent's parent)
  /down - Move down in conversation tree (to first child)
  /left - Move to left sibling
  /right - Move to right sibling
  /root - Move to root of conversation
Bot Management:
  /save - Save bot state to file
  /load - Load bot state from file
  /auto - Toggle autonomous mode (bot continues until no tools used)
Information:
  /help - Show this help message
  /fp - Show functional prompt information
Usage:
- Type commands in the message input
- Use navigation buttons or commands to move through conversation tree
- Current position shown with ► in tree view
- Tree view updates automatically with navigation`;
}
/**
 * Component for displaying slash command help
 */
export const SlashCommandHelp: React.FC<{
  onClose?: () => void;
}> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Slash Commands Help</h2>
          {onClose && (
            <button 
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          )}
        </div>
        <pre className="text-sm whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded">
          {getSlashCommandHelp()}
        </pre>
        {onClose && (
          <div className="mt-4 text-right">
            <button 
              onClick={onClose}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
export default useSlashCommandProcessor;
