from pathlib import Path

from fastapi.testclient import TestClient

from openmesh.bus import Event
from openmesh.chats import GroupIn
from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig, load_config
from openmesh.runtime import Mesh
from openmesh.server import create_app


HOUSE = """
mesh: {name: t, chief: chief}
agents:
  - {id: chief, name: Chief, role: lead, tools: [handoff]}
  - {id: coder, name: Coder, role: code, tools: [handoff]}
  - {id: researcher, name: Researcher, role: research, tools: [handoff]}
"""


def _config(tmp_path: Path) -> MeshConfig:
    return MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(chief="chief"),
        provider=ProviderConfig(api_key="x"),
        agents=[
            AgentConfig(id="chief", name="Chief", role="lead", tools=["handoff"]),
            AgentConfig(id="coder", name="Coder", role="code", tools=["handoff"]),
            AgentConfig(id="researcher", name="Researcher", role="research", tools=["handoff"]),
        ],
    )


def _house(tmp_path: Path) -> TestClient:
    (tmp_path / "mesh.yaml").write_text(HOUSE, encoding="utf-8")
    return TestClient(create_app(load_config(tmp_path)))


def test_route_dm_stays_with_that_teammate(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    assert mesh._route("@researcher help", thread="dm:coder") == ["coder"]
    assert mesh._route("hello", prefer="researcher", thread="dm:coder") == ["coder"]


def test_route_group_honors_mention(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    group = mesh.chats.create_group(
        mesh.config, GroupIn(title="ship", members=["coder", "researcher"])
    )
    assert mesh._route("hey @coder", thread=group.id) == ["coder"]
    assert mesh._route("everyone", thread=group.id) == ["coder", "researcher"]


def test_prompt_does_not_leak_other_dm(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    mesh.bus.events.extend(
        [
            Event(kind="user", sender="you", text="secret for coder", thread="dm:coder"),
            Event(kind="agent", sender="coder", text="got it", thread="dm:coder"),
            Event(kind="user", sender="you", text="hello researcher", thread="dm:researcher"),
        ]
    )
    coder = mesh._prompt(mesh.config.agent("coder"), "dm:coder")[1]["content"]
    researcher = mesh._prompt(mesh.config.agent("researcher"), "dm:researcher")[1]["content"]
    assert "secret for coder" in coder
    assert "got it" in coder
    assert "hello researcher" not in coder
    assert "hello researcher" in researcher
    assert "secret for coder" not in researcher


def test_create_group_and_clear_only_that_chat(tmp_path: Path) -> None:
    client = _house(tmp_path)
    res = client.post("/api/chats", json={"title": "Ship", "members": ["coder", "researcher"]})
    assert res.status_code == 200
    chat_id = res.json()["chat"]["id"]
    state = client.get("/api/state").json()
    assert any(item["id"] == chat_id for item in state["chats"])
    assert any(item["id"] == "dm:coder" for item in state["chats"])

    app = client.app
    app.state.mesh.bus.events.extend(
        [
            Event(kind="user", sender="you", text="in group", thread=chat_id),
            Event(kind="user", sender="you", text="in coder", thread="dm:coder"),
        ]
    )
    assert client.delete(f"/api/chats/{chat_id}/messages").status_code == 200
    threads = {event.thread for event in app.state.mesh.bus.events}
    assert chat_id not in threads
    assert "dm:coder" in threads


def test_group_needs_two_members(tmp_path: Path) -> None:
    client = _house(tmp_path)
    res = client.post("/api/chats", json={"title": "Nope", "members": ["coder"]})
    assert res.status_code == 400
