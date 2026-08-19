import pytest

from openmesh.scaffold import init_project


def test_init_creates_team(tmp_path) -> None:
    root = init_project(tmp_path / "house")
    assert (root / "mesh.yaml").exists()
    assert (root / ".env.example").exists()
    assert (root / "workspaces" / "coder" / "README.md").exists()
    assert (root / "computer" / "README.md").exists()
    assert (root / "skills" / "local-files" / "SKILL.md").exists()
    assert (root / "plugins" / "echo" / "plugin.json").exists()
    with pytest.raises(FileExistsError):
        init_project(root)
