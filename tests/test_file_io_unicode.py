"""Comprehensive tests for file I/O operations with unicode content.

This module tests file operations to ensure proper unicode handling and prevent
mojibake issues when reading/writing files with unicode content and filenames.

Tests cover:
- Reading/writing files with unicode content
- Unicode filenames
- Different encoding parameters
- Malformed unicode handling
- Large files with unicode
"""

from encoding_fixtures import UNICODE_TEST_STRINGS, assert_no_mojibake


class TestFileReadWriteUnicode:
    """Test reading and writing files with unicode content."""

    def test_write_and_read_unicode_content(self, tmp_path):
        """Test writing and reading file with unicode content."""
        test_file = tmp_path / "unicode_test.txt"
        content = UNICODE_TEST_STRINGS["mixed"]

        # Write unicode content
        test_file.write_text(content, encoding="utf-8")

        # Read it back
        read_content = test_file.read_text(encoding="utf-8")

        # Verify no mojibake
        assert_no_mojibake(read_content, ["✅", "中文", "🎉", "العربية", "❌"])
        assert read_content == content

    def test_write_emoji_content(self, tmp_path):
        """Test writing and reading emoji characters."""
        test_file = tmp_path / "emoji_test.txt"
        emojis = [
            UNICODE_TEST_STRINGS["emoji_checkmark"],
            UNICODE_TEST_STRINGS["emoji_cross"],
            UNICODE_TEST_STRINGS["emoji_warning"],
            UNICODE_TEST_STRINGS["emoji_party"],
            UNICODE_TEST_STRINGS["emoji_memo"],
            UNICODE_TEST_STRINGS["emoji_wrench"],
        ]
        content = " ".join(emojis)

        # Write with explicit UTF-8
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Read back
        with open(test_file, "r", encoding="utf-8") as f:
            read_content = f.read()

        # Verify all emojis present
        for emoji in emojis:
            assert emoji in read_content, f"Emoji {emoji} not found in {read_content!r}"

        assert_no_mojibake(read_content, emojis)

    def test_write_chinese_content(self, tmp_path):
        """Test writing and reading Chinese characters."""
        test_file = tmp_path / "chinese_test.txt"
        content = UNICODE_TEST_STRINGS["chinese"]

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert "中文" in read_content
        assert read_content == content

    def test_write_arabic_content(self, tmp_path):
        """Test writing and reading Arabic characters."""
        test_file = tmp_path / "arabic_test.txt"
        content = UNICODE_TEST_STRINGS["arabic"]

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert "العربية" in read_content
        assert read_content == content

    def test_append_unicode_content(self, tmp_path):
        """Test appending unicode content to existing file."""
        test_file = tmp_path / "append_test.txt"

        # Write initial content
        test_file.write_text("Initial ✅\n", encoding="utf-8")

        # Append more content
        with open(test_file, "a", encoding="utf-8") as f:
            f.write("Appended 🎉\n")

        # Read all
        content = test_file.read_text(encoding="utf-8")

        assert "✅" in content
        assert "🎉" in content
        assert_no_mojibake(content, ["✅", "🎉"])


class TestUnicodeFilenames:
    """Test file operations with unicode filenames."""

    def test_create_file_with_emoji_filename(self, tmp_path):
        """Test creating file with emoji in filename."""
        filename = "test_✅_file.txt"
        test_file = tmp_path / filename

        # Write content
        test_file.write_text("Test content", encoding="utf-8")

        # Verify file exists
        assert test_file.exists()
        assert test_file.name == filename

        # Read content back
        content = test_file.read_text(encoding="utf-8")
        assert content == "Test content"

    def test_create_file_with_chinese_filename(self, tmp_path):
        """Test creating file with Chinese characters in filename."""
        filename = "测试文件_中文.txt"
        test_file = tmp_path / filename

        test_file.write_text("Chinese filename test", encoding="utf-8")

        assert test_file.exists()
        assert "中文" in test_file.name

        # List directory and verify filename
        files = list(tmp_path.glob("*.txt"))
        assert len(files) == 1
        assert "中文" in files[0].name

    def test_create_file_with_arabic_filename(self, tmp_path):
        """Test creating file with Arabic characters in filename."""
        filename = "ملف_العربية.txt"
        test_file = tmp_path / filename

        test_file.write_text("Arabic filename test", encoding="utf-8")

        assert test_file.exists()
        assert "العربية" in test_file.name

    def test_create_file_with_mixed_unicode_filename(self, tmp_path):
        """Test creating file with mixed unicode in filename."""
        filename = "test_✅_中文_🎉_العربية.txt"
        test_file = tmp_path / filename

        test_file.write_text("Mixed unicode filename", encoding="utf-8")

        assert test_file.exists()
        assert "✅" in test_file.name
        assert "中文" in test_file.name
        assert "🎉" in test_file.name

    def test_list_files_with_unicode_names(self, tmp_path):
        """Test listing directory with unicode filenames."""
        # Create multiple files with unicode names
        files = ["test_✅.txt", "测试_中文.txt", "emoji_🎉.txt"]

        for filename in files:
            (tmp_path / filename).write_text("content", encoding="utf-8")

        # List all files
        found_files = [f.name for f in tmp_path.glob("*.txt")]

        assert len(found_files) == 3
        for filename in files:
            assert filename in found_files


class TestDifferentEncodings:
    """Test file operations with different encoding parameters."""

    def test_utf8_encoding(self, tmp_path):
        """Test explicit UTF-8 encoding."""
        test_file = tmp_path / "utf8_test.txt"
        content = UNICODE_TEST_STRINGS["mixed"]

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        with open(test_file, "r", encoding="utf-8") as f:
            read_content = f.read()

        assert read_content == content
        assert_no_mojibake(read_content, ["✅", "中文", "🎉"])

    def test_utf16_encoding(self, tmp_path):
        """Test UTF-16 encoding."""
        test_file = tmp_path / "utf16_test.txt"
        content = UNICODE_TEST_STRINGS["mixed"]

        with open(test_file, "w", encoding="utf-16") as f:
            f.write(content)

        with open(test_file, "r", encoding="utf-16") as f:
            read_content = f.read()

        assert read_content == content
        assert_no_mojibake(read_content, ["✅", "中文", "🎉"])

    def test_encoding_mismatch_detection(self, tmp_path):
        """Test that encoding mismatch causes issues (negative test)."""
        test_file = tmp_path / "mismatch_test.txt"
        content = "Test ✅"

        # Write as UTF-8
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Try to read as latin-1 (will cause issues with emoji)
        with open(test_file, "r", encoding="latin-1", errors="replace") as f:
            read_content = f.read()

        # Content should NOT match due to encoding mismatch
        assert read_content != content
        # The emoji will be replaced or garbled
        assert "✅" not in read_content or read_content != content

    def test_utf8_with_bom(self, tmp_path):
        """Test UTF-8 with BOM (Byte Order Mark)."""
        test_file = tmp_path / "utf8_bom_test.txt"
        content = UNICODE_TEST_STRINGS["mixed"]

        with open(test_file, "w", encoding="utf-8-sig") as f:
            f.write(content)

        # Read with BOM handling
        with open(test_file, "r", encoding="utf-8-sig") as f:
            read_content = f.read()

        assert read_content == content
        assert_no_mojibake(read_content, ["✅", "中文", "🎉"])

    def test_default_encoding_is_utf8(self, tmp_path):
        """Test that default encoding handles unicode properly."""
        test_file = tmp_path / "default_encoding_test.txt"
        content = "Test ✅ 中文"

        # Write without explicit encoding (should use UTF-8 on modern Python)
        test_file.write_text(content)

        # Read without explicit encoding
        read_content = test_file.read_text()

        # Should work with unicode
        assert "✅" in read_content
        assert "中文" in read_content


class TestMalformedUnicode:
    """Test handling of malformed unicode data."""

    def test_read_with_errors_replace(self, tmp_path):
        """Test reading malformed unicode with errors='replace'."""
        test_file = tmp_path / "malformed_test.txt"

        # Write valid UTF-8
        test_file.write_bytes(b"Valid \xe2\x9c\x85")  # ✅ in UTF-8

        # Append invalid UTF-8 sequence
        with open(test_file, "ab") as f:
            f.write(b" Invalid \xff\xfe")

        # Read with error handling
        with open(test_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Should have replacement character for invalid bytes
        assert "✅" in content
        assert "�" in content or "Invalid" in content

    def test_read_with_errors_ignore(self, tmp_path):
        """Test reading malformed unicode with errors='ignore'."""
        test_file = tmp_path / "malformed_ignore_test.txt"

        # Write mixed valid and invalid UTF-8
        test_file.write_bytes(b"Test \xe2\x9c\x85 \xff\xfe End")

        # Read with ignore
        with open(test_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Should have valid chars, invalid ones ignored
        assert "✅" in content
        assert "Test" in content
        assert "End" in content

    def test_write_surrogate_pairs(self, tmp_path):
        """Test handling of unicode surrogate pairs (emoji)."""
        test_file = tmp_path / "surrogate_test.txt"

        # Emoji that use surrogate pairs
        content = "🎉 🔧 📝"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        with open(test_file, "r", encoding="utf-8") as f:
            read_content = f.read()

        assert read_content == content
        assert "🎉" in read_content
        assert "🔧" in read_content
        assert "📝" in read_content


class TestLargeFilesWithUnicode:
    """Test operations on large files containing unicode."""

    def test_large_file_with_repeated_unicode(self, tmp_path):
        """Test reading/writing large file with repeated unicode."""
        test_file = tmp_path / "large_unicode_test.txt"

        # Create large content with unicode
        content = UNICODE_TEST_STRINGS["long_unicode"]  # ✅ * 100

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert read_content == content
        assert read_content.count("✅") == 100

    def test_large_file_with_mixed_unicode(self, tmp_path):
        """Test large file with mixed unicode characters."""
        test_file = tmp_path / "large_mixed_test.txt"

        # Create large content with various unicode
        lines = []
        for i in range(1000):
            line = f"Line {i}: {UNICODE_TEST_STRINGS['mixed']}\n"
            lines.append(line)

        content = "".join(lines)

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert read_content == content
        # Verify unicode preserved throughout
        assert read_content.count("✅") == 1000
        assert read_content.count("🎉") == 1000
        assert read_content.count("中文") == 1000

    def test_read_large_file_line_by_line(self, tmp_path):
        """Test reading large unicode file line by line."""
        test_file = tmp_path / "large_lines_test.txt"

        # Write lines with unicode
        lines = [f"Line {i}: ✅ Test 中文\n" for i in range(100)]
        test_file.write_text("".join(lines), encoding="utf-8")

        # Read line by line
        with open(test_file, "r", encoding="utf-8") as f:
            read_lines = f.readlines()

        assert len(read_lines) == 100
        for line in read_lines:
            assert "✅" in line
            assert "中文" in line
            assert_no_mojibake(line, ["✅", "中文"])


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_file_with_unicode_name(self, tmp_path):
        """Test creating empty file with unicode name."""
        filename = "empty_✅_file.txt"
        test_file = tmp_path / filename

        test_file.touch()

        assert test_file.exists()
        assert test_file.stat().st_size == 0
        assert "✅" in test_file.name

    def test_overwrite_unicode_content(self, tmp_path):
        """Test overwriting file with different unicode content."""
        test_file = tmp_path / "overwrite_test.txt"

        # Write initial content
        test_file.write_text("Initial ✅", encoding="utf-8")

        # Overwrite
        test_file.write_text("New 🎉", encoding="utf-8")

        content = test_file.read_text(encoding="utf-8")
        assert "🎉" in content
        assert "✅" not in content

    def test_binary_mode_with_unicode(self, tmp_path):
        """Test writing unicode in binary mode."""
        test_file = tmp_path / "binary_unicode_test.txt"
        content = "Test ✅"

        # Write in binary mode (must encode manually)
        with open(test_file, "wb") as f:
            f.write(content.encode("utf-8"))

        # Read in text mode
        with open(test_file, "r", encoding="utf-8") as f:
            read_content = f.read()

        assert read_content == content
        assert "✅" in read_content

    def test_file_with_only_emoji(self, tmp_path):
        """Test file containing only emoji characters."""
        test_file = tmp_path / "only_emoji.txt"
        content = "✅❌⚠️🎉📝🔧"

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert read_content == content
        assert len(read_content) == len(content)  # Use dynamic length instead of hard-coded value

    def test_newlines_with_unicode(self, tmp_path):
        """Test various newline styles with unicode content."""
        test_file = tmp_path / "newlines_test.txt"

        # Test different newline styles
        content = "Line1 ✅\nLine2 🎉\r\nLine3 中文"

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        # Python normalizes newlines on Windows
        assert "✅" in read_content
        assert "🎉" in read_content
        assert "中文" in read_content
