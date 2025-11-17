# tests/engines/test_openmm_system_creation.py

from unittest.mock import Mock, patch

import pytest

from fastmdsimulation.engines.openmm_engine import _new_simulation, create_system


class TestOpenMMSystemCreation:
    """Tests for system creation and simulation initialization."""

    def test_create_system_forcefield_with_unused_kwargs(self):
        """Test create_system with ForceField and unused kwargs"""
        # Import the actual classes to use in isinstance checks
        from openmm.app import ForceField

        mock_ff = Mock(spec=ForceField)
        mock_ff.createSystem.side_effect = [
            ValueError(
                "The argument 'unused_param' was specified to createSystem() but was never used."
            ),
            Mock(),  # Success on second attempt
        ]

        topology = Mock()
        kwargs = {"unused_param": "value", "valid_param": "value"}

        # Mock the regex matching for the error message
        with patch("re.search") as mock_search:
            mock_search.return_value = Mock(group=lambda x: "unused_param")

            system = create_system(mock_ff, topology=topology, kwargs=kwargs)
            assert system is not None

    def test_create_system_unsupported_type(self):
        """Test create_system with unsupported object type"""
        with pytest.raises(TypeError):
            create_system(Mock())  # Unsupported type

    def test_create_system_charmm_psf_missing_paramset(self):
        """Test create_system with CharmmPsfFile but missing paramset"""
        from openmm.app import CharmmPsfFile

        mock_psf = Mock(spec=CharmmPsfFile)

        with pytest.raises(ValueError):
            create_system(mock_psf, kwargs={})

    def test_create_system_forcefield_missing_topology(self):
        """Test create_system with ForceField but missing topology"""
        from openmm.app import ForceField

        mock_ff = Mock(spec=ForceField)

        with pytest.raises(ValueError):
            create_system(mock_ff, kwargs={})

    def test_new_simulation_with_platform_props(self):
        """Test _new_simulation with platform properties"""
        with patch(
            "fastmdsimulation.engines.openmm_engine._select_platform"
        ) as mock_select:
            mock_platform = Mock()
            mock_platform.getName.return_value = (
                "CUDA"  # Fix the string concatenation issue
            )
            mock_select.return_value = mock_platform

            topology = Mock()
            system = Mock()
            integrator = Mock()

            platform_props = {"CudaDeviceIndex": "0", "CudaPrecision": "mixed"}

            with patch("openmm.app.Simulation") as mock_sim_class:
                mock_sim = Mock()
                mock_sim.context.getPlatform.return_value = mock_platform
                mock_sim_class.return_value = mock_sim

                sim = _new_simulation(
                    topology, system, integrator, "CUDA", platform_props
                )
                assert sim == mock_sim
