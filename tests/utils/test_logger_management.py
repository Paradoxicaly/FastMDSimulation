"""Tests for logger management functions."""

import logging

from fastmdsimulation.utils.logging import get_logger, set_level, setup_console


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_base(self):
        """Test get_logger without name returns base logger."""
        logger = get_logger()
        assert logger.name == "fastmds"

    def test_get_logger_child(self):
        """Test get_logger with name returns child logger."""
        child_logger = get_logger("engine.openmm")
        assert child_logger.name == "fastmds.engine.openmm"
        assert child_logger.parent.name == "fastmds"


class TestSetLevel:
    """Test set_level function."""

    def test_set_level_int(self):
        """Test set_level with integer level."""
        logger = setup_console(level=logging.INFO)
        set_level(logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_set_level_string(self):
        """Test set_level with string level."""
        logger = setup_console(level=logging.INFO)
        set_level("WARNING")
        assert logger.level == logging.WARNING

    def test_set_level_invalid(self):
        """Test set_level with invalid level."""
        logger = setup_console(level=logging.INFO)
        original_level = logger.level
        set_level("INVALID_LEVEL")
        # Should handle invalid level gracefully
        assert logger.level == original_level  # Or some default
