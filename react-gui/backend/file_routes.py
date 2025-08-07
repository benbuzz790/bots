"""
FastAPI routes for bot file operations.
"""
import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import Optional
try:
    from .file_manager import (
        FileManager,
        FileUploadResponse,
        FileListResponse,
        FileDeleteResponse,
        FileValidationError,
        StorageError
    )
except ImportError:
    from file_manager import (
        FileManager,
        FileUploadResponse,
        FileListResponse,
        FileDeleteResponse,
        FileValidationError,
        StorageError
    )
logger = logging.getLogger(__name__)
# Create router
router = APIRouter(prefix="/api/files", tags=["files"])
# Global file manager instance (will be initialized in main.py)
file_manager: Optional[FileManager] = None
def get_file_manager() -> FileManager:
    """Dependency to get file manager instance."""
    if file_manager is None:
        raise HTTPException(status_code=500, detail="File manager not initialized")
    assert isinstance(file_manager, FileManager), f"Expected FileManager, got {type(file_manager)}"
    return file_manager
def set_file_manager(fm: FileManager) -> None:
    """Set the global file manager instance."""
    global file_manager
    assert isinstance(fm, FileManager), f"Expected FileManager, got {type(fm)}"
    file_manager = fm
@router.post("/load-bot/{filename}")
async def load_bot_from_file(
    filename: str,
    fm: FileManager = Depends(get_file_manager)
) -> dict:
    """Load a bot instance from file and return bot ID."""
    # Input validation
    assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
    assert filename.strip(), "filename cannot be empty"
    assert isinstance(fm, FileManager), f"Expected FileManager, got {type(fm)}"
    try:
        # Validate filename format
        if not filename.endswith('.bot'):
            raise FileValidationError("Invalid file extension")
        # Check if file exists
        if not await fm.file_exists(filename):
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        # Load bot from file
        bot = await fm.load_bot_from_file(filename)
        # Import bot manager to register the loaded bot
        try:
            from .bot_manager import get_bot_manager
        except ImportError:
            from bot_manager import get_bot_manager
        bot_manager = get_bot_manager()
        # Register the loaded bot
        bot_id = await bot_manager.register_loaded_bot(bot, filename)
        response = {
            "success": True,
            "message": f"Successfully loaded bot from {filename}",
            "bot_id": bot_id,
            "filename": filename
        }
        # Output validation
        assert isinstance(response, dict), f"Expected dict, got {type(response)}"
        assert response["success"] is True, "Response success flag must be True"
        assert isinstance(response["bot_id"], str), f"bot_id must be str, got {type(response['bot_id'])}"
        logger.info(f"Bot loaded from file: {filename} -> {bot_id}")
        return response
    except FileValidationError as e:
        logger.warning(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in load_bot_from_file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during bot loading")
@router.post("/save-bot/{bot_id}")
async def save_bot_to_file(
    bot_id: str,
    filename: str = Form(...),
    overwrite: bool = Form(False),
    fm: FileManager = Depends(get_file_manager)
) -> dict:
    """Save a bot instance to file."""
    # Input validation
    assert isinstance(bot_id, str), f"bot_id must be str, got {type(bot_id)}"
    assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
    assert isinstance(overwrite, bool), f"overwrite must be bool, got {type(overwrite)}"
    assert isinstance(fm, FileManager), f"Expected FileManager, got {type(fm)}"
    assert bot_id.strip(), "bot_id cannot be empty"
    assert filename.strip(), "filename cannot be empty"
    try:
        # Import bot manager to get the bot
        try:
            from .bot_manager import get_bot_manager
        except ImportError:
            from bot_manager import get_bot_manager
        bot_manager = get_bot_manager()
        # Get bot instance
        bot = await bot_manager.get_bot(bot_id)
        if bot is None:
            raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
        # Save bot to file
        file_info = await fm.save_bot_to_file(bot, filename, overwrite)
        response = {
            "success": True,
            "message": f"Successfully saved bot to {filename}",
            "bot_id": bot_id,
            "file_info": file_info.dict()
        }
        # Output validation
        assert isinstance(response, dict), f"Expected dict, got {type(response)}"
        assert response["success"] is True, "Response success flag must be True"
        logger.info(f"Bot saved to file: {bot_id} -> {filename}")
        return response
    except FileValidationError as e:
        logger.warning(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        logger.error(f"Storage error: {str(e)}")
        raise HTTPException(status_code=507, detail=f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in save_bot_to_file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during bot saving")
