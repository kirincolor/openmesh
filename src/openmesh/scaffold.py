from __future__ import annotations

from pathlib import Path

DEFAULT_MESH = """mesh:
  name: home
  chief: chief

provider:
  base_url: ${OPENMESH_BASE_URL}
  api_key: ${OPENMESH_API_KEY}
  model: ${OPENMESH_MODEL}

agents:
  - id: chief
    name: Chief
    color: "#7C9CFF"
    role: >
      You are the chief of staff. You talk to the human, decide who should work,
      and summarize results. Do the small things yourself. Delegate real work
      with the handoff tool. Never pretend you finished work you handed off.
    tools: [handoff, memory_read, memory_write, inbox_list, inbox_read, doc_write, schedule_task, list_schedule, cancel_schedule]

  - id: coder
    name: Coder
    color: "#3DDC97"
    role: >
      You write and review code. Stay in your workspace. Explain what you changed.
      If you need research or a decision, hand off — do not invent missing facts.
    tools: [handoff, fs_list, fs_read, fs_write, inbox_list, inbox_read, doc_write, memory_read, memory_write]
    workspace: workspaces/coder

  - id: researcher
    name: Researcher
    color: "#F5C14A"
    role: >
      You look things up and brief the team. Prefer sources over guesses.
      Return a short brief, not a dump.
    tools: [handoff, http_fetch, inbox_list, inbox_read, doc_write, memory_read, memory_write]
    workspace: workspaces/researcher
"""

DEFAULT_ENV = """# OpenAI-compatible endpoint. Works with OpenAI, DeepSeek, Groq, Ollama, etc.
OPENMESH_API_KEY=sk-your-key
OPENMESH_BASE_URL=https://api.openai.com/v1
OPENMESH_MODEL=gpt-4o-mini

# Optional: bind address
OPENMESH_HOST=127.0.0.1
OPENMESH_PORT=8787
"""


def init_project(root: Path) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    mesh = root / "mesh.yaml"
    if mesh.exists():
        raise FileExistsError(f"already a mesh: {mesh}")
    mesh.write_text(DEFAULT_MESH, encoding="utf-8")
    env_example = root / ".env.example"
    if not env_example.exists():
        env_example.write_text(DEFAULT_ENV, encoding="utf-8")
    for agent_id, note in (
        ("coder", "This folder is Coder's jail. Other agents cannot write here.\n"),
        ("researcher", "This folder is Researcher's jail.\n"),
    ):
        folder = root / "workspaces" / agent_id
        folder.mkdir(parents=True, exist_ok=True)
        readme = folder / "README.md"
        if not readme.exists():
            readme.write_text(note, encoding="utf-8")
    return root
