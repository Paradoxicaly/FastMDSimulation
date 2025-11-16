from unittest.mock import patch

import pytest
import yaml

from fastmdsimulation.core.simulate import simulate_from_pdb


class TestSimulateErrorCases:
    """Test error cases and edge conditions."""

    def test_simulate_from_pdb_pdbfixer_failure(self, tmp_path):
        """Test behavior when PDB fixing fails."""
        # Create a mock PDB file
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        # Mock PDB fixer to raise an exception
        with patch(
            "fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"
        ) as mock_fix_pdb:
            mock_fix_pdb.side_effect = Exception("PDB fixing failed")

            with pytest.raises(Exception, match="PDB fixing failed"):
                simulate_from_pdb(str(pdb_file))

    def test_simulate_from_pdb_invalid_config_yaml(self, tmp_path):
        """Test behavior with invalid YAML config."""
        # Create a mock PDB file
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        invalid_config = tmp_path / "invalid.yml"
        invalid_config.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            simulate_from_pdb(str(pdb_file), config=str(invalid_config))
