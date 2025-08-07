"""
File manager service for bot file operations with defensive validation.
"""

import os
import hashlib
import json
import aiofiles
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass

class StorageError(Exception):
    """Custom exception for storage-related errors."""
    pass

class BotFileMetadata(BaseModel):
    """Metadata for a bot file with defensive validation."""

    filename: str = Field(..., min_length=1, max_length=255)
    size_bytes: int = Field(..., ge=0, le=50_000_000)  # Max 50MB
    created_at: datetime
    modified_at: datetime
    checksum: str = Field(..., min_length=32, max_length=64)  # MD5 or SHA256
    bot_name: Optional[str] = Field(None, max_length=100)
    bot_version: Optional[str] = Field(None, max_length=20)

    @validator('filename')
    def validate_filename(cls, v):
        assert isinstance(v, str), f"filename must be str, got {type(v)}"
        assert v.strip(), "filename cannot be empty"
        assert v.endswith('.bot'), "filename must end with .bot extension"
        # Prevent path traversal
        assert not any(char in v for char in ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']), \
            "filename contains invalid characters"
        return v.strip()

    @validator('checksum')
    def validate_checksum(cls, v):
        assert isinstance(v, str), f"checksum must be str, got {type(v)}"
        assert v.strip(), "checksum cannot be empty"
        assert all(c in '0123456789abcdef' for c in v.lower()), \
            "checksum must be valid hexadecimal"
        return v.lower()

class BotFileInfo(BaseModel):
    """Extended bot file information."""

    metadata: BotFileMetadata
    is_valid: bool
    validation_errors: List[str] = []
    preview: Optional[str] = Field(None, max_length=500)  # First few lines of bot content

class FileUploadRequest(BaseModel):
    """Request model for file upload."""

    filename: str
    overwrite: bool = False

    @validator('filename')
    def validate_filename(cls, v):
        return BotFileMetadata.validate_filename(v)

class FileUploadResponse(BaseModel):
    """Response model for file upload."""

    success: bool
    message: str
    file_info: Optional[BotFileInfo] = None
    warnings: List[str] = []

class FileListResponse(BaseModel):
    """Response model for file listing."""

    files: List[BotFileInfo]
    total_count: int
    total_size_bytes: int

    @validator('total_count')
    def validate_total_count(cls, v):
        assert isinstance(v, int), f"total_count must be int, got {type(v)}"
        assert v >= 0, "total_count cannot be negative"
        return v

class FileDeleteResponse(BaseModel):
    """Response model for file deletion."""

    success: bool
    message: str
    deleted_filename: Optional[str] = None

class BotFileValidationResult:
    """Result of bot file validation."""

    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        assert isinstance(is_valid, bool), f"is_valid must be bool, got {type(is_valid)}"

        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

        # Validate lists
        assert isinstance(self.errors, list), f"errors must be list, got {type(self.errors)}"
        assert isinstance(self.warnings, list), f"warnings must be list, got {type(self.warnings)}"

        for error in self.errors:
            assert isinstance(error, str), f"error must be str, got {type(error)}"
        for warning in self.warnings:
            assert isinstance(warning, str), f"warning must be str, got {type(warning)}"

class FileManager:
    """Manages bot file operations with defensive validation."""

    def __init__(self, storage_dir: str, max_storage_bytes: int = 1_000_000_000):  # 1GB default
        assert isinstance(storage_dir, str), f"storage_dir must be str, got {type(storage_dir)}"
        assert isinstance(max_storage_bytes, int), f"max_storage_bytes must be int, got {type(max_storage_bytes)}"
        assert storage_dir.strip(), "storage_dir cannot be empty"
        assert max_storage_bytes > 0, f"max_storage_bytes must be positive, got {max_storage_bytes}"

        self.storage_dir = os.path.abspath(storage_dir.strip())
        self.max_storage_bytes = max_storage_bytes

        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)

        # Validate directory is writable
        if not os.access(self.storage_dir, os.W_OK):
            raise StorageError(f"Storage directory not writable: {self.storage_dir}")

    async def validate_bot_file(self, content: bytes) -> BotFileValidationResult:
        """Validate bot file content."""
        assert isinstance(content, bytes), f"content must be bytes, got {type(content)}"

        errors = []
        warnings = []

        try:
            # Try to decode as UTF-8
            text_content = content.decode('utf-8')

            # Try to parse as JSON (bot files are typically JSON)
            try:
                bot_data = json.loads(text_content)

                # Basic structure validation
                if not isinstance(bot_data, dict):
                    errors.append("Bot file must contain a JSON object")
                else:
                    # Check for required fields (adjust based on your bot format)
                    required_fields = ['conversation', 'model_params']
                    for field in required_fields:
                        if field not in bot_data:
                            warnings.append(f"Missing recommended field: {field}")

                    # Check for suspicious content
                    if 'api_key' in str(bot_data).lower():
                        warnings.append("File may contain API keys - review before use")

            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format: {str(e)}")

        except UnicodeDecodeError:
            errors.append("File must be valid UTF-8 text")

        # Check file size
        if len(content) > 50_000_000:  # 50MB
            errors.append(f"File too large: {len(content)} bytes")

        result = BotFileValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

        assert isinstance(result, BotFileValidationResult), f"Expected BotFileValidationResult, got {type(result)}"
        return result

    async def save_bot_file(self, filename: str, content: bytes, overwrite: bool = False) -> BotFileInfo:
        """Save bot file to storage."""
        assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
        assert isinstance(content, bytes), f"content must be bytes, got {type(content)}"
        assert isinstance(overwrite, bool), f"overwrite must be bool, got {type(overwrite)}"
        assert filename.strip(), "filename cannot be empty"

        # Check storage limits
        current_size = await self._get_total_storage_size()
        if current_size + len(content) > self.max_storage_bytes:
            raise StorageError(f"Storage limit exceeded: {current_size + len(content)} > {self.max_storage_bytes}")

        file_path = os.path.join(self.storage_dir, filename)

        # Check if file exists
        if os.path.exists(file_path) and not overwrite:
            raise FileValidationError(f"File {filename} already exists")

        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # Verify file was written correctly
        if not os.path.exists(file_path):
            raise StorageError("File save verification failed")

        # Get file stats
        stat = os.stat(file_path)

        # Create metadata
        metadata = BotFileMetadata(
            filename=filename,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            checksum=checksum
        )

        # Validate content
        validation_result = await self.validate_bot_file(content)

        # Create preview
        preview = None
        try:
            text_content = content.decode('utf-8')
            preview = text_content[:500]  # First 500 characters
        except UnicodeDecodeError:
            preview = "Binary content"

        file_info = BotFileInfo(
            metadata=metadata,
            is_valid=validation_result.is_valid,
            validation_errors=validation_result.errors,
            preview=preview
        )

        assert isinstance(file_info, BotFileInfo), f"Expected BotFileInfo, got {type(file_info)}"
        return file_info

    async def file_exists(self, filename: str) -> bool:
        """Check if file exists."""
        assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
        assert filename.strip(), "filename cannot be empty"

        file_path = os.path.join(self.storage_dir, filename)
        exists = os.path.exists(file_path)

        assert isinstance(exists, bool), f"Expected bool, got {type(exists)}"
        return exists

    async def get_file_path(self, filename: str) -> str:
        """Get full path to file."""
        assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
        assert filename.strip(), "filename cannot be empty"

        file_path = os.path.join(self.storage_dir, filename)

        # Security check: ensure path is within storage directory
        abs_file_path = os.path.abspath(file_path)
        if not abs_file_path.startswith(self.storage_dir):
            raise FileValidationError("Invalid file path")

        assert isinstance(abs_file_path, str), f"Expected str, got {type(abs_file_path)}"
        return abs_file_path

    async def delete_file(self, filename: str) -> bool:
        """Delete file from storage."""
        assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
        assert filename.strip(), "filename cannot be empty"

        file_path = await self.get_file_path(filename)

        try:
            os.remove(file_path)
            success = True
        except OSError:
            success = False

        assert isinstance(success, bool), f"Expected bool, got {type(success)}"
        return success

    async def list_files(self, limit: int, offset: int, sort_by: str, sort_order: str) -> Tuple[List[BotFileInfo], int, int]:
        """List files with pagination and sorting."""
        assert isinstance(limit, int), f"limit must be int, got {type(limit)}"
        assert isinstance(offset, int), f"offset must be int, got {type(offset)}"
        assert isinstance(sort_by, str), f"sort_by must be str, got {type(sort_by)}"
        assert isinstance(sort_order, str), f"sort_order must be str, got {type(sort_order)}"

        files = []
        total_size = 0

        # Get all .bot files
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.bot'):
                file_path = os.path.join(self.storage_dir, filename)
                stat = os.stat(file_path)

                # Read file for validation and preview
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()

                checksum = hashlib.sha256(content).hexdigest()
                validation_result = await self.validate_bot_file(content)

                # Create preview
                preview = None
                try:
                    text_content = content.decode('utf-8')
                    preview = text_content[:500]
                except UnicodeDecodeError:
                    preview = "Binary content"

                metadata = BotFileMetadata(
                    filename=filename,
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                    checksum=checksum
                )

                file_info = BotFileInfo(
                    metadata=metadata,
                    is_valid=validation_result.is_valid,
                    validation_errors=validation_result.errors,
                    preview=preview
                )

                files.append(file_info)
                total_size += stat.st_size

        # Sort files
        reverse = sort_order == 'desc'
        if sort_by == 'filename':
            files.sort(key=lambda x: x.metadata.filename, reverse=reverse)
        elif sort_by == 'size_bytes':
            files.sort(key=lambda x: x.metadata.size_bytes, reverse=reverse)
        elif sort_by == 'created_at':
            files.sort(key=lambda x: x.metadata.created_at, reverse=reverse)
        elif sort_by == 'modified_at':
            files.sort(key=lambda x: x.metadata.modified_at, reverse=reverse)

        total_count = len(files)

        # Apply pagination
        paginated_files = files[offset:offset + limit]

        # Validate output
        assert isinstance(paginated_files, list), f"Expected list, got {type(paginated_files)}"
        assert isinstance(total_count, int), f"Expected int, got {type(total_count)}"
        assert isinstance(total_size, int), f"Expected int, got {type(total_size)}"

        return paginated_files, total_count, total_size

    async def _get_total_storage_size(self) -> int:
        """Get total size of all files in storage."""
        total_size = 0

        for filename in os.listdir(self.storage_dir):
            file_path = os.path.join(self.storage_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)

        assert isinstance(total_size, int), f"Expected int, got {type(total_size)}"
        assert total_size >= 0, f"total_size must be non-negative, got {total_size}"

        return total_size

    async def load_bot_from_file(self, filename: str) -> Any:
        """Load a bot instance from file."""
        assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
        assert filename.strip(), "filename cannot be empty"

        file_path = await self.get_file_path(filename)

        if not os.path.exists(file_path):
            raise FileValidationError(f"File {filename} not found")

        try:
            # Import bots framework
            from bots.foundation.base import Bot

            # Load bot from file
            bot = Bot.load(file_path)

            assert bot is not None, "Bot loading returned None"
            return bot

        except Exception as e:
            logger.error(f"Error loading bot from {filename}: {str(e)}")
            raise FileValidationError(f"Failed to load bot: {str(e)}")

    async def save_bot_to_file(self, bot: Any, filename: str, overwrite: bool = False) -> BotFileInfo:
        """Save a bot instance to file."""
        assert bot is not None, "bot cannot be None"
        assert isinstance(filename, str), f"filename must be str, got {type(filename)}"
        assert isinstance(overwrite, bool), f"overwrite must be bool, got {type(overwrite)}"
        assert filename.strip(), "filename cannot be empty"

        # Ensure filename has .bot extension
        if not filename.endswith('.bot'):
            filename = filename + '.bot'

        file_path = os.path.join(self.storage_dir, filename)

        # Check if file exists
        if os.path.exists(file_path) and not overwrite:
            raise FileValidationError(f"File {filename} already exists")

        try:
            # Save bot to file
            bot.save(file_path)

            # Verify file was created
            if not os.path.exists(file_path):
                raise StorageError("Bot save verification failed")

            # Read file content for metadata
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()

            # Create file info
            file_info = await self.save_bot_file(filename, content, overwrite=True)

            assert isinstance(file_info, BotFileInfo), f"Expected BotFileInfo, got {type(file_info)}"
            return file_info

        except Exception as e:
            logger.error(f"Error saving bot to {filename}: {str(e)}")
            raise StorageError(f"Failed to save bot: {str(e)}")