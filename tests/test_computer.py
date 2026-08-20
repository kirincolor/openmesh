from pathlib import Path

import pytest

from openmesh.computer import Computer
from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig
from openmesh.files import FileStore
from openmesh.jobs import WorkStore
from openmesh.memory import Memory
from openmesh.plugins import PluginBook
from openmesh.runtime import Mesh
from openmesh.skills import SkillBook
from openmesh.tools import Toolbelt
from openmesh.vault import Vault, VaultDenied


def test_computer_stays_in_roots(tmp_path: Path) -> None:
    box = Computer(tmp_path)
    inside = box.resolve("notes.md")
    assert inside.parent == box.roots[0]
    inside.write_text("hi", encoding="utf-8")
    outside = tmp_path.parent / "nope.txt"
    with pytest.raises(VaultDenied):
        box.resolve(str(outside))


def test_pc_and_skill_tools(tmp_path: Path) -> None:
    config = MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(chief="coder"),
        provider=ProviderConfig(api_key="x"),
        agents=[
            AgentConfig(
                id="coder",
                name="Coder",
                role="code",
                tools=["pc_list", "pc_write", "pc_read", "pc_run", "skill_list", "skill_read", "plugin_list", "plugin_run"],
            )
        ],
    )
    mesh = Mesh(config)
    agent = config.agent("coder")
    wrote = mesh.tools.run(agent, "pc_write", {"path": "hello.txt", "content": "openmesh"})
    assert wrote.startswith("LOCAL::")
    assert "hello.txt" in wrote
    assert "openmesh" in mesh.tools.run(agent, "pc_read", {"path": "hello.txt"})
    listing = mesh.tools.run(agent, "pc_list", {"path": "."})
    assert "hello.txt" in listing
    out = mesh.tools.run(agent, "pc_run", {"command": "python -c \"print(2+2)\""})
    assert "4" in out
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "skills" / "demo" / "SKILL.md").write_text("# Demo\nDo the demo.\n", encoding="utf-8")
    assert "demo" in mesh.tools.run(agent, "skill_list", {})
    assert "Do the demo" in mesh.tools.run(agent, "skill_read", {"skill": "demo"})
    plugin = tmp_path / "plugins" / "echo"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text(
        '{"name":"echo","tools":[{"name":"echo","command":["python","run.py"]}]}',
        encoding="utf-8",
    )
    (plugin / "run.py").write_text(
        "import json,sys; print(json.dumps({'echo': json.load(sys.stdin).get('args')}))\n",
        encoding="utf-8",
    )
    listed = mesh.tools.run(agent, "plugin_list", {})
    assert "echo" in listed
    ran = mesh.tools.run(agent, "plugin_run", {"plugin": "echo", "tool": "echo", "args": {"n": 1}})
    assert "1" in ran


def test_computer_tool_denied_without_grant(tmp_path: Path) -> None:
    config = MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(),
        provider=ProviderConfig(api_key="x"),
        agents=[AgentConfig(id="chief", name="Chief", role="lead", tools=["handoff"])],
    )
    tools = Toolbelt(Vault(config), Memory(config), FileStore(tmp_path), WorkStore(tmp_path), Computer(tmp_path), SkillBook(tmp_path), PluginBook(tmp_path))
    with pytest.raises(VaultDenied):
        tools.run(config.agent("chief"), "pc_write", {"path": "x.txt", "content": "no"})
