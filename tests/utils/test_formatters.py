"""Tests for logging formatters."""

import logging
from datetime import datetime

from fastmdsimulation.utils.logging import _PlainISOFormatter, _PrettyFormatter


class TestPrettyFormatter:
    """Test _PrettyFormatter class."""

    def test_pretty_formatter_with_color(self):
        """Test pretty formatter with color enabled."""
        formatter = _PrettyFormatter(use_color=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = datetime.now().timestamp()

        result = formatter.format(record)
        assert "✓" in result  # INFO icon
        assert "INFO" in result
        assert "Test message" in result

    def test_pretty_formatter_without_color(self):
        """Test pretty formatter with color disabled."""
        formatter = _PrettyFormatter(use_color=False)
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.created = datetime.now().timestamp()

        result = formatter.format(record)
        assert "⚠" in result  # WARNING icon
        assert "WARNING" in result
        assert "Warning message" in result
        # Should not contain color codes
        assert "\x1b[" not in result

    def test_pretty_formatter_all_levels(self):
        """Test pretty formatter with all log levels."""
        formatter = _PrettyFormatter(use_color=False)
        levels = [
            (logging.DEBUG, "·"),
            (logging.INFO, "✓"),
            (logging.WARNING, "⚠"),
            (logging.ERROR, "✗"),
            (logging.CRITICAL, "‼"),
        ]

        for level, expected_icon in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg=f"Message for {logging.getLevelName(level)}",
                args=(),
                exc_info=None,
            )
            record.created = datetime.now().timestamp()

            result = formatter.format(record)
            assert expected_icon in result
            assert logging.getLevelName(level) in result


class TestPlainISOFormatter:
    """Test _PlainISOFormatter class."""

    def test_plain_iso_formatter_basic(self):
        """Test plain ISO formatter basic functionality."""
        formatter = _PlainISOFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = datetime.now().timestamp()
        record.msecs = 123  # Set milliseconds

        result = formatter.format(record)
        assert " - INFO - Test message" in result
        # Should include date and time
        assert "-" in result.split(" ")[0]  # Date part has dashes

    def test_plain_iso_formatter_with_milliseconds(self):
        """Test plain ISO formatter includes milliseconds."""
        formatter = _PlainISOFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Debug message",
            args=(),
            exc_info=None,
        )
        record.created = datetime.now().timestamp()
        record.msecs = 456

        result = formatter.format(record)
        # Should contain milliseconds
        assert ",456" in result or " - DEBUG - Debug message" in result
