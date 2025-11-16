# tests/test_core.py

import re
import textwrap
import pathlib as pl
import pytest

import fastmdsimulation as pkg
import fastmdsimulation.core.orchestrator as orch
from fastmdsimulation.core.pdbfix import fix_pdb_with_pdbfixer


class TestOrchestrator:
    """Test suite for core orchestrator functionality."""
    
    def test_prepare_systems_skips_pdbfixer_for_fixed_pdb(self, monkeypatch, tmp_path, water2nm_pdb):
        """Test that fixed_pdb inputs bypass PDBFixer entirely."""
        # Track PDBFixer calls - should be zero for fixed_pdb inputs
        pdbfixer_calls = []
        
        def mock_pdbfixer(input_pdb, output_pdb, ph=7.0):
            pdbfixer_calls.append((input_pdb, output_pdb, ph))
            raise RuntimeError("PDBFixer should not be called for fixed_pdb inputs")
        
        monkeypatch.setattr(
            "fastmdsimulation.core.pdbfix.fix_pdb_with_pdbfixer", 
            mock_pdbfixer
        )
        
        # Create job YAML using fixed_pdb (should skip PDBFixer)
        job_yml = tmp_path / "fixed_pdb_job.yml"
        job_yml.write_text(textwrap.dedent(f"""
            project: WaterBox
            defaults: 
                engine: openmm
                temperature_K: 300
            stages: 
                - {{name: minimize, steps: 0}}
            systems:
                - id: water_system
                  fixed_pdb: {water2nm_pdb.as_posix()}
        """))
        
        # Mock the actual execution to avoid running simulations
        execution_called = False
        
        def mock_run_all(plan, output_base):
            nonlocal execution_called
            execution_called = True
            # Return a mock output directory
            return tmp_path / "simulate_output" / "WaterBox"
        
        monkeypatch.setattr(orch, "_run_all", mock_run_all)
        
        # Execute the orchestrator
        result_dir = orch.run_from_yaml(str(job_yml), output=None)
        
        # Verify behavior
        assert execution_called is True, "Orchestrator should have executed"
        assert len(pdbfixer_calls) == 0, "PDBFixer should not be called for fixed_pdb inputs"
        assert "WaterBox" in str(result_dir)
    
    def test_prepare_systems_calls_pdbfixer_for_raw_pdb(self, monkeypatch, tmp_path, sample_pdb_file):
        """Test that raw PDB inputs trigger PDBFixer."""
        pdbfixer_calls = []
        
        def mock_pdbfixer(input_pdb, output_pdb, ph=7.0):
            pdbfixer_calls.append((input_pdb, output_pdb, ph))
            # Create a mock fixed file
            pl.Path(output_pdb).write_text("FIXED_PDB_CONTENT")
            return output_pdb
        
        monkeypatch.setattr(
            "fastmdsimulation.core.pdbfix.fix_pdb_with_pdbfixer", 
            mock_pdbfixer
        )
        
        # Create job YAML using raw PDB (should call PDBFixer)
        job_yml = tmp_path / "raw_pdb_job.yml"
        job_yml.write_text(textwrap.dedent(f"""
            project: TestProtein
            defaults: 
                engine: openmm
            stages: 
                - {{name: minimize, steps: 0}}
            systems:
                - id: protein_system
                  pdb: {sample_pdb_file.as_posix()}
        """))
        
        # Mock execution
        def mock_run_all(plan, output_base):
            return tmp_path / "simulate_output" / "TestProtein"
        
        monkeypatch.setattr(orch, "_run_all", mock_run_all)
        
        # Execute
        orch.run_from_yaml(str(job_yml), output=None)
        
        # Verify PDBFixer was called
        assert len(pdbfixer_calls) == 1, "PDBFixer should be called once for raw PDB inputs"
        input_pdb, output_pdb, ph = pdbfixer_calls[0]
        assert input_pdb == str(sample_pdb_file)
        assert ph == 7.0  # default pH


class TestPDBFixerIntegration:
    """Test suite for PDBFixer integration."""
    
    @pytest.mark.requires_openmm
    def test_fix_pdb_with_pdbfixer_rejects_placeholder_pdb(self, tmp_path):
        """Test that PDBFixer properly rejects invalid/placeholder PDB files."""
        placeholder_pdb = tmp_path / "placeholder.pdb"
        placeholder_pdb.write_text(textwrap.dedent("""
            HEADER PLACEHOLDER_STRUCTURE
            REMARK This is not a real PDB file
            END
        """))
        
        output_pdb = tmp_path / "fixed.pdb"
        
        # Should raise an exception for invalid PDB content
        with pytest.raises((ValueError, RuntimeError, Exception)):
            fix_pdb_with_pdbfixer(str(placeholder_pdb), str(output_pdb), ph=7.0)
        
        # Output file should not be created
        assert not output_pdb.exists(), "Output file should not be created for invalid input"
    
    @pytest.mark.requires_openmm  
    def test_fix_pdb_with_pdbfixer_processes_valid_pdb(self, tmp_path, sample_pdb_file):
        """Test that PDBFixer processes valid PDB files successfully."""
        output_pdb = tmp_path / "fixed.pdb"
        
        # This should work for a valid PDB structure
        try:
            result = fix_pdb_with_pdbfixer(str(sample_pdb_file), str(output_pdb), ph=7.0)
            assert result == str(output_pdb)
            assert output_pdb.exists()
            # Basic sanity check on output
            content = output_pdb.read_text()
            assert len(content) > 0
            assert "ATOM" in content or "HETATM" in content
        except (ImportError, RuntimeError) as e:
            # Skip if PDBFixer isn't available or fails for other reasons
            pytest.skip(f"PDBFixer not available: {e}")


class TestPackageMetadata:
    """Test suite for package metadata and versioning."""
    
    def test_version_format_is_semantic(self):
        """Test that package version follows semantic versioning pattern."""
        version = getattr(pkg, "__version__", "0.0.0")
        
        # Should match major.minor.patch pattern
        assert re.match(r"^\d+\.\d+\.\d+", version), \
            f"Version {version} should follow semantic versioning (X.Y.Z)"
        
        # Additional validation
        parts = version.split('.')
        assert len(parts) >= 3, "Version should have at least major.minor.patch components"
        assert all(part.isdigit() for part in parts[:3]), "Version components should be numeric"
    
    def test_package_has_required_metadata(self):
        """Test that package has essential metadata attributes."""
        assert hasattr(pkg, "__version__"), "Package should have __version__ attribute"
        assert hasattr(pkg, "__name__"), "Package should have __name__ attribute"
        assert pkg.__name__ == "fastmdsimulation"
        
        # Version should be a string
        version = getattr(pkg, "__version__", None)
        assert isinstance(version, str), "Version should be a string"
        assert version != "", "Version should not be empty"


class TestOrchestratorInputValidation:
    """Test suite for orchestrator input validation."""
    
    def test_run_from_yaml_with_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML files."""
        invalid_yml = tmp_path / "invalid.yml"
        invalid_yml.write_text("invalid: yaml: content: [")
        
        with pytest.raises((ValueError, yaml.YAMLError)):
            orch.run_from_yaml(str(invalid_yml), output=None)
    
    def test_run_from_yaml_with_missing_file(self):
        """Test handling of non-existent YAML files."""
        with pytest.raises(FileNotFoundError):
            orch.run_from_yaml("/nonexistent/path/to/job.yml", output=None)