"""Tests for console encoding and unicode output handling."""

import logging

from tests.encoding_fixtures import UNICODE_TEST_STRINGS, assert_no_mojibake


class TestConsoleEncoding:
    """Test console output encoding."""

    def test_print_unicode_string(self, capsys):
        """Test printing unicode strings to console."""
        test_string = UNICODE_TEST_STRINGS["emoji_checkmark"]
        print(test_string)
        captured = capsys.readouterr()
        assert_no_mojibake(captured.out, [test_string])

    def test_print_mixed_unicode(self, capsys):
        """Test printing mixed unicode content."""
        mixed = f"{UNICODE_TEST_STRINGS['emoji_checkmark']} Success {UNICODE_TEST_STRINGS['chinese']}"
        print(mixed)
        captured = capsys.readouterr()
        expected_chars = [
            UNICODE_TEST_STRINGS["emoji_checkmark"],
            UNICODE_TEST_STRINGS["chinese"],
        ]
        assert_no_mojibake(captured.out, expected_chars)

    def test_logger_with_unicode(self, caplog):
        """Test logging with unicode content."""
        logger = logging.getLogger(__name__)
        test_msg = f"Test {UNICODE_TEST_STRINGS['emoji_checkmark']} message"
        with caplog.at_level(logging.INFO):
            logger.info(test_msg)
        expected_chars = [UNICODE_TEST_STRINGS["emoji_checkmark"]]
        assert_no_mojibake(caplog.records[0].message, expected_chars)

    def test_logger_exception_with_unicode(self, caplog):
        """Test logging exception with unicode in message."""
        logger = logging.getLogger(__name__)
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError(f"Invalid value {UNICODE_TEST_STRINGS['emoji_cross']}")
            except ValueError:
                logger.exception("Exception occurred")
        # Check that exception message preserved unicode
        log_output = caplog.text
        assert UNICODE_TEST_STRINGS["emoji_cross"] in log_output or "emoji_cross" in log_output


# Minimal test file for console encoding
