import React, { useEffect } from 'react';
import { ChatInterface } from './ChatInterface';
import { useBotStore } from '../store/botStore';

interface AppProps {}

export const App: React.FC<AppProps> = () => {
  const { connect, connected, error, createBot, currentBotId } = useBotStore();
  const [initialized, setInitialized] = React.useState(false);

  useEffect(() => {
    // Connect to WebSocket on app start
    const initializeApp = async () => {
      // Prevent multiple initializations
      if (connected && currentBotId) {
        return;
      }
      
      if (initialized) {
        return;
      }
      setInitialized(true);
      
          console.log('Creating default bot...');
      try {
        await connect();
        
        // Create a default bot if none exists
        if (!currentBotId) {
          await createBot('Default Bot');
        }
      } catch (error) {
        console.error('Failed to initialize app:', error);
      }
    };

    initializeApp();
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Connection Error</h1>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!connected) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-700 text-center">Connecting to bot framework...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-none mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              Bots Framework GUI
            </h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-none mx-auto px-4 sm:px-6 lg:px-8 py-6 min-h-screen">
        {currentBotId ? (
          <ChatInterface botId={currentBotId} />
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-700">No bot available. Creating default bot...</p>
          </div>
        )}
      </main>
    </div>
  );
};
