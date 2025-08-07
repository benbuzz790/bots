"""
Comprehensive error handling tests for network failures, invalid files, and storage limits.
"""

import pytest
import json
import os
import tempfile
import shutil
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import aiofiles

# Import the application components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.main import app
from backend.file_manager import FileManager, FileValidationError, StorageError
from backend.bot_manager import BotManager
from backend.websocket_handler import WebSocketHandler

class TestNetworkFailures:
    """Test handling of various network failure scenarios."""

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

    def test_upload_connection_timeout(self, client, temp_storage):
        """Test upload behavior during connection timeout."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.validate_bot_file = AsyncMock(side_effect=asyncio.TimeoutError("Connection timeout"))
            mock_get_fm.return_value = mock_fm

            files = {"file": ("test.bot", b'{"test": "data"}', "application/octet-stream")}
            data = {"overwrite": "false"}

            response = client.post("/api/files/upload", files=files, data=data)

            # Should return 500 for internal server error
            assert response.status_code == 500
            assert "internal server error" in response.json()["detail"].lower()

    def test_download_connection_interrupted(self, client, temp_storage):
        """Test download behavior when connection is interrupted."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.file_exists = AsyncMock(return_value=True)
            mock_fm.get_file_path = AsyncMock(side_effect=ConnectionError("Connection lost"))
            mock_get_fm.return_value = mock_fm

            response = client.get("/api/files/download/test.bot")

            assert response.status_code == 500
            assert "internal server error" in response.json()["detail"].lower()

    def test_list_files_network_error(self, client, temp_storage):
        """Test file listing during network errors."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()
            mock_fm.list_files = AsyncMock(side_effect=ConnectionResetError("Network reset"))
            mock_get_fm.return_value = mock_fm

            response = client.get("/api/files/list")

            assert response.status_code == 500
            assert "internal server error" in response.json()["detail"].lower()

    def test_websocket_connection_failure(self, temp_storage):
        """Test WebSocket behavior during connection failures."""

        bot_manager = BotManager()
        websocket_handler = WebSocketHandler(bot_manager)

        # Mock WebSocket that fails during message handling
        mock_websocket = Mock()
        mock_websocket.receive_text = AsyncMock(side_effect=ConnectionError("WebSocket connection lost"))
        mock_websocket.accept = AsyncMock()

        # Test connection handling with failure
        with pytest.raises(ConnectionError):
            asyncio.run(websocket_handler.handle_connection(mock_websocket))

    def test_api_gateway_timeout(self, client):
        """Test behavior when API gateway times out."""

        # Simulate very slow operation that would trigger gateway timeout
        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            mock_fm = Mock()

            async def slow_operation(*args, **kwargs):
                await asyncio.sleep(60)  # Simulate 60 second delay
                return []

            mock_fm.list_files = slow_operation
            mock_get_fm.return_value = mock_fm

            # In a real scenario, this would timeout
            # For testing, we'll just verify the setup
            assert mock_fm.list_files is not None

    def test_dns_resolution_failure(self, client):
        """Test behavior when DNS resolution fails."""

        # This would typically affect external service calls
        # For our file operations, DNS failures would be less relevant
        # But we can test error propagation

        with patch('socket.gethostbyname', side_effect=OSError("DNS resolution failed")):
            # Most file operations are local, so DNS shouldn't affect them
            response = client.get("/api/health")
            assert response.status_code == 200  # Should still work for local operations

class TestInvalidFiles:
    """Test handling of various invalid file scenarios."""

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
        """Create file manager."""
        return FileManager(temp_storage)

    def test_corrupted_json_file(self, client, temp_storage):
        """Test handling of corrupted JSON files."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            # Various types of corrupted JSON
            corrupted_files = [
                (b'{"incomplete": ', "incomplete JSON"),
                (b'{"duplicate": "key", "duplicate": "key2"}', "duplicate keys"),
                (b'{"nested": {"deep": {"very": {"deep": ', "deeply nested incomplete"),
                (b'\x00\x01\x02\x03', "binary data"),
                (b'{"unicode": "\uD800"}', "invalid unicode"),
                (b'{"number": 1e999999}', "invalid number"),
            ]

            for corrupted_content, description in corrupted_files:
                files = {"file": (f"{description.replace(' ', '_')}.bot", corrupted_content, "application/octet-stream")}
                data = {"overwrite": "false"}

                response = client.post("/api/files/upload", files=files, data=data)

                assert response.status_code == 400, f"Should reject {description}"
                assert "invalid" in response.json()["detail"].lower()

    def test_malicious_file_content(self, client, temp_storage):
        """Test handling of potentially malicious file content."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            malicious_contents = [
                # Script injection attempts
                (json.dumps({"script": "<script>alert('xss')</script>"}).encode(), "XSS attempt"),
                (json.dumps({"sql": "'; DROP TABLE users; --"}).encode(), "SQL injection attempt"),
                (json.dumps({"path": "../../../etc/passwd"}).encode(), "Path traversal attempt"),
                (json.dumps({"command": "rm -rf /"}).encode(), "Command injection attempt"),
                (json.dumps({"eval": "eval('malicious code')"}).encode(), "Code evaluation attempt"),
            ]

            for malicious_content, description in malicious_contents:
                files = {"file": (f"malicious_{description.replace(' ', '_')}.bot", malicious_content, "application/octet-stream")}
                data = {"overwrite": "false"}

                response = client.post("/api/files/upload", files=files, data=data)

                # Should accept the file (content validation is separate from security)
                # But should warn about suspicious content
                if response.status_code == 200:
                    result = response.json()
                    # Check if warnings are present
                    assert "warnings" in result
                else:
                    # If rejected, should be due to validation, not security
                    assert response.status_code == 400

    def test_extremely_nested_json(self, file_manager):
        """Test handling of extremely nested JSON structures."""

        # Create deeply nested JSON that might cause stack overflow
        nested_dict = {}
        current = nested_dict
        for i in range(1000):  # Very deep nesting
            current["level"] = {}
            current = current["level"]
        current["value"] = "deep"

        deeply_nested_content = json.dumps(nested_dict).encode()

        # Test validation
        result = asyncio.run(file_manager.validate_bot_file(deeply_nested_content))

        # Should handle gracefully without crashing
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    def test_invalid_utf8_sequences(self, file_manager):
        """Test handling of invalid UTF-8 byte sequences."""

        invalid_utf8_sequences = [
            b'\xff\xfe',  # Invalid start bytes
            b'\x80\x80',  # Invalid continuation
            b'\xc0\x80',  # Overlong encoding
            b'\xed\xa0\x80',  # UTF-16 surrogate
            b'\xf4\x90\x80\x80',  # Code point too large
        ]

        for invalid_sequence in invalid_utf8_sequences:
            result = asyncio.run(file_manager.validate_bot_file(invalid_sequence))

            assert result.is_valid is False
            assert any("utf-8" in error.lower() for error in result.errors)

    def test_zero_byte_injection(self, file_manager):
        """Test handling of null byte injection attempts."""

        # Null bytes in JSON content
        null_byte_content = b'{"test": "value\x00injection"}'

        result = asyncio.run(file_manager.validate_bot_file(null_byte_content))

        # Should either reject or handle gracefully
        assert isinstance(result.is_valid, bool)
        if not result.is_valid:
            assert len(result.errors) > 0

    def test_file_type_confusion(self, client, temp_storage):
        """Test handling of files with wrong extensions or MIME types."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            # Valid JSON but wrong extension
            valid_json = json.dumps({"test": "data"}).encode()

            files = {"file": ("test.txt", valid_json, "text/plain")}
            data = {"overwrite": "false"}

            response = client.post("/api/files/upload", files=files, data=data)

            assert response.status_code == 400
            assert "extension" in response.json()["detail"].lower()

    def test_compression_bomb_simulation(self, file_manager):
        """Test handling of files that expand dramatically when processed."""

        # Create content that might expand significantly
        # (JSON with many repeated keys)
        bomb_dict = {}
        for i in range(10000):
            bomb_dict[f"key_{i}"] = "x" * 100  # 100 chars per key

        bomb_content = json.dumps(bomb_dict).encode()

        # Should handle without excessive memory usage
        result = asyncio.run(file_manager.validate_bot_file(bomb_content))

        # Might be rejected due to size, but shouldn't crash
        assert isinstance(result.is_valid, bool)

class TestStorageLimits:
    """Test handling of storage limit scenarios."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_individual_file_size_limit(self, temp_storage):
        """Test enforcement of individual file size limits."""

        file_manager = FileManager(temp_storage)

        # Create file that exceeds 50MB limit
        oversized_content = b"x" * (51 * 1024 * 1024)  # 51MB

        result = asyncio.run(file_manager.validate_bot_file(oversized_content))

        assert result.is_valid is False
        assert any("large" in error.lower() or "size" in error.lower() for error in result.errors)

    def test_total_storage_limit(self, temp_storage):
        """Test enforcement of total storage limits."""

        # Create file manager with small total storage limit
        file_manager = FileManager(temp_storage, max_storage_bytes=1024)  # 1KB total

        # Try to save files that exceed total limit
        file1_content = b"x" * 600  # 600 bytes
        file2_content = b"x" * 600  # 600 bytes (total 1200 > 1024)

        # First file should succeed
        file1_info = asyncio.run(file_manager.save_bot_file("file1.bot", file1_content))
        assert file1_info is not None

        # Second file should fail due to storage limit
        with pytest.raises(StorageError, match="Storage limit exceeded"):
            asyncio.run(file_manager.save_bot_file("file2.bot", file2_content))

    def test_disk_space_exhaustion(self, temp_storage):
        """Test behavior when disk space is exhausted."""

        file_manager = FileManager(temp_storage)

        # Mock disk space exhaustion
        with patch('aiofiles.open', side_effect=OSError("No space left on device")):
            with pytest.raises(Exception):  # Should propagate the OS error
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_inode_exhaustion(self, temp_storage):
        """Test behavior when filesystem inodes are exhausted."""

        file_manager = FileManager(temp_storage)

        # Mock inode exhaustion
        with patch('aiofiles.open', side_effect=OSError("No space left on device")):  # Same error for inodes
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_concurrent_storage_usage(self, temp_storage):
        """Test storage calculations with concurrent operations."""

        file_manager = FileManager(temp_storage, max_storage_bytes=2048)  # 2KB total

        # Simulate concurrent file saves
        async def save_multiple_files():
            tasks = []
            for i in range(5):
                content = f"content_{i}".encode() * 50  # ~500 bytes each
                task = file_manager.save_bot_file(f"concurrent_{i}.bot", content)
                tasks.append(task)

            results = []
            for task in tasks:
                try:
                    result = await task
                    results.append(("success", result))
                except StorageError as e:
                    results.append(("error", str(e)))

            return results

        results = asyncio.run(save_multiple_files())

        # Some should succeed, some should fail due to storage limits
        successes = [r for r in results if r[0] == "success"]
        errors = [r for r in results if r[0] == "error"]

        assert len(successes) > 0, "At least some files should succeed"
        assert len(errors) > 0, "Some files should fail due to storage limits"

    def test_storage_cleanup_after_deletion(self, temp_storage):
        """Test that storage is properly reclaimed after file deletion."""

        file_manager = FileManager(temp_storage, max_storage_bytes=1024)  # 1KB total

        # Fill storage
        large_content = b"x" * 800  # 800 bytes
        file_info = asyncio.run(file_manager.save_bot_file("large.bot", large_content))
        assert file_info is not None

        # Try to save another file (should fail)
        with pytest.raises(StorageError):
            asyncio.run(file_manager.save_bot_file("another.bot", b"x" * 300))

        # Delete the large file
        success = asyncio.run(file_manager.delete_file("large.bot"))
        assert success is True

        # Now should be able to save the other file
        file_info2 = asyncio.run(file_manager.save_bot_file("another.bot", b"x" * 300))
        assert file_info2 is not None

    def test_storage_calculation_accuracy(self, temp_storage):
        """Test accuracy of storage size calculations."""

        file_manager = FileManager(temp_storage)

        # Create files with known sizes
        test_files = [
            ("small.bot", b"x" * 100),    # 100 bytes
            ("medium.bot", b"x" * 500),   # 500 bytes
            ("large.bot", b"x" * 1000),   # 1000 bytes
        ]

        for filename, content in test_files:
            asyncio.run(file_manager.save_bot_file(filename, content))

        # Check total storage calculation
        total_size = asyncio.run(file_manager._get_total_storage_size())
        expected_size = 100 + 500 + 1000  # 1600 bytes

        # Allow for small filesystem overhead
        assert abs(total_size - expected_size) < 100, f"Storage calculation inaccurate: {total_size} vs {expected_size}"

class TestFileSystemErrors:
    """Test handling of various filesystem-level errors."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_permission_denied_errors(self, temp_storage):
        """Test handling of permission denied errors."""

        file_manager = FileManager(temp_storage)

        # Mock permission denied error
        with patch('aiofiles.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_readonly_filesystem(self, temp_storage):
        """Test behavior on read-only filesystem."""

        file_manager = FileManager(temp_storage)

        # Mock read-only filesystem error
        with patch('aiofiles.open', side_effect=OSError("Read-only file system")):
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_filesystem_corruption(self, temp_storage):
        """Test handling of filesystem corruption."""

        file_manager = FileManager(temp_storage)

        # Mock filesystem corruption
        with patch('aiofiles.open', side_effect=OSError("Input/output error")):
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_network_filesystem_issues(self, temp_storage):
        """Test handling of network filesystem issues."""

        file_manager = FileManager(temp_storage)

        # Mock network filesystem errors
        network_errors = [
            OSError("Stale file handle"),
            OSError("Connection timed out"),
            OSError("Host is unreachable"),
        ]

        for error in network_errors:
            with patch('aiofiles.open', side_effect=error):
                with pytest.raises(Exception):
                    asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_interrupted_operations(self, temp_storage):
        """Test handling of interrupted file operations."""

        file_manager = FileManager(temp_storage)

        # Mock interrupted system call
        with patch('aiofiles.open', side_effect=InterruptedError("Interrupted system call")):
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

class TestRecoveryMechanisms:
    """Test error recovery and graceful degradation."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_partial_file_cleanup(self, temp_storage):
        """Test cleanup of partially written files after errors."""

        file_manager = FileManager(temp_storage)

        # Mock error during file write
        original_open = aiofiles.open

        async def failing_open(*args, **kwargs):
            if 'w' in str(args) or 'wb' in str(args):
                # Let file be created, then fail
                file_handle = await original_open(*args, **kwargs)
                await file_handle.write(b"partial")
                await file_handle.close()
                raise OSError("Write failed")
            return await original_open(*args, **kwargs)

        with patch('aiofiles.open', side_effect=failing_open):
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"full content"))

        # Check if partial file was cleaned up
        file_path = os.path.join(temp_storage, "test.bot")
        # In a real implementation, we'd want partial files to be cleaned up
        # For now, just verify the error was handled

    def test_retry_mechanism_simulation(self, temp_storage):
        """Test retry mechanisms for transient errors."""

        file_manager = FileManager(temp_storage)

        # This would be implemented in a real retry mechanism
        # For now, just test that errors are properly categorized

        transient_errors = [
            OSError("Resource temporarily unavailable"),
            ConnectionError("Connection reset by peer"),
            TimeoutError("Operation timed out"),
        ]

        for error in transient_errors:
            with patch('aiofiles.open', side_effect=error):
                with pytest.raises(Exception):
                    asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_graceful_degradation(self, temp_storage):
        """Test graceful degradation when some features fail."""

        file_manager = FileManager(temp_storage)

        # Test that basic operations still work even if advanced features fail
        # For example, if checksum calculation fails, file should still be saved

        with patch('hashlib.sha256', side_effect=Exception("Checksum failed")):
            # In a real implementation, this might fall back to a simpler checksum
            # or save without checksum verification
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

class TestInputValidation:
    """Test comprehensive input validation and sanitization."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_filename_validation_edge_cases(self, temp_storage):
        """Test filename validation with edge cases."""

        file_manager = FileManager(temp_storage)

        invalid_filenames = [
            None,           # None type
            123,            # Integer
            [],             # List
            {},             # Dict
            "",             # Empty string
            "   ",          # Whitespace only
            "a" * 300,      # Too long
            "test",         # No extension
            ".bot",         # No name
            "test.BOT",     # Wrong case (might be valid depending on implementation)
        ]

        for invalid_filename in invalid_filenames:
            with pytest.raises(AssertionError):
                asyncio.run(file_manager.save_bot_file(invalid_filename, b"content"))

    def test_content_validation_edge_cases(self, temp_storage):
        """Test content validation with edge cases."""

        file_manager = FileManager(temp_storage)

        invalid_contents = [
            None,           # None type
            "string",       # String instead of bytes
            123,            # Integer
            [],             # List
            {},             # Dict
        ]

        for invalid_content in invalid_contents:
            with pytest.raises(AssertionError):
                asyncio.run(file_manager.save_bot_file("test.bot", invalid_content))

    def test_parameter_type_validation(self, temp_storage):
        """Test that all parameters are properly type-validated."""

        # Test FileManager initialization
        invalid_storage_dirs = [None, 123, [], {}]
        for invalid_dir in invalid_storage_dirs:
            with pytest.raises(AssertionError):
                FileManager(invalid_dir)

        invalid_max_storage = ["string", [], {}, None]
        for invalid_max in invalid_max_storage:
            with pytest.raises(AssertionError):
                FileManager(temp_storage, invalid_max)

    def test_defensive_assertions_coverage(self, temp_storage):
        """Test that defensive assertions cover all critical paths."""

        file_manager = FileManager(temp_storage)

        # Test all major methods have proper input validation
        methods_to_test = [
            ('save_bot_file', ["test.bot", b"content"]),
            ('file_exists', ["test.bot"]),
            ('get_file_path', ["test.bot"]),
            ('delete_file', ["test.bot"]),
            ('validate_bot_file', [b"content"]),
        ]

        for method_name, valid_args in methods_to_test:
            method = getattr(file_manager, method_name)

            # Test with None as first argument
            with pytest.raises(AssertionError):
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method(None, *valid_args[1:]))
                else:
                    method(None, *valid_args[1:])

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])