from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from openmesh.config import load_config
from openmesh.prefs import PrefsIn, load_prefs, patch_prefs
from openmesh.server import create_app
from openmesh.team import AgentIn, TeamError, add_agent, remove_agent, save_team


HOUSE = """
mesh: {name: t, chief: chief}
provider:
  base_url: ${OPENMESH_BASE_URL}
  api_key: ${OPENMESH_API_KEY}
  model: ${OPENMESH_MODEL}
agents:
  - {id: chief, name: Chief, role: lead, tools: [handoff], color: "#7C9CFF"}
"""


def _house(tmp_path: Path) -> TestClient:
    (tmp_path / "mesh.yaml").write_text(HOUSE, encoding="utf-8")
    return TestClient(create_app(load_config(tmp_path)))


def test_create_and_delete_agent_updates_yaml(tmp_path: Path) -> None:
    client = _house(tmp_path)
    res = client.post(
        "/api/agents",
        json={"name": "Docs", "role": "answers from files", "tools": ["fs_read", "handoff"]},
    )
    assert res.status_code == 200
    agent = res.json()["agent"]
    assert agent["id"] == "docs"
    assert agent["workspace"] == "workspaces/docs"
    yaml_text = (tmp_path / "mesh.yaml").read_text(encoding="utf-8")
    assert "id: docs" in yaml_text
    assert "${OPENMESH_API_KEY}" in yaml_text
    assert "sk-" not in yaml_text

    gone = client.delete("/api/agents/docs")
    assert gone.status_code == 200
    again = yaml.safe_load((tmp_path / "mesh.yaml").read_text(encoding="utf-8"))
    assert [item["id"] for item in again["agents"]] == ["chief"]


def test_unknown_tool_rejected(tmp_path: Path) -> None:
    client = _house(tmp_path)
    res = client.post("/api/agents", json={"name": "X", "tools": ["nuke"]})
    assert res.status_code == 400
    assert "unknown tools" in res.json()["detail"]


def test_cannot_delete_last_teammate(tmp_path: Path) -> None:
    client = _house(tmp_path)
    res = client.delete("/api/agents/chief")
    assert res.status_code == 400
    assert "last teammate" in res.json()["detail"]


def test_edit_agent_and_reassign_chief(tmp_path: Path) -> None:
    client = _house(tmp_path)
    client.post("/api/agents", json={"id": "coder", "name": "Coder", "tools": ["fs_write"]})
    client.delete("/api/agents/chief")
    state = client.get("/api/state").json()
    assert state["mesh"]["chief"] == "coder"
    res = client.put(
        "/api/agents/coder",
        json={"name": "Builder", "role": "writes code", "tools": ["fs_write", "handoff"], "color": "#3DDC97"},
    )
    assert res.status_code == 200
    assert res.json()["agent"]["name"] == "Builder"


def test_state_includes_prefs_and_tools(tmp_path: Path) -> None:
    client = _house(tmp_path)
    state = client.get("/api/state").json()
    assert state["prefs"] == {"theme": "light", "language": "en"}
    assert "handoff" in state["tools"]
    assert "shell" in state["tools"]
    assert "office_write" in state["tools"]


def test_prefs_roundtrip(tmp_path: Path) -> None:
    client = _house(tmp_path)
    res = client.put("/api/prefs", json={"theme": "dark", "language": "zh"})
    assert res.status_code == 200
    assert res.json()["prefs"] == {"theme": "dark", "language": "zh"}
    assert client.get("/api/state").json()["prefs"]["language"] == "zh"
    prefs = load_prefs(tmp_path)
    assert prefs.theme == "dark"
    assert patch_prefs(tmp_path, PrefsIn(language="en")).language == "en"


def test_save_team_never_writes_raw_key(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text(
        "mesh: {name: t, chief: chief}\nprovider: {api_key: sk-live-secret}\nagents: [{id: chief, name: C, role: r}]\n",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    save_team(config)
    text = (tmp_path / "mesh.yaml").read_text(encoding="utf-8")
    assert "sk-live-secret" not in text
    assert "${OPENMESH_API_KEY}" in text


def test_add_agent_rejects_reserved_id(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text(HOUSE, encoding="utf-8")
    config = load_config(tmp_path)
    try:
        add_agent(config, AgentIn(id="you", name="You"))
        raise AssertionError("should refuse")
    except TeamError:
        pass
    try:
        remove_agent(config, "missing")
        raise AssertionError("should miss")
    except KeyError:
        pass
