from pathlib import Path

from fastmdsimulation.core.simulate import (
    _auto_project_name,
    _deep_update,
    build_auto_config,
)


class TestDeepUpdate:
    """Test the _deep_update utility function."""

    def test_deep_update_basic(self):
        """Test basic dictionary merging."""
        dst = {"a": 1, "b": 2}
        src = {"b": 3, "c": 4}
        result = _deep_update(dst, src)
        assert result == {"a": 1, "b": 3, "c": 4}
        assert dst == result  # Should modify in place

    def test_deep_update_nested(self):
        """Test nested dictionary merging."""
        dst = {"a": 1, "nested": {"x": 10, "y": 20}}
        src = {"nested": {"y": 30, "z": 40}, "b": 2}
        result = _deep_update(dst, src)
        expected = {"a": 1, "nested": {"x": 10, "y": 30, "z": 40}, "b": 2}
        assert result == expected

    def test_deep_update_empty_src(self):
        """Test with empty source dictionary."""
        dst = {"a": 1, "b": 2}
        src = {}
        result = _deep_update(dst, src)
        assert result == dst

    def test_deep_update_none_src(self):
        """Test with None source."""
        dst = {"a": 1, "b": 2}
        result = _deep_update(dst, None)
        assert result == dst

    def test_deep_update_overwrite_with_dict(self):
        """Test when scalar value is overwritten with dict."""
        dst = {"a": 1, "b": "scalar"}
        src = {"b": {"nested": "value"}}
        result = _deep_update(dst, src)
        assert result == {"a": 1, "b": {"nested": "value"}}


class TestAutoProjectName:
    """Test the _auto_project_name function."""

    def test_auto_project_name_basic(self):
        """Test basic project name generation."""
        pdb_path = Path("protein.pdb")
        result = _auto_project_name(pdb_path)
        assert result == "protein-auto"

    def test_auto_project_name_complex_path(self):
        """Test with complex file paths."""
        pdb_path = Path("/some/path/to/my_protein.pdb")
        result = _auto_project_name(pdb_path)
        assert result == "my_protein-auto"

    def test_auto_project_name_no_extension(self):
        """Test with file that has no extension."""
        pdb_path = Path("protein")
        result = _auto_project_name(pdb_path)
        assert result == "protein-auto"


class TestBuildAutoConfig:
    """Test the build_auto_config function."""

    def test_build_auto_config_default(self):
        """Test building config with default parameters."""
        fixed_pdb = Path("fixed_protein.pdb")
        config = build_auto_config(fixed_pdb)

        assert config["project"] == "fixed_protein-auto"
        assert config["systems"][0]["pdb"] == "fixed_protein.pdb"
        assert "source_pdb" not in config["systems"][0]  # Should not be in auto config

        # Check defaults
        defaults = config["defaults"]
        assert defaults["engine"] == "openmm"
        assert defaults["temperature_K"] == 300
        assert defaults["timestep_fs"] == 2.0

        # Check stages
        stage_names = [stage["name"] for stage in config["stages"]]
        assert stage_names == ["minimize", "nvt", "npt", "production"]

    def test_build_auto_config_custom_project(self):
        """Test building config with custom project name."""
        fixed_pdb = Path("fixed_protein.pdb")
        project_name = "my-custom-project"
        config = build_auto_config(fixed_pdb, project=project_name)

        assert config["project"] == project_name
        assert config["systems"][0]["pdb"] == "fixed_protein.pdb"

    def test_build_auto_config_none_project(self):
        """Test building config with None project name."""
        fixed_pdb = Path("test.pdb")
        config = build_auto_config(fixed_pdb, project=None)
        assert config["project"] == "test-auto"
