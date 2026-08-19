from datetime import datetime
from pathlib import Path

from openmesh.bus import Event
from openmesh.config import AgentConfig, MeshConfig, MeshMeta, ProviderConfig
from openmesh.files import FileStore
from openmesh.harness import Harness
from openmesh.jobs import ScheduleIn, WorkStore, cron_match
from openmesh.memory import Memory
from openmesh.runtime import Mesh
from openmesh.tools import Toolbelt
from openmesh.vault import Vault


class ScriptLLM:
    def __init__(self, script: list[dict]) -> None:
        self.script = list(script)
        self.models: list[str] = []

    def complete(self, messages, tools=None, model=None, account=None):
        self.models.append(model)
        if not self.script:
            return {"content": "done"}
        return self.script.pop(0)


def _mesh(tmp_path: Path) -> Mesh:
    config = MeshConfig(
        root=tmp_path,
        mesh=MeshMeta(chief="chief"),
        provider=ProviderConfig(api_key="x", model="gpt-4o-mini"),
        agents=[
            AgentConfig(id="chief", name="Chief", role="lead", tools=["handoff", "schedule_task", "list_schedule"]),
            AgentConfig(id="coder", name="Coder", role="code", tools=["handoff"]),
        ],
    )
    return Mesh(config)


def test_harness_continues_long_tool_job(tmp_path: Path) -> None:
    config = _mesh(tmp_path).config
    agent = config.agent("chief")
    llm = ScriptLLM(
        [
            {"content": "", "tool_calls": [{"id": "1", "function": {"name": "list_schedule", "arguments": "{}"}}]},
            {"content": "", "tool_calls": [{"id": "2", "function": {"name": "list_schedule", "arguments": "{}"}}]},
            {"content": "finished"},
        ]
    )
    tools = Toolbelt(Vault(config), Memory(config), FileStore(tmp_path), WorkStore(tmp_path))
    harness = Harness(llm, tools, max_rounds=1, max_continues=2)
    result = harness.run(agent, [{"role": "user", "content": "go"}], "dm:chief")
    assert result.final == "finished"
    assert result.rounds == 3
    assert any(event.kind == "status" and "continuing" in event.text for event in result.traces)


def test_harness_stops_when_cancelled(tmp_path: Path) -> None:
    config = _mesh(tmp_path).config
    agent = config.agent("chief")
    llm = ScriptLLM(
        [{"content": "", "tool_calls": [{"id": "1", "function": {"name": "list_schedule", "arguments": "{}"}}]}]
    )
    tools = Toolbelt(Vault(config), Memory(config), FileStore(tmp_path), WorkStore(tmp_path))
    harness = Harness(llm, tools, max_rounds=8)
    result = harness.run(
        agent,
        [{"role": "user", "content": "go"}],
        "dm:chief",
        should_stop=lambda: True,
    )
    assert result.stopped
    assert any(event.text == "Stopped." for event in result.traces)


def test_cron_and_schedule_due(tmp_path: Path) -> None:
    assert cron_match("0 9 * * 1", datetime(2026, 8, 17, 9, 0))  # Monday
    assert not cron_match("0 9 * * 1", datetime(2026, 8, 17, 10, 0))
    work = WorkStore(tmp_path)
    item = work.add_schedule(
        ScheduleIn(title="ping", thread="dm:chief", text="status", every_seconds=60)
    )
    assert item.next_run is not None
    assert work.due(item.next_run + 1)
    fired_at = item.next_run + 1
    work.mark_fired(item, now=fired_at)
    assert not work.due(fired_at + 1)
    assert work.due(item.next_run + 1)


def test_chat_model_and_thread_busy(tmp_path: Path) -> None:
    mesh = _mesh(tmp_path)
    mesh.set_chat_model("dm:coder", "deepseek-chat")
    assert mesh.work.model_for("dm:coder", "gpt-4o-mini") == "deepseek-chat"
    run = mesh.work.start_run("dm:coder", "long", "deepseek-chat")
    assert mesh.thread_busy("dm:coder")
    assert not mesh.thread_busy("dm:chief")
    mesh.cancel_thread("dm:coder")
    assert mesh.work.is_cancelled(run.id)
    snap = mesh.snapshot()
    ids = [item["id"] if isinstance(item, dict) else item for item in snap["models"]["options"]]
    assert "default" in ids
    assert snap["models"]["by_chat"]["dm:coder"] == "deepseek-chat"
    assert snap["computer"]["roots"]


def test_prompt_uses_chat_log_only(tmp_path: Path) -> None:
    mesh = _mesh(tmp_path)
    mesh.bus.events.append(Event(kind="user", sender="you", text="only coder", thread="dm:coder"))
    text = mesh._prompt(mesh.config.agent("coder"), "dm:coder")[1]["content"]
    assert "only coder" in text
