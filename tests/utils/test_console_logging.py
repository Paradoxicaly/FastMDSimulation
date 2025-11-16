"""Tests for console logging setup."""

import logging
import os
from unittest.mock import patch

from fastmdsimulation.utils.logging import setup_console


class TestSetupConsole:
    """Test setup_console function."""

    def test_setup_console_initial(self):
        """Test initial setup_console call."""
        logger = setup_console(level=logging.DEBUG, style="plain")
        assert logger.name == "fastmds"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) >= 1

    def test_setup_console_multiple_calls(self):
        """Test multiple setup_console calls don't duplicate handlers."""
        # First call
        logger1 = setup_console(level=logging.INFO)
        handler_count = len(logger1.handlers)

        # Second call - should not add duplicate handlers
        logger2 = setup_console(level=logging.WARNING)
        assert len(logger2.handlers) == handler_count
        assert logger2.level == logging.WARNING

    @patch.dict(os.environ, {"FASTMDS_LOGLEVEL": "DEBUG"})
    def test_setup_console_with_env_level(self):
        """Test setup_console honors FASTMDS_LOGLEVEL environment variable."""
        logger = setup_console(level=logging.INFO)  # Should be overridden by env
        assert logger.level == logging.DEBUG

    @patch("sys.stdout.isatty")
    def test_setup_console_color_detection(self, mock_isatty):
        """Test setup_console color detection."""
        # Test with TTY
        mock_isatty.return_value = True
        setup_console(style="pretty")
        # Should use color when TTY

        # Test without TTY
        mock_isatty.return_value = False
        setup_console(style="pretty")
        # Should not use color when not TTY

    @patch.dict(os.environ, {"NO_COLOR": "1"})
    @patch("sys.stdout.isatty")
    def test_setup_console_no_color_env(self, mock_isatty):
        """Test setup_console respects NO_COLOR environment variable."""
        mock_isatty.return_value = True  # Would normally use color
        setup_console(style="pretty")
        # Should not use color when NO_COLOR is set
