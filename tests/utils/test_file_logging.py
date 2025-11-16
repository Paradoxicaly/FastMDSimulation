"""Tests for file logging functionality."""

import logging
import os
from unittest.mock import patch

from fastmdsimulation.utils.logging import attach_file_logger


class TestAttachFileLogger:
    """Test attach_file_logger function."""

    def test_attach_file_logger_initial(self, tmp_path):
        """Test initial attach_file_logger call."""
        log_file = tmp_path / "test.log"
        logger = attach_file_logger(str(log_file), level=logging.DEBUG, style="plain")

        assert logger.name == "fastmds"
        assert log_file.exists()

        # Test that logging works
        logger.info("Test message")
        with open(log_file) as f:
            log_content = f.read()
        assert "Test message" in log_content

    def test_attach_file_logger_replaces_previous(self, tmp_path):
        """Test attach_file_logger replaces previous file handler."""
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"

        # First call
        logger1 = attach_file_logger(str(log_file1))
        handler_count = len(logger1.handlers)

        # Second call - should replace file handler
        logger2 = attach_file_logger(str(log_file2))
        # Should have same number of handlers (replaced, not added)
        assert len(logger2.handlers) == handler_count

        # Only second file should get new messages
        logger2.info("New message")
        assert not log_file1.exists() or "New message" not in log_file1.read_text()
        assert "New message" in log_file2.read_text()

    @patch.dict(os.environ, {"FASTMDS_LOGLEVEL": "ERROR"})
    def test_attach_file_logger_with_env_level(self, tmp_path):
        """Test attach_file_logger honors FASTMDS_LOGLEVEL environment variable."""
        log_file = tmp_path / "test.log"

        # Clear any existing handlers to ensure fresh state
        logger = logging.getLogger("fastmds")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        logger = attach_file_logger(str(log_file), level=logging.DEBUG)

        # The file handler should have ERROR level from environment
        file_handlers = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.ERROR
