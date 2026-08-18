from pathlib import Path

import pytest

from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig
from openmesh.vault import Vault, VaultDenied


def _mesh(tmp_path: Path) -> MeshConfig:
    return MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(),
        provider=ProviderConfig(api_key="x"),
        agents=[
            AgentConfig(id="coder", name="Coder", role="code", tools=["fs_read"], workspace="workspaces/coder"),
            AgentConfig(id="chief", name="Chief", role="lead", tools=["handoff"]),
        ],
    )


def test_file_stays_in_workspace(tmp_path: Path) -> None:
    vault = Vault(_mesh(tmp_path))
    coder = vault.config.agent("coder")
    target = vault.resolve_file(coder, "hello.py")
    assert target.parent == vault.workspace(coder)


def test_path_escape_denied(tmp_path: Path) -> None:
    vault = Vault(_mesh(tmp_path))
    coder = vault.config.agent("coder")
    with pytest.raises(VaultDenied):
        vault.resolve_file(coder, "../../secrets.env")


def test_unknown_tool_denied(tmp_path: Path) -> None:
    vault = Vault(_mesh(tmp_path))
    chief = vault.config.agent("chief")
    with pytest.raises(VaultDenied):
        vault.check(chief, "fs_write")
