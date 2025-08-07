import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './components/App';
import './index.css';

// Defensive programming: Validate that we have a root element
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Failed to find the root element. Make sure index.html contains a div with id="root"');
}

// Error boundary component for top-level error handling
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Application error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
          <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Application Error</h1>
            <p className="text-gray-700 mb-4">
              Something went wrong. Please refresh the page or contact support if the problem persists.
            </p>
            <details className="mb-4">
              <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                Technical Details
              </summary>
              <pre className="mt-2 text-xs text-gray-500 bg-gray-50 p-2 rounded overflow-auto">
                {this.state.error?.message}
              </pre>
            </details>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Create root and render with error boundary
try {
  const root = ReactDOM.createRoot(rootElement);
  
  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
} catch (error) {
  console.error('Failed to render React application:', error);
  
  // Fallback rendering in case React fails to initialize
  rootElement.innerHTML = `
    <div style="
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #f3f4f6;
      font-family: system-ui, -apple-system, sans-serif;
    ">
      <div style="
        background: white;
        padding: 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        max-width: 28rem;
        width: 100%;
        text-align: center;
      ">
        <h1 style="color: #dc2626; margin-bottom: 1rem;">Failed to Load Application</h1>
        <p style="color: #374151; margin-bottom: 1rem;">
          The React application failed to initialize. Please check the console for details.
        </p>
        <button 
          onclick="window.location.reload()" 
          style="
            width: 100%;
            background-color: #3b82f6;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 0.25rem;
            cursor: pointer;
          "
        >
          Reload Page
        </button>
      </div>
    </div>
  `;
}
