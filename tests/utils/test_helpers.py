"""Tests for logging helper functions."""

import logging
import os
from unittest.mock import patch

from fastmdsimulation.utils.logging import _resolve_style, _to_level


class TestToLevel:
    """Test _to_level function."""

    def test_to_level_int(self):
        """Test _to_level with integer input."""
        assert _to_level(logging.DEBUG) == logging.DEBUG
        assert _to_level(logging.INFO) == logging.INFO
        assert _to_level(logging.WARNING) == logging.WARNING

    def test_to_level_string(self):
        """Test _to_level with string input."""
        assert _to_level("DEBUG") == logging.DEBUG
        assert _to_level("INFO") == logging.INFO
        assert _to_level("WARNING") == logging.WARNING
        assert _to_level("ERROR") == logging.ERROR
        assert _to_level("CRITICAL") == logging.CRITICAL

    def test_to_level_invalid_string(self):
        """Test _to_level with invalid string input."""
        assert _to_level("INVALID") == logging.INFO  # Default fallback

    def test_to_level_other_types(self):
        """Test _to_level with other types."""
        assert _to_level(None) == logging.INFO  # Default fallback
        assert _to_level(123.45) == logging.INFO  # Default fallback


class TestResolveStyle:
    """Test _resolve_style function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_resolve_style_no_env(self):
        """Test _resolve_style with no environment variable."""
        assert _resolve_style() == "pretty"  # Default
        assert _resolve_style("plain") == "plain"  # Provided default

    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "plain"})
    def test_resolve_style_env_plain(self):
        """Test _resolve_style with FASTMDS_LOG_STYLE=plain."""
        assert _resolve_style() == "plain"
        assert _resolve_style("pretty") == "plain"  # Env overrides default

    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "pretty"})
    def test_resolve_style_env_pretty(self):
        """Test _resolve_style with FASTMDS_LOG_STYLE=pretty."""
        assert _resolve_style() == "pretty"
        assert _resolve_style("plain") == "pretty"  # Env overrides default

    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "invalid"})
    def test_resolve_style_env_invalid(self):
        """Test _resolve_style with invalid FASTMDS_LOG_STYLE."""
        assert _resolve_style() == "pretty"  # Falls back to default
        assert _resolve_style("plain") == "plain"  # Uses provided default
