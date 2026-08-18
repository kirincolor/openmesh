from pathlib import Path

from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig
from openmesh.runtime import Mesh


def _config(tmp_path: Path) -> MeshConfig:
    return MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(chief="chief"),
        provider=ProviderConfig(api_key="x"),
        agents=[
            AgentConfig(id="chief", name="Chief", role="lead", tools=["handoff"]),
            AgentConfig(id="coder", name="Coder", role="code", tools=["fs_read"]),
        ],
    )


def test_route_default_chief(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    assert mesh._route("写一个 hello") == ["chief"]


def test_route_mention(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    assert mesh._route("请 @coder 改文件") == ["coder"]
