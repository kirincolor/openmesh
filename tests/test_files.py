from pathlib import Path

from fastapi.testclient import TestClient

from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig, load_config
from openmesh.files import FileError, FileStore
from openmesh.runtime import Mesh
from openmesh.server import create_app


HOUSE = """
mesh: {name: t, chief: chief}
agents:
  - {id: chief, name: Chief, role: lead, tools: [handoff, inbox_list, inbox_read, doc_write]}
  - {id: coder, name: Coder, role: code, tools: [inbox_read, doc_write]}
"""


def _config(tmp_path: Path) -> MeshConfig:
    return MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(chief="chief"),
        provider=ProviderConfig(api_key="x"),
        agents=[
            AgentConfig(id="chief", name="Chief", role="lead", tools=["inbox_list", "inbox_read", "doc_write"]),
            AgentConfig(id="coder", name="Coder", role="code", tools=["inbox_read", "doc_write"]),
        ],
    )


def test_store_rejects_escape_and_oversize(tmp_path: Path) -> None:
    store = FileStore(tmp_path)
    rec = store.save_bytes("dm:coder", "notes.md", b"# hi\n")
    assert rec.name == "notes.md"
    assert store.read_text(rec.id, "dm:coder").startswith("# hi")
    try:
        store.save_bytes("dm:coder", "big.bin", b"x" * (10 * 1024 * 1024 + 1))
        raise AssertionError("should refuse")
    except FileError:
        pass
    try:
        store.read_text(rec.id, "dm:chief")
        raise AssertionError("should stay in chat")
    except FileError:
        pass


def test_doc_not_visible_in_other_chat_prompt(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    mesh.files.write_doc("dm:coder", "Plan", "secret plan")
    coder = mesh._prompt(mesh.config.agent("coder"), "dm:coder")[0]["content"]
    chief = mesh._prompt(mesh.config.agent("chief"), "dm:chief")[0]["content"]
    assert "Plan.md" in coder
    assert "Plan.md" not in chief


def test_upload_and_download(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text(HOUSE, encoding="utf-8")
    client = TestClient(create_app(load_config(tmp_path)))
    res = client.post(
        "/api/chats/dm:coder/files",
        files={"file": ("brief.md", b"hello team", "text/markdown")},
    )
    assert res.status_code == 200
    file_id = res.json()["file"]["id"]
    down = client.get(f"/api/files/{file_id}")
    assert down.status_code == 200
    assert down.content == b"hello team"
    events = client.get("/api/state").json()["events"]
    assert any(item["kind"] == "file" and item["thread"] == "dm:coder" for item in events)


def test_doc_write_tool_stays_in_thread(tmp_path: Path) -> None:
    mesh = Mesh(_config(tmp_path))
    chief = mesh.config.agent("chief")
    result = mesh.tools.run(chief, "doc_write", {"title": "Brief", "content": "done"}, thread="dm:chief")
    assert result.startswith("FILE::")
    listed = mesh.tools.run(chief, "inbox_list", {}, thread="dm:chief")
    assert "Brief.md" in listed
    empty = mesh.tools.run(chief, "inbox_list", {}, thread="dm:coder")
    assert "Brief.md" not in empty
