"""Tests for package initialization and version handling."""

import sys
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch


def test_version_logic_direct():
    """Test the version retrieval logic directly by reloading the module."""
    # Test successful version retrieval
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = "1.2.3"

        # Remove the module from cache and re-import to trigger version retrieval
        if "fastmdsimulation" in sys.modules:
            del sys.modules["fastmdsimulation"]
        if "fastmdsimulation.__init__" in sys.modules:
            del sys.modules["fastmdsimulation.__init__"]

        from fastmdsimulation import __version__

        assert __version__ == "1.2.3"

    # Test PackageNotFoundError
    with patch("importlib.metadata.version") as mock_version:
        mock_version.side_effect = PackageNotFoundError("Package not found")

        # Remove the module from cache and re-import
        if "fastmdsimulation" in sys.modules:
            del sys.modules["fastmdsimulation"]
        if "fastmdsimulation.__init__" in sys.modules:
            del sys.modules["fastmdsimulation.__init__"]

        from fastmdsimulation import __version__

        assert __version__ == "0.0.0"

    # Test generic exception
    with patch("importlib.metadata.version") as mock_version:
        mock_version.side_effect = Exception("Any error")

        # Remove the module from cache and re-import
        if "fastmdsimulation" in sys.modules:
            del sys.modules["fastmdsimulation"]
        if "fastmdsimulation.__init__" in sys.modules:
            del sys.modules["fastmdsimulation.__init__"]

        from fastmdsimulation import __version__

        assert __version__ == "0.0.0"


def test_fastmdsimulation_import():
    """Test that FastMDSimulation can be imported from package."""
    from fastmdsimulation import FastMDSimulation, __version__

    assert FastMDSimulation is not None
    assert __version__ is not None


def test_all_imports():
    """Test that __all__ contains expected exports."""
    from fastmdsimulation import __all__

    expected_exports = ["FastMDSimulation", "__version__"]
    assert set(__all__) == set(expected_exports)
