import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from openmesh.bus import Bus, Event
from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig
from openmesh.runtime import Mesh
from openmesh.scaffold import init_project
from openmesh.secrets import redact, write_env
from openmesh.server import create_app
from openmesh.ssrf import blocked_reason


def _config(tmp_path: Path) -> MeshConfig:
    return MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(),
        provider=ProviderConfig(api_key=""),
        agents=[
            AgentConfig(id="chief", name="Chief", role="lead", tools=["handoff"]),
            AgentConfig(id="coder", name="Coder", role="code", tools=["fs_write"], workspace="workspaces/coder"),
        ],
    )


def test_route_default_is_chief(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    assert mesh._route("写一个 hello") == ["chief"]


def test_route_mention(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    assert mesh._route("请 @coder 改文件") == ["coder"]


def test_bus_persists_and_skips_status(tmp_path: Path) -> None:
    path = tmp_path / "room.jsonl"

    async def go() -> None:
        bus = Bus(path)
        await bus.publish(Event(kind="user", sender="you", text="hi"))
        await bus.publish(Event(kind="status", sender="mesh", text="thinking"))

    asyncio.run(go())
    again = Bus(path)
    assert [event.kind for event in again.events] == ["user"]
    assert again.events[0].text == "hi"


def test_ssrf_blocks_loopback() -> None:
    assert blocked_reason("http://127.0.0.1/secret")
    assert blocked_reason("http://localhost:8787/")
    assert blocked_reason("file:///etc/passwd")


def test_redact_key() -> None:
    assert redact("Bearer sk-secret boom", "sk-secret") == "Bearer *** boom"


def test_write_env(tmp_path: Path) -> None:
    write_env(tmp_path, {"OPENMESH_API_KEY": "sk-test", "OPENMESH_MODEL": "x"})
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "OPENMESH_API_KEY=sk-test" in text
    write_env(tmp_path, {"OPENMESH_API_KEY": "sk-2"})
    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "sk-2" in text
    assert "sk-test" not in text


def test_init_and_refuse_twice(tmp_path: Path) -> None:
    root = init_project(tmp_path / "house")
    assert (root / "mesh.yaml").exists()
    assert (root / "workspaces" / "coder" / "README.md").exists()
    try:
        init_project(root)
        raise AssertionError("should refuse")
    except FileExistsError:
        pass


def test_chat_requires_key(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text("mesh: {name: t, chief: chief}\nagents: [{id: chief, name: C, role: r}]\n", encoding="utf-8")
    app = create_app(_config(tmp_path))
    client = TestClient(app)
    res = client.post("/api/chat", json={"text": "hi"})
    assert res.status_code == 400
    assert "key" in res.json()["detail"].lower()


def test_favicon_is_not_json_404(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text("mesh: {name: t, chief: chief}\nagents: [{id: chief, name: C, role: r}]\n", encoding="utf-8")
    client = TestClient(create_app(_config(tmp_path)))
    res = client.get("/favicon.ico")
    assert res.status_code == 200
    assert "svg" in res.headers.get("content-type", "")


def test_clear_room(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text("mesh: {name: t, chief: chief}\nagents: [{id: chief, name: C, role: r}]\n", encoding="utf-8")
    app = create_app(_config(tmp_path))
    app.state.mesh.bus.events.append(Event(kind="error", sender="mesh", text="old"))
    client = TestClient(app)
    res = client.delete("/api/room")
    assert res.status_code == 200
    assert app.state.mesh.bus.events == []
