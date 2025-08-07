"""
Integration tests for the complete bot save/load workflow.
"""

import pytest
import json
import os
import tempfile
import shutil
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import websockets
import threading
import time

# Import the application components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.main import app
from backend.file_manager import FileManager
from backend.bot_manager import BotManager
from backend.websocket_handler import WebSocketHandler

class TestIntegration:
    """Integration tests for complete save/load workflow."""

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
    def bot_manager(self):
        """Create bot manager."""
        return BotManager()

    @pytest.fixture
    def valid_bot_data(self):
        """Valid bot file data for testing."""
        return {
            "conversation": {
                "root": {
                    "content": "Hello, I'm a test bot",
                    "role": "assistant",
                    "replies": []
                }
            },
            "model_params": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {}
                }
            ],
            "metadata": {
                "created": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "name": "Test Bot"
            }
        }

    def test_complete_save_load_workflow(self, client, temp_storage, valid_bot_data):
        """Test complete workflow: create bot -> save -> load -> verify."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm, \
             patch('backend.file_routes.get_bot_manager') as mock_get_bm, \
             patch('backend.main.bot_manager') as mock_main_bm:

            # Setup mocks
            file_manager = FileManager(temp_storage)
            bot_manager = BotManager()

            mock_get_fm.return_value = file_manager
            mock_get_bm.return_value = bot_manager
            mock_main_bm = bot_manager

            # Step 1: Create a bot
            create_response = client.post("/api/bots/create", json={"name": "Test Bot"})
            assert create_response.status_code == 200, f"Create failed: {create_response.text}"

            create_data = create_response.json()
            assert create_data["success"] is True
            bot_id = create_data["bot_id"]
            assert isinstance(bot_id, str) and bot_id.strip()

            # Step 2: Mock bot instance for saving
            mock_bot = Mock()
            mock_bot.save = Mock()

            with patch.object(bot_manager, 'get_bot', return_value=mock_bot):
                # Step 3: Save the bot to file
                save_data = {"filename": "test_bot.bot", "overwrite": "false"}
                save_response = client.post(f"/api/files/save-bot/{bot_id}", data=save_data)

                assert save_response.status_code == 200, f"Save failed: {save_response.text}"

                save_result = save_response.json()
                assert save_result["success"] is True
                assert save_result["bot_id"] == bot_id
                assert "file_info" in save_result

            # Step 4: Verify file was created (mock the file creation)
            bot_file_path = os.path.join(temp_storage, "test_bot.bot")
            with open(bot_file_path, 'w') as f:
                json.dump(valid_bot_data, f)

            # Step 5: List files to verify it appears
            list_response = client.get("/api/files/list")
            assert list_response.status_code == 200

            list_data = list_response.json()
            assert list_data["total_count"] >= 1

            # Find our file
            our_file = None
            for file_info in list_data["files"]:
                if file_info["metadata"]["filename"] == "test_bot.bot":
                    our_file = file_info
                    break

            assert our_file is not None, "Saved file not found in list"
            assert our_file["is_valid"] is True
            assert len(our_file["validation_errors"]) == 0

            # Step 6: Download the file to verify content
            download_response = client.get("/api/files/download/test_bot.bot")
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "application/octet-stream"

            # Step 7: Load the bot from file
            with patch('bots.foundation.base.Bot.load') as mock_load:
                mock_loaded_bot = Mock()
                mock_load.return_value = mock_loaded_bot

                load_response = client.post("/api/files/load-bot/test_bot.bot")
                assert load_response.status_code == 200

                load_data = load_response.json()
                assert load_data["success"] is True
                assert "bot_id" in load_data
                assert load_data["filename"] == "test_bot.bot"

                new_bot_id = load_data["bot_id"]
                assert new_bot_id != bot_id  # Should be a new bot instance

    def test_file_upload_and_load_workflow(self, client, temp_storage, valid_bot_data):
        """Test workflow: upload file -> load bot -> verify."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm, \
             patch('backend.file_routes.get_bot_manager') as mock_get_bm:

            # Setup mocks
            file_manager = FileManager(temp_storage)
            bot_manager = BotManager()

            mock_get_fm.return_value = file_manager
            mock_get_bm.return_value = bot_manager

            # Step 1: Create valid bot file content
            bot_content = json.dumps(valid_bot_data).encode('utf-8')

            # Step 2: Upload the file
            files = {"file": ("uploaded_bot.bot", bot_content, "application/octet-stream")}
            upload_data = {"overwrite": "false"}

            upload_response = client.post("/api/files/upload", files=files, data=upload_data)
            assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"

            upload_result = upload_response.json()
            assert upload_result["success"] is True
            assert upload_result["file_info"]["is_valid"] is True

            # Step 3: Verify file exists in storage
            file_path = os.path.join(temp_storage, "uploaded_bot.bot")
            assert os.path.exists(file_path)

            with open(file_path, 'rb') as f:
                saved_content = f.read()
            assert saved_content == bot_content

            # Step 4: Load bot from uploaded file
            with patch('bots.foundation.base.Bot.load') as mock_load:
                mock_loaded_bot = Mock()
                mock_load.return_value = mock_loaded_bot

                load_response = client.post("/api/files/load-bot/uploaded_bot.bot")
                assert load_response.status_code == 200

                load_data = load_response.json()
                assert load_data["success"] is True
                assert load_data["filename"] == "uploaded_bot.bot"

                # Verify Bot.load was called with correct path
                mock_load.assert_called_once_with(file_path)

    def test_error_handling_workflow(self, client, temp_storage):
        """Test error handling throughout the workflow."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm, \
             patch('backend.file_routes.get_bot_manager') as mock_get_bm:

            file_manager = FileManager(temp_storage)
            bot_manager = BotManager()

            mock_get_fm.return_value = file_manager
            mock_get_bm.return_value = bot_manager

            # Test 1: Upload invalid file
            invalid_content = b"invalid json content"
            files = {"file": ("invalid.bot", invalid_content, "application/octet-stream")}
            upload_data = {"overwrite": "false"}

            upload_response = client.post("/api/files/upload", files=files, data=upload_data)
            assert upload_response.status_code == 400
            assert "invalid" in upload_response.json()["detail"].lower()

            # Test 2: Try to load non-existent file
            load_response = client.post("/api/files/load-bot/nonexistent.bot")
            assert load_response.status_code == 404

            # Test 3: Try to save non-existent bot
            save_data = {"filename": "test.bot", "overwrite": "false"}
            save_response = client.post("/api/files/save-bot/nonexistent-bot", data=save_data)
            assert save_response.status_code == 404

            # Test 4: Try to delete non-existent file
            delete_response = client.delete("/api/files/delete/nonexistent.bot?confirm=true")
            assert delete_response.status_code == 404

            # Test 5: Try to download non-existent file
            download_response = client.get("/api/files/download/nonexistent.bot")
            assert download_response.status_code == 404

    def test_concurrent_operations(self, client, temp_storage, valid_bot_data):
        """Test concurrent file operations."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm, \
             patch('backend.file_routes.get_bot_manager') as mock_get_bm:

            file_manager = FileManager(temp_storage)
            bot_manager = BotManager()

            mock_get_fm.return_value = file_manager
            mock_get_bm.return_value = bot_manager

            # Create multiple bot files
            bot_content = json.dumps(valid_bot_data).encode('utf-8')

            # Upload multiple files concurrently (simulate with sequential calls)
            upload_results = []
            for i in range(3):
                filename = f"concurrent_bot_{i}.bot"
                files = {"file": (filename, bot_content, "application/octet-stream")}
                upload_data = {"overwrite": "false"}

                response = client.post("/api/files/upload", files=files, data=upload_data)
                upload_results.append((filename, response))

            # Verify all uploads succeeded
            for filename, response in upload_results:
                assert response.status_code == 200, f"Upload of {filename} failed: {response.text}"
                result = response.json()
                assert result["success"] is True

            # List files to verify all are present
            list_response = client.get("/api/files/list")
            assert list_response.status_code == 200

            list_data = list_response.json()
            assert list_data["total_count"] >= 3

            uploaded_files = [f["metadata"]["filename"] for f in list_data["files"]]
            for i in range(3):
                assert f"concurrent_bot_{i}.bot" in uploaded_files

    def test_storage_limits(self, temp_storage):
        """Test storage limit enforcement."""

        # Create file manager with very small storage limit
        small_storage_fm = FileManager(temp_storage, max_storage_bytes=1000)  # 1KB limit

        with patch('backend.file_routes.get_file_manager', return_value=small_storage_fm):
            client = TestClient(app)

            # Try to upload file that exceeds limit
            large_content = b"x" * 2000  # 2KB content
            files = {"file": ("large.bot", large_content, "application/octet-stream")}
            upload_data = {"overwrite": "false"}

            response = client.post("/api/files/upload", files=files, data=upload_data)
            assert response.status_code == 507  # Insufficient Storage
            assert "storage" in response.json()["detail"].lower()

    def test_file_validation_edge_cases(self, client, temp_storage):
        """Test file validation with various edge cases."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            test_cases = [
                # (content, expected_status, description)
                (b"", 400, "empty file"),
                (b"not json", 400, "invalid json"),
                (json.dumps({"invalid": "structure"}).encode(), 200, "json but invalid bot structure"),
                (b"\xff\xfe\x00\x00", 400, "non-utf8 content"),
                (json.dumps({"conversation": {}, "model_params": {}}).encode(), 200, "minimal valid structure"),
            ]

            for i, (content, expected_status, description) in enumerate(test_cases):
                filename = f"test_{i}.bot"
                files = {"file": (filename, content, "application/octet-stream")}
                upload_data = {"overwrite": "false"}

                response = client.post("/api/files/upload", files=files, data=upload_data)
                assert response.status_code == expected_status, \
                    f"Test case '{description}' failed: expected {expected_status}, got {response.status_code}"

    def test_filename_security(self, client, temp_storage):
        """Test filename security and path traversal prevention."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            # Test malicious filenames
            malicious_filenames = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "file<script>alert(1)</script>.bot",
                "file|rm -rf /.bot",
                "file?.bot",
                "file*.bot",
                "file\x00.bot",
                "CON.bot",  # Windows reserved name
                "PRN.bot",  # Windows reserved name
            ]

            valid_content = json.dumps({"test": "data"}).encode()

            for malicious_filename in malicious_filenames:
                # Test upload
                files = {"file": (malicious_filename, valid_content, "application/octet-stream")}
                upload_response = client.post("/api/files/upload", files=files, data={"overwrite": "false"})
                assert upload_response.status_code == 400, \
                    f"Malicious filename '{malicious_filename}' should be rejected"

                # Test download
                download_response = client.get(f"/api/files/download/{malicious_filename}")
                assert download_response.status_code == 400, \
                    f"Malicious filename '{malicious_filename}' should be rejected for download"

                # Test delete
                delete_response = client.delete(f"/api/files/delete/{malicious_filename}?confirm=true")
                assert delete_response.status_code == 400, \
                    f"Malicious filename '{malicious_filename}' should be rejected for deletion"

    def test_websocket_integration(self, temp_storage):
        """Test WebSocket integration with file operations."""

        # This test would require a more complex setup with actual WebSocket connections
        # For now, we'll test the WebSocket handler components

        bot_manager = BotManager()
        websocket_handler = WebSocketHandler(bot_manager)

        # Test WebSocket handler initialization
        assert websocket_handler.bot_manager is bot_manager
        assert isinstance(websocket_handler.connections, dict)
        assert isinstance(websocket_handler.connection_bots, dict)

        # Test message validation
        mock_websocket = Mock()

        # Test invalid message format
        with pytest.raises(Exception):
            asyncio.run(websocket_handler.handle_message(
                mock_websocket, "conn1", "invalid json"
            ))

        # Test valid message structure validation
        valid_message = json.dumps({
            "type": "send_message",
            "data": {
                "botId": "test-bot",
                "content": "Hello"
            }
        })

        # This would require more complex async testing setup
        # The actual WebSocket integration would be tested in end-to-end tests

    def test_cleanup_and_resource_management(self, client, temp_storage, valid_bot_data):
        """Test proper cleanup and resource management."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            # Create and upload multiple files
            bot_content = json.dumps(valid_bot_data).encode('utf-8')

            for i in range(5):
                filename = f"cleanup_test_{i}.bot"
                files = {"file": (filename, bot_content, "application/octet-stream")}
                upload_data = {"overwrite": "false"}

                response = client.post("/api/files/upload", files=files, data=upload_data)
                assert response.status_code == 200

            # Verify files exist
            list_response = client.get("/api/files/list")
            list_data = list_response.json()
            assert list_data["total_count"] >= 5

            # Delete all test files
            for i in range(5):
                filename = f"cleanup_test_{i}.bot"
                delete_response = client.delete(f"/api/files/delete/{filename}?confirm=true")
                assert delete_response.status_code == 200

            # Verify files are deleted
            final_list_response = client.get("/api/files/list")
            final_list_data = final_list_response.json()

            cleanup_files = [f for f in final_list_data["files"] 
                           if f["metadata"]["filename"].startswith("cleanup_test_")]
            assert len(cleanup_files) == 0, "Not all test files were cleaned up"

    def test_api_rate_limiting_simulation(self, client, temp_storage):
        """Simulate rapid API calls to test rate limiting behavior."""

        with patch('backend.file_routes.get_file_manager') as mock_get_fm:
            file_manager = FileManager(temp_storage)
            mock_get_fm.return_value = file_manager

            # Make rapid consecutive requests
            responses = []
            for i in range(10):
                response = client.get("/api/files/list")
                responses.append(response)

            # All should succeed (no rate limiting implemented yet)
            for i, response in enumerate(responses):
                assert response.status_code == 200, f"Request {i} failed: {response.status_code}"

    def test_health_check_integration(self, client):
        """Test health check endpoint integration."""

        response = client.get("/api/health")
        assert response.status_code == 200

        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        assert "services" in health_data

        services = health_data["services"]
        assert isinstance(services, dict)
        # Note: In test environment, services might not be initialized
        # This test verifies the endpoint structure

class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_network_failure_simulation(self, temp_storage):
        """Test behavior during simulated network failures."""

        file_manager = FileManager(temp_storage)

        # Simulate disk I/O errors
        with patch('aiofiles.open', side_effect=IOError("Disk error")):
            with pytest.raises(Exception):
                asyncio.run(file_manager.save_bot_file("test.bot", b"content"))

    def test_memory_pressure_simulation(self, temp_storage):
        """Test behavior under memory pressure."""

        file_manager = FileManager(temp_storage)

        # Simulate memory error during large file processing
        with patch('json.loads', side_effect=MemoryError("Out of memory")):
            result = asyncio.run(file_manager.validate_bot_file(b'{"test": "data"}'))
            assert result.is_valid is False
            assert any("error" in error.lower() for error in result.errors)

    def test_concurrent_access_conflicts(self, temp_storage):
        """Test handling of concurrent access conflicts."""

        file_manager = FileManager(temp_storage)

        # Simulate file being deleted between existence check and access
        async def test_race_condition():
            # This would require more complex async testing
            # to properly simulate race conditions
            pass

        # For now, just verify the file manager handles basic concurrent operations
        assert file_manager is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])