"""
Comprehensive tests for file operations API endpoints.
"""

import pytest
import json
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Import the application components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.main import app
from backend.file_manager import FileManager, BotFileValidationResult, FileValidationError, StorageError
from backend.bot_manager import BotManager

class TestFileAPI:
    """Test suite for file operations API with comprehensive edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def file_manager(self, temp_storage):
        """Create file manager with temporary storage."""
        return FileManager(temp_storage)

    @pytest.fixture
    def valid_bot_content(self):
        """Valid bot file content for testing."""
        return json.dumps({
            "conversation": {"root": {"content": "test", "role": "user"}},
            "model_params": {"model": "gpt-4", "temperature": 0.7},
            "tools": [],
            "metadata": {"created": "2024-01-01T00:00:00Z"}
        }).encode('utf-8')

    @pytest.fixture
    def invalid_bot_content(self):
        """Invalid bot file content for testing."""
        return b"invalid json content"

    def test_upload_valid_bot_file(self, client, valid_bot_content):
        """Test uploading a valid bot file."""
        # Create test file
        files = {"file": ("test_bot.bot", valid_bot_content, "application/octet-stream")}
        data = {"overwrite": "false"}

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.validate_bot_file = AsyncMock(return_value=BotFileValidationResult(True, [], []))
            mock_fm.file_exists = AsyncMock(return_value=False)
            mock_fm.save_bot_file = AsyncMock(return_value=Mock(
                metadata=Mock(filename="test_bot.bot", size_bytes=len(valid_bot_content)),
                is_valid=True,
                validation_errors=[],
                preview="test preview"
            ))
            mock_get_fm.return_value = mock_fm

            response = client.post("/api/files/upload", files=files, data=data)

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        response_data = response.json()
        assert isinstance(response_data, dict), f"Response must be dict, got {type(response_data)}"
        assert response_data["success"] is True, "Upload should succeed"
        assert "message" in response_data, "Response must have message"
        assert isinstance(response_data["message"], str), "Message must be string"
        assert "file_info" in response_data, "Response must have file_info"

    def test_upload_invalid_extension(self, client, valid_bot_content):
        """Test uploading file with invalid extension."""
        files = {"file": ("test_file.txt", valid_bot_content, "text/plain")}
        data = {"overwrite": "false"}

        response = client.post("/api/files/upload", files=files, data=data)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "detail" in response_data, "Error response must have detail"
        assert "extension" in response_data["detail"].lower(), "Error should mention extension"

    def test_upload_empty_file(self, client):
        """Test uploading empty file."""
        files = {"file": ("empty.bot", b"", "application/octet-stream")}
        data = {"overwrite": "false"}

        response = client.post("/api/files/upload", files=files, data=data)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "empty" in response_data["detail"].lower(), "Error should mention empty file"

    def test_upload_oversized_file(self, client):
        """Test uploading file that exceeds size limit."""
        # Create 51MB file (exceeds 50MB limit)
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.bot", large_content, "application/octet-stream")}
        data = {"overwrite": "false"}

        response = client.post("/api/files/upload", files=files, data=data)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "large" in response_data["detail"].lower(), "Error should mention file size"

    def test_upload_invalid_json(self, client, invalid_bot_content):
        """Test uploading file with invalid JSON content."""
        files = {"file": ("invalid.bot", invalid_bot_content, "application/octet-stream")}
        data = {"overwrite": "false"}

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.validate_bot_file = AsyncMock(return_value=BotFileValidationResult(
                False, ["Invalid JSON format"], []
            ))
            mock_get_fm.return_value = mock_fm

            response = client.post("/api/files/upload", files=files, data=data)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "invalid" in response_data["detail"].lower(), "Error should mention invalid content"

    def test_upload_existing_file_no_overwrite(self, client, valid_bot_content):
        """Test uploading file that already exists without overwrite."""
        files = {"file": ("existing.bot", valid_bot_content, "application/octet-stream")}
        data = {"overwrite": "false"}

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.validate_bot_file = AsyncMock(return_value=BotFileValidationResult(True, [], []))
            mock_fm.file_exists = AsyncMock(return_value=True)
            mock_get_fm.return_value = mock_fm

            response = client.post("/api/files/upload", files=files, data=data)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "exists" in response_data["detail"].lower(), "Error should mention file exists"

    def test_upload_storage_error(self, client, valid_bot_content):
        """Test upload with storage error."""
        files = {"file": ("test.bot", valid_bot_content, "application/octet-stream")}
        data = {"overwrite": "false"}

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.validate_bot_file = AsyncMock(return_value=BotFileValidationResult(True, [], []))
            mock_fm.file_exists = AsyncMock(return_value=False)
            mock_fm.save_bot_file = AsyncMock(side_effect=StorageError("Disk full"))
            mock_get_fm.return_value = mock_fm

            response = client.post("/api/files/upload", files=files, data=data)

        assert response.status_code == 507, f"Expected 507, got {response.status_code}"

        response_data = response.json()
        assert "storage" in response_data["detail"].lower(), "Error should mention storage"

    def test_download_existing_file(self, client):
        """Test downloading an existing file."""
        filename = "test.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=True)
            mock_fm.get_file_path = AsyncMock(return_value="/tmp/test.bot")
            mock_get_fm.return_value = mock_fm

            with patch('os.path.exists', return_value=True), \
                 patch('os.access', return_value=True):
                response = client.get(f"/api/files/download/{filename}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers["content-type"] == "application/octet-stream"

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist."""
        filename = "nonexistent.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=False)
            mock_get_fm.return_value = mock_fm

            response = client.get(f"/api/files/download/{filename}")

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

        response_data = response.json()
        assert "not found" in response_data["detail"].lower()

    def test_download_invalid_filename(self, client):
        """Test downloading with invalid filename characters."""
        invalid_filenames = [
            "../../../etc/passwd",
            "file<script>alert(1)</script>.bot",
            "file|rm -rf /.bot",
            "file?.bot"
        ]

        for filename in invalid_filenames:
            response = client.get(f"/api/files/download/{filename}")
            assert response.status_code == 400, f"Expected 400 for {filename}, got {response.status_code}"

    def test_download_non_bot_extension(self, client):
        """Test downloading file without .bot extension."""
        filename = "test.txt"

        response = client.get(f"/api/files/download/{filename}")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "extension" in response_data["detail"].lower()

    def test_list_files_default_params(self, client):
        """Test listing files with default parameters."""
        mock_files = [
            Mock(
                metadata=Mock(filename="bot1.bot", size_bytes=1024),
                is_valid=True,
                validation_errors=[],
                preview="preview1"
            ),
            Mock(
                metadata=Mock(filename="bot2.bot", size_bytes=2048),
                is_valid=False,
                validation_errors=["Invalid format"],
                preview="preview2"
            )
        ]

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.list_files = AsyncMock(return_value=(mock_files, 2, 3072))
            mock_get_fm.return_value = mock_fm

            response = client.get("/api/files/list")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        response_data = response.json()
        assert isinstance(response_data, dict), f"Response must be dict, got {type(response_data)}"
        assert "files" in response_data, "Response must have files"
        assert "total_count" in response_data, "Response must have total_count"
        assert "total_size_bytes" in response_data, "Response must have total_size_bytes"
        assert isinstance(response_data["files"], list), "Files must be list"
        assert response_data["total_count"] == 2, "Total count should be 2"
        assert response_data["total_size_bytes"] == 3072, "Total size should be 3072"

    def test_list_files_with_pagination(self, client):
        """Test listing files with pagination parameters."""
        params = {
            "limit": 10,
            "offset": 5,
            "sort_by": "filename",
            "sort_order": "asc"
        }

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.list_files = AsyncMock(return_value=([], 0, 0))
            mock_get_fm.return_value = mock_fm

            response = client.get("/api/files/list", params=params)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify the mock was called with correct parameters
        mock_fm.list_files.assert_called_once_with(
            limit=10, offset=5, sort_by="filename", sort_order="asc"
        )

    def test_list_files_invalid_params(self, client):
        """Test listing files with invalid parameters."""
        invalid_params = [
            {"limit": 0},  # Below minimum
            {"limit": 1001},  # Above maximum
            {"offset": -1},  # Negative offset
            {"sort_by": "invalid_field"},  # Invalid sort field
            {"sort_order": "invalid_order"}  # Invalid sort order
        ]

        for params in invalid_params:
            response = client.get("/api/files/list", params=params)
            assert response.status_code == 422, f"Expected 422 for {params}, got {response.status_code}"

    def test_delete_existing_file(self, client):
        """Test deleting an existing file."""
        filename = "test.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(side_effect=[True, False])  # Exists before, not after
            mock_fm.delete_file = AsyncMock(return_value=True)
            mock_get_fm.return_value = mock_fm

            response = client.delete(f"/api/files/delete/{filename}?confirm=true")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        response_data = response.json()
        assert response_data["success"] is True, "Delete should succeed"
        assert response_data["deleted_filename"] == filename, "Should return deleted filename"

    def test_delete_without_confirmation(self, client):
        """Test deleting file without confirmation."""
        filename = "test.bot"

        response = client.delete(f"/api/files/delete/{filename}")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

        response_data = response.json()
        assert "confirmation" in response_data["detail"].lower()

    def test_delete_nonexistent_file(self, client):
        """Test deleting a file that doesn't exist."""
        filename = "nonexistent.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=False)
            mock_get_fm.return_value = mock_fm

            response = client.delete(f"/api/files/delete/{filename}?confirm=true")

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_delete_invalid_filename(self, client):
        """Test deleting with invalid filename."""
        invalid_filename = "../../../important.file"

        response = client.delete(f"/api/files/delete/{invalid_filename}?confirm=true")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    def test_delete_failure(self, client):
        """Test delete operation failure."""
        filename = "test.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=True)
            mock_fm.delete_file = AsyncMock(return_value=False)  # Delete fails
            mock_get_fm.return_value = mock_fm

            response = client.delete(f"/api/files/delete/{filename}?confirm=true")

        assert response.status_code == 500, f"Expected 500, got {response.status_code}"

    def test_load_bot_success(self, client):
        """Test successful bot loading."""
        filename = "test.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm, \
             patch('backend.file_routes.get_bot_manager') as mock_get_bm:

            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=True)
            mock_fm.load_bot_from_file = AsyncMock(return_value=Mock())
            mock_get_fm.return_value = mock_fm

            mock_bm = Mock()
            mock_bm.register_loaded_bot = AsyncMock(return_value="bot123")
            mock_get_bm.return_value = mock_bm

            response = client.post(f"/api/files/load-bot/{filename}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        response_data = response.json()
        assert response_data["success"] is True, "Load should succeed"
        assert response_data["bot_id"] == "bot123", "Should return bot ID"
        assert response_data["filename"] == filename, "Should return filename"

    def test_load_bot_nonexistent_file(self, client):
        """Test loading bot from nonexistent file."""
        filename = "nonexistent.bot"

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=False)
            mock_get_fm.return_value = mock_fm

            response = client.post(f"/api/files/load-bot/{filename}")

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_save_bot_success(self, client):
        """Test successful bot saving."""
        bot_id = "bot123"
        data = {"filename": "saved_bot.bot", "overwrite": "false"}

        with patch('backend.file_routes.get_file_manager') as mock_get_fm, \
             patch('backend.file_routes.get_bot_manager') as mock_get_bm:

            mock_bm = Mock()
            mock_bm.get_bot = AsyncMock(return_value=Mock())  # Return mock bot
            mock_get_bm.return_value = mock_bm

            mock_fm = Mock()
            mock_fm.save_bot_to_file = AsyncMock(return_value=Mock(
                dict=Mock(return_value={"filename": "saved_bot.bot"})
            ))
            mock_get_fm.return_value = mock_fm

            response = client.post(f"/api/files/save-bot/{bot_id}", data=data)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        response_data = response.json()
        assert response_data["success"] is True, "Save should succeed"
        assert response_data["bot_id"] == bot_id, "Should return bot ID"

    def test_save_bot_nonexistent_bot(self, client):
        """Test saving nonexistent bot."""
        bot_id = "nonexistent"
        data = {"filename": "test.bot", "overwrite": "false"}

        with patch('backend.file_routes.get_bot_manager') as mock_get_bm:
            mock_bm = Mock()
            mock_bm.get_bot = AsyncMock(return_value=None)  # Bot not found
            mock_get_bm.return_value = mock_bm

            response = client.post(f"/api/files/save-bot/{bot_id}", data=data)

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

class TestFileManagerUnit:
    """Unit tests for FileManager class."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def file_manager(self, temp_storage):
        """Create file manager with temporary storage."""
        return FileManager(temp_storage)

    def test_init_valid_directory(self, temp_storage):
        """Test FileManager initialization with valid directory."""
        fm = FileManager(temp_storage)
        assert fm.storage_dir == os.path.abspath(temp_storage)
        assert fm.max_storage_bytes == 1_000_000_000  # Default 1GB

    def test_init_invalid_directory_type(self):
        """Test FileManager initialization with invalid directory type."""
        with pytest.raises(AssertionError, match="storage_dir must be str"):
            FileManager(123)

    def test_init_empty_directory(self):
        """Test FileManager initialization with empty directory."""
        with pytest.raises(AssertionError, match="storage_dir cannot be empty"):
            FileManager("")

    def test_init_invalid_max_storage(self, temp_storage):
        """Test FileManager initialization with invalid max storage."""
        with pytest.raises(AssertionError, match="max_storage_bytes must be positive"):
            FileManager(temp_storage, -1)

    @pytest.mark.asyncio
    async def test_validate_bot_file_valid_json(self, file_manager):
        """Test validating valid bot file content."""
        valid_content = json.dumps({
            "conversation": {"root": {"content": "test"}},
            "model_params": {"model": "gpt-4"}
        }).encode('utf-8')

        result = await file_manager.validate_bot_file(valid_content)

        assert isinstance(result, BotFileValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_bot_file_invalid_json(self, file_manager):
        """Test validating invalid JSON content."""
        invalid_content = b"invalid json"

        result = await file_manager.validate_bot_file(invalid_content)

        assert isinstance(result, BotFileValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("json" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_bot_file_non_utf8(self, file_manager):
        """Test validating non-UTF8 content."""
        non_utf8_content = b'\xff\xfe\x00\x00'  # Invalid UTF-8

        result = await file_manager.validate_bot_file(non_utf8_content)

        assert isinstance(result, BotFileValidationResult)
        assert result.is_valid is False
        assert any("utf-8" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_bot_file_oversized(self, file_manager):
        """Test validating oversized file."""
        oversized_content = b"x" * (51 * 1024 * 1024)  # 51MB

        result = await file_manager.validate_bot_file(oversized_content)

        assert isinstance(result, BotFileValidationResult)
        assert result.is_valid is False
        assert any("large" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_bot_file_invalid_input_type(self, file_manager):
        """Test validating with invalid input type."""
        with pytest.raises(AssertionError, match="content must be bytes"):
            await file_manager.validate_bot_file("string instead of bytes")

    @pytest.mark.asyncio
    async def test_save_bot_file_success(self, file_manager):
        """Test successful bot file saving."""
        filename = "test.bot"
        content = json.dumps({"test": "data"}).encode('utf-8')

        file_info = await file_manager.save_bot_file(filename, content)

        assert isinstance(file_info, file_manager.__class__.__module__.split('.')[-1] + '.BotFileInfo')
        assert file_info.metadata.filename == filename
        assert file_info.metadata.size_bytes == len(content)
        assert file_info.is_valid is True

        # Verify file was actually created
        file_path = os.path.join(file_manager.storage_dir, filename)
        assert os.path.exists(file_path)

        with open(file_path, 'rb') as f:
            saved_content = f.read()
        assert saved_content == content

    @pytest.mark.asyncio
    async def test_save_bot_file_invalid_filename_type(self, file_manager):
        """Test saving with invalid filename type."""
        with pytest.raises(AssertionError, match="filename must be str"):
            await file_manager.save_bot_file(123, b"content")

    @pytest.mark.asyncio
    async def test_save_bot_file_empty_filename(self, file_manager):
        """Test saving with empty filename."""
        with pytest.raises(AssertionError, match="filename cannot be empty"):
            await file_manager.save_bot_file("", b"content")

    @pytest.mark.asyncio
    async def test_save_bot_file_invalid_content_type(self, file_manager):
        """Test saving with invalid content type."""
        with pytest.raises(AssertionError, match="content must be bytes"):
            await file_manager.save_bot_file("test.bot", "string content")

    @pytest.mark.asyncio
    async def test_save_bot_file_existing_no_overwrite(self, file_manager):
        """Test saving over existing file without overwrite."""
        filename = "existing.bot"
        content = b"test content"

        # Create existing file
        await file_manager.save_bot_file(filename, content)

        # Try to save again without overwrite
        with pytest.raises(FileValidationError, match="already exists"):
            await file_manager.save_bot_file(filename, content, overwrite=False)

    @pytest.mark.asyncio
    async def test_save_bot_file_storage_limit_exceeded(self, temp_storage):
        """Test saving file that exceeds storage limit."""
        # Create file manager with very small storage limit
        fm = FileManager(temp_storage, max_storage_bytes=100)

        filename = "large.bot"
        content = b"x" * 200  # Exceeds 100 byte limit

        with pytest.raises(StorageError, match="Storage limit exceeded"):
            await fm.save_bot_file(filename, content)

    @pytest.mark.asyncio
    async def test_file_exists_true(self, file_manager):
        """Test file_exists returns True for existing file."""
        filename = "test.bot"
        content = b"test"

        # Create file
        await file_manager.save_bot_file(filename, content)

        # Check existence
        exists = await file_manager.file_exists(filename)
        assert exists is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, file_manager):
        """Test file_exists returns False for non-existing file."""
        filename = "nonexistent.bot"

        exists = await file_manager.file_exists(filename)
        assert exists is False

    @pytest.mark.asyncio
    async def test_file_exists_invalid_filename_type(self, file_manager):
        """Test file_exists with invalid filename type."""
        with pytest.raises(AssertionError, match="filename must be str"):
            await file_manager.file_exists(123)

    @pytest.mark.asyncio
    async def test_get_file_path_valid(self, file_manager):
        """Test getting valid file path."""
        filename = "test.bot"

        path = await file_manager.get_file_path(filename)

        expected_path = os.path.join(file_manager.storage_dir, filename)
        assert path == os.path.abspath(expected_path)

    @pytest.mark.asyncio
    async def test_get_file_path_traversal_attempt(self, file_manager):
        """Test path traversal prevention."""
        malicious_filename = "../../../etc/passwd"

        with pytest.raises(FileValidationError, match="Invalid file path"):
            await file_manager.get_file_path(malicious_filename)

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_manager):
        """Test successful file deletion."""
        filename = "test.bot"
        content = b"test"

        # Create file
        await file_manager.save_bot_file(filename, content)
        assert await file_manager.file_exists(filename) is True

        # Delete file
        success = await file_manager.delete_file(filename)
        assert success is True
        assert await file_manager.file_exists(filename) is False

    @pytest.mark.asyncio
    async def test_delete_file_nonexistent(self, file_manager):
        """Test deleting non-existent file."""
        filename = "nonexistent.bot"

        success = await file_manager.delete_file(filename)
        assert success is False

    @pytest.mark.asyncio
    async def test_list_files_empty_directory(self, file_manager):
        """Test listing files in empty directory."""
        files, total_count, total_size = await file_manager.list_files(
            limit=100, offset=0, sort_by="filename", sort_order="asc"
        )

        assert isinstance(files, list)
        assert len(files) == 0
        assert total_count == 0
        assert total_size == 0

    @pytest.mark.asyncio
    async def test_list_files_with_files(self, file_manager):
        """Test listing files with actual files."""
        # Create test files
        files_to_create = [
            ("bot1.bot", b"content1"),
            ("bot2.bot", b"content2"),
            ("bot3.bot", b"content3")
        ]

        for filename, content in files_to_create:
            await file_manager.save_bot_file(filename, content)

        # List files
        files, total_count, total_size = await file_manager.list_files(
            limit=100, offset=0, sort_by="filename", sort_order="asc"
        )

        assert isinstance(files, list)
        assert len(files) == 3
        assert total_count == 3
        assert total_size > 0

        # Check sorting
        filenames = [f.metadata.filename for f in files]
        assert filenames == sorted(filenames)

    @pytest.mark.asyncio
    async def test_list_files_pagination(self, file_manager):
        """Test file listing with pagination."""
        # Create test files
        for i in range(5):
            await file_manager.save_bot_file(f"bot{i}.bot", f"content{i}".encode())

        # Get first page
        files_page1, total_count, total_size = await file_manager.list_files(
            limit=2, offset=0, sort_by="filename", sort_order="asc"
        )

        assert len(files_page1) == 2
        assert total_count == 5

        # Get second page
        files_page2, _, _ = await file_manager.list_files(
            limit=2, offset=2, sort_by="filename", sort_order="asc"
        )

        assert len(files_page2) == 2

        # Ensure no overlap
        page1_names = {f.metadata.filename for f in files_page1}
        page2_names = {f.metadata.filename for f in files_page2}
        assert page1_names.isdisjoint(page2_names)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])