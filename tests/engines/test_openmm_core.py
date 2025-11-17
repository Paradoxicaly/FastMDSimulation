# tests/engines/test_openmm_core.py

from unittest.mock import Mock, patch

import pytest

from fastmdsimulation.engines.openmm_engine import (
    _constraints_from_str,
    _create_system_kwargs,
    _get_minimize_tolerance,
    _load_forcefield,
    _make_integrator,
    _map_nonbonded_method,
    _parse_ions,
    _select_platform,
)


class TestOpenMMCore:
    """Core functionality tests for OpenMM engine utilities."""

    def test_load_forcefield_fallback(self):
        """Test _load_forcefield with fallback to openmmforcefields"""
        with patch("openmm.app.ForceField") as mock_ff:
            # Mock the import to avoid the patch error
            with patch.dict("sys.modules", {"openmmforcefields": Mock()}):
                mock_ff.side_effect = [Exception("First attempt failed"), mock_ff]
                result = _load_forcefield(["test.xml"])
                assert result is not None

    def test_select_platform_auto(self):
        """Test _select_platform with 'auto' selection"""
        with patch("openmm.Platform") as mock_platform:
            mock_platform.getPlatformByName.side_effect = [
                Exception("CUDA failed"),
                Exception("OpenCL failed"),
                Mock(),  # CPU succeeds
            ]
            mock_platform.getPlatform.return_value = Mock()
            platform = _select_platform("auto")
            assert platform is not None

    def test_select_platform_specific(self):
        """Test _select_platform with specific platform"""
        with patch("openmm.Platform") as mock_platform:
            mock_platform.getPlatformByName.return_value = Mock()
            platform = _select_platform("CUDA")
            assert platform is not None

    def test_parse_ions_dict(self):
        """Test _parse_ions with dictionary configuration"""
        defaults = {"ions": {"positiveIon": "K+", "negativeIon": "Br-"}}
        pos, neg = _parse_ions(defaults)
        assert pos == "K+"
        assert neg == "Br-"

    def test_parse_ions_unknown_string(self):
        """Test _parse_ions with unknown string configuration"""
        defaults = {"ions": "UnknownSalt"}
        pos, neg = _parse_ions(defaults)
        assert pos == "Na+"
        assert neg == "Cl-"

    def test_get_minimize_tolerance_kjmol_per_nm(self):
        """Test _get_minimize_tolerance with kjmol_per_nm parameter"""
        defaults = {"minimize_tolerance_kjmol_per_nm": 5.0}
        tol, val = _get_minimize_tolerance(defaults)
        assert val == 5.0

    def test_constraints_from_str_variations(self):
        """Test _constraints_from_str with various string inputs"""
        assert _constraints_from_str("none") is None
        assert _constraints_from_str("no") is None
        assert _constraints_from_str("off") is None
        assert _constraints_from_str("false") is None

        from openmm.app import AllBonds, HAngles, HBonds

        assert _constraints_from_str("hbonds") == HBonds
        assert _constraints_from_str("allbonds") == AllBonds
        assert _constraints_from_str("hangles") == HAngles

    def test_map_nonbonded_method_unknown(self):
        """Test _map_nonbonded_method with unknown method"""
        result = _map_nonbonded_method("unknown_method")
        assert result is None

    def test_create_system_kwargs_comprehensive(self):
        """Test _create_system_kwargs with comprehensive configuration"""
        defaults = {
            "create_system": {
                "constraints": "hbonds",
                "nonbondedMethod": "pme",
                "nonbondedCutoff_nm": 1.0,
                "switchDistance_nm": 0.8,
                "useSwitchingFunction": True,
                "rigidWater": True,
                "longRangeDispersionCorrection": True,
                "ewaldErrorTolerance": 0.0005,
                "hydrogenMass_amu": 1.5,
                "removeCMMotion": True,
            }
        }
        kwargs = _create_system_kwargs(defaults)

        assert "constraints" in kwargs
        assert "nonbondedMethod" in kwargs
        assert "nonbondedCutoff" in kwargs
        assert "switchingDistance" in kwargs
        assert "useSwitchingFunction" in kwargs
        assert "rigidWater" in kwargs
        assert "useDispersionCorrection" in kwargs
        assert "ewaldErrorTolerance" in kwargs
        assert "hydrogenMass" in kwargs
        assert "_removeCMMotion" in kwargs

    def test_make_integrator_langevin_middle(self):
        """Test _make_integrator with langevin_middle integrator"""
        defaults = {
            "integrator": {
                "name": "langevin_middle",
                "temperature_K": 310.0,
                "timestep_fs": 4.0,
                "friction_ps": 2.0,
            }
        }

        with patch("openmm.LangevinMiddleIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None

    def test_make_integrator_brownian(self):
        """Test _make_integrator with brownian integrator"""
        defaults = {"integrator": "brownian"}

        with patch("openmm.BrownianIntegrator") as mock_integrator:
            mock_integrator.return_value = Mock()
            integrator = _make_integrator(defaults)
            assert integrator is not None

    def test_make_integrator_unknown(self):
        """Test _make_integrator with unknown integrator"""
        defaults = {"integrator": "unknown_integrator"}

        with pytest.raises(ValueError):
            _make_integrator(defaults)
