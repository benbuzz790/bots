import os
import sys
import subprocess
import time
import signal
import atexit
from pathlib import Path


class BotViewerTest:
    """Test environment for the Bot Viewer application"""

    def __init__(self):
        self.project_root = self.find_project_root()
        self.bot_viewer_dir = self.project_root / 'bot-viewer'
        self.backend_dir = self.bot_viewer_dir / 'backend'
        self.frontend_dir = self.bot_viewer_dir / 'frontend'
        self.backend_process = None
        self.frontend_process = None

    def find_project_root(self):
        """Find the project root directory containing the bot-viewer folder"""
        current = Path(__file__).parent
        while current != current.parent:
            if (current / 'bot-viewer').exists():
                return current
            current = current.parent
        raise FileNotFoundError(
            'Could not find project root with bot-viewer directory')

    def setup_environment(self):
        """Set up the development environment"""
        print('\nChecking and setting up environment...')
        try:
            npm_version = subprocess.run(['powershell', '-Command',
                'npm -v'], capture_output=True, text=True, check=True
                ).stdout.strip()
            print(f'✓ npm {npm_version} is available')
        except subprocess.CalledProcessError:
            print('✗ npm not found')
            print(
                'Please ensure Node.js and npm are installed and in your system PATH'
                )
            print(
                'You can download Node.js (which includes npm) from https://nodejs.org/'
                )
            sys.exit(1)
        print('\nSetting up backend...')
        if not self.backend_dir.exists():
            print('Creating backend directory...')
            self.backend_dir.mkdir(parents=True)
        print('Installing backend dependencies...')
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install',
                'fastapi==0.104.1', 'uvicorn==0.24.0',
                'python-multipart==0.0.6'], check=True)
            print('✓ Backend dependencies installed')
        except subprocess.CalledProcessError as e:
            print(f'✗ Failed to install backend dependencies: {e}')
            sys.exit(1)
        print('\nSetting up frontend...')
        if not self.frontend_dir.exists():
            print('Creating frontend directory...')
            self.frontend_dir.mkdir(parents=True)
        if not (self.frontend_dir / 'package.json').exists():
            print('Initializing new React application...')
            try:
                subprocess.run(['powershell', '-Command', 'npm init -y'],
                    cwd=str(self.frontend_dir), check=True)
                print('Installing React dependencies...')
                subprocess.run(['powershell', '-Command',
                    'npm install react react-dom react-scripts @types/react @types/react-dom typescript @types/node'
                    ], cwd=str(self.frontend_dir), check=True)
                print('✓ React application initialized')
            except subprocess.CalledProcessError as e:
                print(f'✗ Failed to initialize React application: {e}')
                sys.exit(1)
        print('Installing frontend dependencies...')
        try:
            subprocess.run(['powershell', '-Command', 'npm install'], cwd=
                str(self.frontend_dir), check=True)
            print('✓ Frontend dependencies installed')
        except subprocess.CalledProcessError as e:
            print(f'✗ Failed to install frontend dependencies: {e}')
            sys.exit(1)
        print('\nEnvironment setup complete!')

    def start_servers(self):
        """Start both frontend and backend servers"""
        backend_env = os.environ.copy()
        backend_env['PYTHONPATH'] = str(self.project_root)
        self.backend_process = subprocess.Popen([sys.executable, '-m',
            'uvicorn', 'main:app', '--reload', '--port', '8000'], cwd=str(
            self.backend_dir), env=backend_env)
        
        # Add BROWSER=none to frontend environment
        frontend_env = os.environ.copy()
        frontend_env['BROWSER'] = 'none'
        self.frontend_process = subprocess.Popen(['powershell', '-Command',
            'npm start'], cwd=str(self.frontend_dir), env=frontend_env)
        atexit.register(self.cleanup)

    def cleanup(self):
        """Clean up server processes"""
        print('\nShutting down servers...')
        if self.backend_process:
            self.backend_process.terminate()
        if self.frontend_process:
            self.frontend_process.terminate()
        try:
            if self.backend_process:
                self.backend_process.wait(timeout=5)
            if self.frontend_process:
                self.frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if self.backend_process:
                self.backend_process.kill()
            if self.frontend_process:
                self.frontend_process.kill()
        print('Servers stopped')

    def run(self):
        """Run the test environment"""
        print('Starting Bot Viewer test environment...')
        self.setup_environment()
        self.start_servers()
        print('\nBot Viewer is running!')
        print('Frontend: http://localhost:3000')
        print('Backend: http://localhost:8000')
        print('\nPress Ctrl+C to stop the servers and exit')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print('\nReceived shutdown signal...')


if __name__ == '__main__':
    viewer = BotViewerTest()
    viewer.run()
