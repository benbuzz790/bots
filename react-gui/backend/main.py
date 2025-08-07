"""
FastAPI main application for the React GUI backend.
Implements REST endpoints and WebSocket support with defensive programming.
"""
import logging
import os
import sys

# Add the main bots directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
bots_root = os.path.join(current_dir, '..', '..')
bots_root = os.path.abspath(bots_root)
if bots_root not in sys.path:
    sys.path.insert(0, bots_root)
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    # Try relative imports first (when imported as a module)
    from .models import BotState
    from .bot_manager import BotManager, set_bot_manager
    from .websocket_handler import WebSocketHandler
    from .file_routes import router as file_router, set_file_manager
    from .file_manager import FileManager
except ImportError:
    # Fall back to absolute imports (when run directly)
    from models import BotState
    from bot_manager import BotManager, set_bot_manager
    from websocket_handler import WebSocketHandler
    from file_routes import router as file_router, set_file_manager
    from file_manager import FileManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
bot_manager: BotManager = None
websocket_handler: WebSocketHandler = None

def _convert_bot_state_for_frontend(bot_state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert bot state field names from snake_case to camelCase for frontend."""
    field_mapping = {
        'conversation_tree': 'conversationTree',
        'current_node_id': 'currentNodeId',
        'is_connected': 'isConnected',
        'is_thinking': 'isThinking',
        'react_flow_data': 'reactFlowData'
    }

    converted = {}
    for key, value in bot_state_dict.items():
        new_key = field_mapping.get(key, key)

        # Special handling for conversation_tree - convert nested ConversationNode objects
        if key == 'conversation_tree' and isinstance(value, dict):
            converted_tree = {}
            for node_id, node in value.items():
                if hasattr(node, 'dict'):
                    # Pydantic model - convert to dict
                    node_dict = node.dict()
                elif isinstance(node, dict):
                    # Already a dict
                    node_dict = node
                else:
                    # Fallback
                    node_dict = node

                # Convert node field names from snake_case to camelCase
                converted_node = {}
                node_field_mapping = {
                    'is_current': 'isCurrent',
                    'tool_calls': 'toolCalls'
                }

                for node_key, node_value in node_dict.items():
                    converted_node[node_field_mapping.get(node_key, node_key)] = node_value

                converted_tree[node_id] = converted_node
            converted[new_key] = converted_tree
        else:
            converted[new_key] = value

    return converted
"""
FastAPI main application for the React GUI backend.
Implements REST endpoints and WebSocket support with defensive programming.
"""
import logging
import os
import sys

# Add the main bots directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
bots_root = os.path.join(current_dir, '..', '..')
bots_root = os.path.abspath(bots_root)
if bots_root not in sys.path:
    sys.path.insert(0, bots_root)
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    # Try relative imports first (when imported as a module)
    from .models import BotState
    from .bot_manager import BotManager, set_bot_manager
    from .websocket_handler import WebSocketHandler
    from .file_routes import router as file_router, set_file_manager
    from .file_manager import FileManager
except ImportError:
    # Fall back to absolute imports (when run directly)
    from models import BotState
    from bot_manager import BotManager, set_bot_manager
    from websocket_handler import WebSocketHandler
    from file_routes import router as file_router, set_file_manager
    from file_manager import FileManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
bot_manager: BotManager = None
websocket_handler: WebSocketHandler = None
class CreateBotRequest(BaseModel):
    """Request model for creating a bot."""
    name: str = "Default Bot"

class CreateBotResponse(BaseModel):
    """Response model for bot creation."""
    bot_id: str
    name: str
    message: str

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str
    bots_count: int

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: str
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global bot_manager, websocket_handler
    logger.info("Starting Bot GUI backend...")

    # Startup
    try:
        # Initialize services
        bot_manager = BotManager()
        set_bot_manager(bot_manager)  # Set global instance for file routes
        websocket_handler = WebSocketHandler(bot_manager)

        # Initialize file manager (you may want to configure the storage directory)
        import tempfile
        import os
        storage_dir = os.environ.get('BOT_STORAGE_DIR', tempfile.gettempdir())
        file_manager = FileManager(storage_dir)
        set_file_manager(file_manager)

        logger.info("Services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Bot GUI backend...")
app = FastAPI(
    title="Bot GUI Backend",
    description="FastAPI backend for React GUI interface to the bots framework",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(file_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with defensive validation."""
    try:
        bots = await bot_manager.list_bots_async() if bot_manager else []
        response = HealthResponse(
            status="healthy",
            message="Bot GUI backend is running",
            bots_count=len(bots)
        )
        logger.info(f"Health check: {response.bots_count} bots active")
        return response
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
@app.get("/api/debug")
async def debug_info():
    """Debug endpoint to check environment."""
    import os
    import sys
    return {
        "cwd": os.getcwd(),
        "python_path": sys.path[:5],  # First 5 entries
        "bot_manager_exists": bot_manager is not None,
        "env_vars": {k: v for k, v in os.environ.items() if 'ANTHROPIC' in k or 'OPENAI' in k}
    }
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Bot GUI backend server...")
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
@app.post("/api/bots/create", response_model=CreateBotResponse)
async def create_bot(request: CreateBotRequest) -> CreateBotResponse:
    """Create a new bot instance with defensive validation."""
    try:
        if bot_manager is None:
            logger.error("bot_manager is None in REST API")
            raise HTTPException(status_code=500, detail="Bot manager not initialized")

        bot_id = bot_manager.create_bot(request.name.strip())
        response = CreateBotResponse(
            bot_id=bot_id,
            name=request.name.strip(),
            message="Bot created successfully"
        )
        logger.info(f"Created bot via REST API: {bot_id}")
        return response
    except Exception as e:
        logger.error(f"Bot creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {str(e)}")
@app.get("/api/bots/{bot_id}")
async def get_bot(bot_id: str) -> Dict[str, Any]:
    """Get bot state by ID with defensive validation."""
    try:
        # Get bot state
        state = await bot_manager.get_bot_state(bot_id)
        if state is None:
            raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

        # Convert to frontend format with proper field name conversion
        response = _convert_bot_state_for_frontend(state.dict())
        logger.info(f"Retrieved bot state via REST API: {bot_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get bot error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bot: {str(e)}")

@app.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: str) -> Dict[str, str]:
    """Delete a bot by ID with defensive validation."""
    try:
        success = bot_manager.delete_bot(bot_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")

        response = {
            "message": "Bot deleted successfully",
            "bot_id": bot_id
        }
        logger.info(f"Deleted bot via REST API: {bot_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete bot error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete bot: {str(e)}")

@app.get("/api/bots")
async def list_bots() -> Dict[str, Any]:
    """List all bots with defensive validation."""
    try:
        if bot_manager is None:
            logger.error("bot_manager is None in REST API")
            raise HTTPException(status_code=500, detail="Bot manager not initialized")

        bots_list = await bot_manager.list_bots_async()
        return {"bots": bots_list}
    except Exception as e:
        logger.error(f"List bots error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list bots: {str(e)}")
@app.websocket("/ws/{connection_id}")
async def websocket_chat(websocket: WebSocket, connection_id: str):
    """WebSocket endpoint for real-time chat with defensive validation."""

# WebSocket endpoint without connection_id (for frontend compatibility)
@app.websocket("/ws")
async def websocket_simple(websocket: WebSocket):
    """Simple WebSocket endpoint for frontend compatibility."""
    if websocket_handler is None:
        logger.error("WebSocket handler not initialized")
        await websocket.close(code=1011, reason="WebSocket handler not initialized")
        return
    logger.info("WebSocket connection attempt (simple)")
    try:
        await websocket_handler.handle_connection(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

    if websocket_handler is None:
        logger.error("WebSocket handler not initialized")
        await websocket.close(code=1011, reason="WebSocket handler not initialized")
        return
    logger.info(f"WebSocket connection attempt: {connection_id}")
    try:
        await websocket_handler.handle_connection(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Bot GUI Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Bot GUI backend server...")
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise