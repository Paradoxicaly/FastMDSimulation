# tests/engines/test_openmm_file_formats.py

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fastmdsimulation.engines.openmm_engine import (
    _build_from_amber,
    _build_from_charmm,
    _build_from_gromacs,
    _build_simulation,
)


class TestOpenMMFileFormats:
    """Tests for different molecular file format support."""

    def test_build_simulation_with_custom_constraints(self):
        """Test _build_simulation with custom constraints"""
        with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
            tmp.write(
                b"ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N  \n"
            )
            tmp.write(
                b"ATOM      2  CA  ALA A   1       1.458   0.000   0.000  1.00  0.00           C  \n"
            )
            tmp.flush()

            defaults = {
                "forcefield": ["amber14-all.xml", "amber14/tip3p.xml"],
                "constraints": "allbonds",
                "create_system": {"constraints": "hangles"},  # Override
            }

            run_dir = Path(tempfile.mkdtemp())

            try:
                with (
                    patch("openmm.app.PDBFile"),
                    patch("openmm.app.Modeller"),
                    patch("fastmdsimulation.engines.openmm_engine._load_forcefield"),
                    patch(
                        "fastmdsimulation.engines.openmm_engine.create_system"
                    ) as mock_create,
                    patch(
                        "fastmdsimulation.engines.openmm_engine._make_integrator"
                    ) as mock_integrator,
                    patch(
                        "fastmdsimulation.engines.openmm_engine._new_simulation"
                    ) as mock_new_sim,
                ):

                    # Mock the topology to avoid PDB writing issues
                    mock_topology = Mock()
                    mock_topology.getPeriodicBoxVectors.return_value = None
                    mock_new_sim.return_value = Mock(
                        topology=mock_topology,
                        context=Mock(
                            getState=Mock(
                                return_value=Mock(
                                    getPositions=Mock(return_value=Mock())
                                )
                            )
                        ),
                    )
                    mock_create.return_value = Mock()
                    mock_integrator.return_value = Mock()

                    sim = _build_simulation(Path(tmp.name), defaults, run_dir)
                    assert sim is not None
            finally:
                os.unlink(tmp.name)

    def test_build_from_amber_with_rst7(self):
        """Test _build_from_amber with rst7 file"""
        spec = {"prmtop": "test.prmtop", "rst7": "test.rst7"}
        defaults = {}
        run_dir = Path(tempfile.mkdtemp())

        try:
            with (
                patch("openmm.app.AmberPrmtopFile") as mock_prmtop,
                patch("openmm.app.AmberInpcrdFile") as mock_inpcrd,
                patch(
                    "fastmdsimulation.engines.openmm_engine.create_system"
                ) as mock_create,
                patch(
                    "fastmdsimulation.engines.openmm_engine._make_integrator"
                ) as mock_integrator,
                patch(
                    "fastmdsimulation.engines.openmm_engine._new_simulation"
                ) as mock_new_sim,
                patch(
                    "fastmdsimulation.engines.openmm_engine._save_topology_snapshot"
                ) as mock_save,
            ):

                # Mock topology to avoid PDB writing issues
                mock_topology = Mock()
                mock_topology.getPeriodicBoxVectors.return_value = None
                mock_prmtop.return_value = Mock(topology=mock_topology)
                mock_inpcrd.return_value = Mock(
                    getPositions=Mock(return_value=Mock()), boxVectors=None
                )
                mock_create.return_value = Mock()
                mock_integrator.return_value = Mock()
                mock_new_sim.return_value = Mock(
                    topology=mock_topology,
                    context=Mock(
                        getState=Mock(
                            return_value=Mock(getPositions=Mock(return_value=Mock()))
                        )
                    ),
                )
                mock_save.return_value = None  # Don't actually write files

                sim = _build_from_amber(spec, defaults, run_dir)
                assert sim is not None
        finally:
            pass

    def test_build_from_gromacs_with_itp_and_include_dirs(self):
        """Test _build_from_gromacs with itp files and include directories"""
        spec = {
            "top": "test.top",
            "gro": "test.gro",
            "itp": ["mol.itp"],
            "include_dirs": ["/path/to/includes"],
        }
        defaults = {}
        run_dir = Path(tempfile.mkdtemp())

        try:
            with (
                patch("openmm.app.GromacsGroFile") as mock_gro,
                patch("openmm.app.GromacsTopFile") as mock_top,
                patch(
                    "fastmdsimulation.engines.openmm_engine.create_system"
                ) as mock_create,
                patch(
                    "fastmdsimulation.engines.openmm_engine._make_integrator"
                ) as mock_integrator,
                patch(
                    "fastmdsimulation.engines.openmm_engine._new_simulation"
                ) as mock_new_sim,
                patch(
                    "fastmdsimulation.engines.openmm_engine._save_topology_snapshot"
                ) as mock_save,
            ):

                mock_topology = Mock()
                mock_topology.getPeriodicBoxVectors.return_value = None
                mock_gro.return_value = Mock(
                    getPeriodicBoxVectors=Mock(return_value=None), positions=Mock()
                )
                mock_top.return_value = Mock(topology=mock_topology)
                mock_create.return_value = Mock()
                mock_integrator.return_value = Mock()
                mock_new_sim.return_value = Mock(
                    topology=mock_topology,
                    context=Mock(
                        getState=Mock(
                            return_value=Mock(getPositions=Mock(return_value=Mock()))
                        )
                    ),
                )
                mock_save.return_value = None  # Don't actually write files

                sim = _build_from_gromacs(spec, defaults, run_dir)
                assert sim is not None
        finally:
            pass

    def test_build_from_gromacs_missing_gro(self):
        """Test _build_from_gromacs with missing gro file"""
        spec = {"top": "test.top"}
        defaults = {}
        run_dir = Path(tempfile.mkdtemp())

        with pytest.raises(ValueError):
            _build_from_gromacs(spec, defaults, run_dir)

    def test_build_from_charmm_with_pdb(self):
        """Test _build_from_charmm with PDB coordinates"""
        spec = {"psf": "test.psf", "params": ["par_all36_prot.prm"], "pdb": "test.pdb"}
        defaults = {}
        run_dir = Path(tempfile.mkdtemp())

        try:
            with (
                patch("openmm.app.CharmmPsfFile") as mock_psf,
                patch("openmm.app.CharmmParameterSet") as mock_params,
                patch("openmm.app.PDBFile") as mock_pdb,
                patch(
                    "fastmdsimulation.engines.openmm_engine.create_system"
                ) as mock_create,
                patch(
                    "fastmdsimulation.engines.openmm_engine._make_integrator"
                ) as mock_integrator,
                patch(
                    "fastmdsimulation.engines.openmm_engine._new_simulation"
                ) as mock_new_sim,
                patch(
                    "fastmdsimulation.engines.openmm_engine._save_topology_snapshot"
                ) as mock_save,
            ):

                mock_topology = Mock()
                mock_topology.getPeriodicBoxVectors.return_value = None
                mock_psf.return_value = Mock(topology=mock_topology)
                mock_params.return_value = Mock()
                mock_pdb.return_value = Mock(positions=Mock())
                mock_create.return_value = Mock()
                mock_integrator.return_value = Mock()
                mock_new_sim.return_value = Mock(
                    topology=mock_topology,
                    context=Mock(
                        getState=Mock(
                            return_value=Mock(getPositions=Mock(return_value=Mock()))
                        )
                    ),
                )
                mock_save.return_value = None  # Don't actually write files

                sim = _build_from_charmm(spec, defaults, run_dir)
                assert sim is not None
        finally:
            pass

    def test_build_from_charmm_missing_coordinates(self):
        """Test _build_from_charmm with missing coordinate files"""
        spec = {"psf": "test.psf", "params": ["test.prm"]}
        defaults = {}
        run_dir = Path(tempfile.mkdtemp())

        # Mock the file operations to avoid actual file system calls
        with patch("openmm.app.CharmmPsfFile") as mock_psf:
            mock_psf.return_value = Mock(topology=Mock())
            with patch("openmm.app.CharmmParameterSet"):
                with pytest.raises(ValueError):
                    _build_from_charmm(spec, defaults, run_dir)

    def test_build_from_charmm_missing_parameters(self):
        """Test _build_from_charmm with missing parameter files"""
        spec = {"psf": "test.psf", "pdb": "test.pdb"}
        defaults = {}
        run_dir = Path(tempfile.mkdtemp())

        # Mock the file operations to avoid actual file system calls
        with patch("openmm.app.CharmmPsfFile") as mock_psf:
            mock_psf.return_value = Mock(topology=Mock())
            with patch("openmm.app.PDBFile"):
                with pytest.raises(ValueError):
                    _build_from_charmm(spec, defaults, run_dir)
