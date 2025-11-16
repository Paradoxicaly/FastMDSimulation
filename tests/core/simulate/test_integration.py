from unittest.mock import patch

import pytest
import yaml

from fastmdsimulation.core.simulate import simulate_from_pdb


@pytest.mark.integration
@pytest.mark.requires_openmm
class TestSimulateIntegration:
    """Integration tests for the simulate module."""

    def test_end_to_end_workflow(self, sample_pdb_file, tmp_path):
        """Test complete workflow from PDB to simulation."""
        # Mock both dependencies - CORRECTED import path
        with (
            patch("fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"),
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Setup
            mock_run_from_yaml.return_value = str(tmp_path / "final_output")
            outdir = str(tmp_path / "sim_output")

            # Execute
            result = simulate_from_pdb(str(sample_pdb_file), outdir=outdir)

            # Verify
            assert result == str(tmp_path / "final_output")
            mock_run_from_yaml.assert_called_once()

            # Check directory structure was created
            build_dir = tmp_path / "sim_output" / "sample-auto" / "_build"
            assert build_dir.exists()

    def test_simulate_from_pdb_creates_yaml_content(self, tmp_path):
        """Test that the auto-generated YAML has correct content."""
        # Create a minimal PDB file
        pdb_file = tmp_path / "test.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        # Mock both dependencies - CORRECTED import path
        with (
            patch("fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"),
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Capture the YAML file that would be created
            created_yaml_path = None

            def capture_yaml_path(path, *args, **kwargs):
                nonlocal created_yaml_path
                created_yaml_path = path
                return "/mock/output"

            mock_run_from_yaml.side_effect = capture_yaml_path

            # Run the function
            simulate_from_pdb(str(pdb_file), outdir=str(tmp_path / "output"))

            # Verify YAML was created and has correct content
            assert created_yaml_path is not None
            assert created_yaml_path.endswith("job.auto.yml")

            with open(created_yaml_path, "r") as f:
                config = yaml.safe_load(f)

            # Check key structure
            assert "project" in config
            assert "defaults" in config
            assert "stages" in config
            assert "systems" in config
            assert "sweep" in config

            # Check specific values
            assert config["project"] == "test-auto"
            assert config["systems"][0]["source_pdb"] == str(pdb_file)
            assert "fixed" in config["systems"][0]["pdb"]  # Should point to fixed PDB
