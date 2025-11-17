# tests/engines/test_openmm_configuration.py

from unittest.mock import Mock, patch

import pytest

from fastmdsimulation.engines.openmm_engine import (
    _create_system_kwargs,
    _make_integrator,
)


class TestOpenMMConfiguration:
    """Tests for configuration parsing and validation."""

    def test_create_system_kwargs_edge_cases(self):
        """Test edge cases in system creation kwargs."""
        # Empty create_system section
        defaults = {"create_system": {}}
        kwargs = _create_system_kwargs(defaults)
        assert isinstance(kwargs, dict)

        # None create_system section
        defaults = {"create_system": None}
        kwargs = _create_system_kwargs(defaults)
        assert isinstance(kwargs, dict)

        # Missing create_system section
        defaults = {}
        kwargs = _create_system_kwargs(defaults)
        assert isinstance(kwargs, dict)

    def test_create_system_kwargs_invalid_nonbonded_method(self):
        """Test _create_system_kwargs with invalid nonbonded method."""
        defaults = {"create_system": {"nonbondedMethod": "invalid_method"}}

        with pytest.raises(ValueError, match="Unknown nonbondedMethod"):
            _create_system_kwargs(defaults)

    def test_make_integrator_variable_types(self):
        """Test _make_integrator with variable step integrators."""
        # Variable Langevin
        defaults = {
            "integrator": {
                "name": "variable_langevin",
                "temperature_K": 300.0,
                "friction_ps": 1.0,
                "error_tolerance": 0.0001,
            }
        }

        with patch("openmm.VariableLangevinIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None

        # Variable Verlet
        defaults = {
            "integrator": {"name": "variable_verlet", "error_tolerance": 0.0001}
        }

        with patch("openmm.VariableVerletIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None

    def test_make_integrator_fallback_defaults(self):
        """Test _make_integrator uses top-level defaults when integrator spec is minimal."""
        defaults = {
            "temperature_K": 310.0,
            "timestep_fs": 3.0,
            "friction_ps": 2.0,
            "integrator": "langevin",  # Just a string
        }

        with patch("openmm.LangevinIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None
            # Should use top-level defaults

    def test_integrator_error_tolerance_aliases(self):
        """Test integrator error tolerance with different parameter names."""
        # Test with error_tolerance
        defaults = {
            "integrator": {"name": "variable_langevin", "error_tolerance": 0.001}
        }

        with patch("openmm.VariableLangevinIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None

        # Test with errorTol (alias)
        defaults = {"integrator": {"name": "variable_langevin", "errorTol": 0.002}}

        with patch("openmm.VariableLangevinIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None
