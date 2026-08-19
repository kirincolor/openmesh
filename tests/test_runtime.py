from pathlib import Path

from openmesh.bus import Event
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


def test_route_prefer_selected_teammate(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    assert mesh._route("写一个 hello", prefer="coder") == ["coder"]
    assert mesh._route("@chief 先看", prefer="coder") == ["chief"]


def test_prompt_skips_error_events(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    mesh.bus.events.extend(
        [
            Event(kind="user", sender="you", text="hello"),
            Event(kind="error", sender="chief", text="LLM HTTP 401: invalid_api_key"),
            Event(kind="agent", sender="chief", text="ok"),
        ]
    )
    messages = mesh._prompt(mesh.config.agent("chief"), "main")
    log = messages[1]["content"]
    assert "hello" in log
    assert "ok" in log
    assert "401" not in log
    assert "invalid_api_key" not in log
