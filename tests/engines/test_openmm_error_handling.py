# tests/engines/test_openmm_error_handling.py

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fastmdsimulation.engines.openmm_engine import (
    _build_from_amber,
    _build_simulation,
    create_system,
)


class TestOpenMMErrorHandling:
    """Tests for error handling and edge cases."""

    def test_create_system_unexpected_error(self):
        """Test create_system with unexpected error (not about unused kwargs)"""
        from openmm.app import ForceField

        mock_ff = Mock(spec=ForceField)
        mock_ff.createSystem.side_effect = ValueError("Some other error")

        topology = Mock()

        with pytest.raises(ValueError, match="Some other error"):
            create_system(mock_ff, topology=topology, kwargs={"param": "value"})

    def test_create_system_regex_no_match(self):
        """Test create_system when regex doesn't match error message"""
        from openmm.app import ForceField

        mock_ff = Mock(spec=ForceField)
        mock_ff.createSystem.side_effect = ValueError("Different error format")

        topology = Mock()

        with patch("re.search") as mock_search:
            mock_search.return_value = None  # No match

            # Don't use regex matching, just check the exception type
            with pytest.raises(ValueError):
                create_system(mock_ff, topology=topology, kwargs={"param": "value"})

    def test_build_simulation_missing_pdb(self):
        """Test _build_simulation with missing PDB file"""
        defaults = {}
        run_dir = Mock()

        with pytest.raises(Exception):  # Will fail when trying to read the file
            _build_simulation(Path("nonexistent.pdb"), defaults, run_dir)

    def test_build_from_amber_missing_files(self):
        """Test _build_from_amber with missing files"""
        spec = {"prmtop": "missing.prmtop", "inpcrd": "missing.inpcrd"}
        defaults = {}
        run_dir = Mock()

        with patch("openmm.app.AmberPrmtopFile") as mock_prmtop:
            mock_prmtop.side_effect = Exception("File not found")

            with pytest.raises(Exception):
                _build_from_amber(spec, defaults, run_dir)

    def test_create_system_kwargs_invalid_nonbonded_method(self):
        """Test _create_system_kwargs with invalid nonbonded method"""
        from fastmdsimulation.engines.openmm_engine import _create_system_kwargs

        defaults = {"create_system": {"nonbondedMethod": "invalid_method"}}

        with pytest.raises(ValueError):
            _create_system_kwargs(defaults)
