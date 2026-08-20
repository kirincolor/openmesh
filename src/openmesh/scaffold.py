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
      Read skills when the job is specialized.
    tools: [handoff, memory_read, memory_write, inbox_list, inbox_read, doc_write, office_write, schedule_task, list_schedule, cancel_schedule, skill_list, skill_read, plugin_list]

  - id: coder
    name: Coder
    color: "#3DDC97"
    role: >
      You write real source files and project folders on disk, not markdown stand-ins.
      Use the correct extension (.cpp, .java, .py, …). Use office_write for Word/Excel/PowerPoint.
      Stay inside your workspace or the allowed computer folders.
      Explain what you changed. If you need research or a decision, hand off.
    tools: [handoff, fs_list, fs_read, fs_write, shell, pc_list, pc_read, pc_write, pc_run, office_write, inbox_list, inbox_read, doc_write, memory_read, memory_write, skill_list, skill_read, plugin_list, plugin_run]
    workspace: workspaces/coder

  - id: researcher
    name: Researcher
    color: "#F5C14A"
    role: >
      You look things up and brief the team. Prefer sources over guesses.
      Return a short brief, not a dump.
    tools: [handoff, http_fetch, inbox_list, inbox_read, doc_write, office_write, memory_read, memory_write, skill_list, skill_read]
    workspace: workspaces/researcher
"""

DEFAULT_ENV = """# OpenAI-compatible endpoint. Works with OpenAI, DeepSeek, Groq, Ollama, etc.
# You can also add several APIs in the app Settings.
OPENMESH_API_KEY=sk-your-key
OPENMESH_BASE_URL=https://api.openai.com/v1
OPENMESH_MODEL=gpt-4o-mini

# Optional: bind address
OPENMESH_HOST=127.0.0.1
OPENMESH_PORT=8787
"""

DEFAULT_SKILL = """# Local files

Use this skill when the human wants files, a project, or an office document on this computer.

1. Call `pc_list` on `.` (and `recursive` if needed) to see the allowed folders.
2. Source code is a real file with the right suffix: `main.cpp`, `App.java`, `app.py`. Never put a program in a `.md` file.
3. A project is a folder: create it, then `pc_write` every file (source, headers, build files). Add `README.md` only as a real readme beside the code.
4. Word / Excel / PowerPoint: `office_write` to `reports/name.docx` (or `.xlsx` / `.pptx`).
5. `doc_write` only attaches one downloadable file to the chat. Prefer disk for anything the human will keep.
6. Stay inside allowed computer folders or your workspace.
"""

DEFAULT_PLUGIN = """{
  "name": "echo",
  "description": "Echo arguments back. A template for local plugins.",
  "tools": [
    {
      "name": "echo",
      "command": ["python", "run.py"]
    }
  ]
}
"""

DEFAULT_PLUGIN_RUN = """import json
import sys

payload = json.load(sys.stdin)
args = payload.get("args") or {}
print(json.dumps({"ok": True, "echo": args}, ensure_ascii=False))
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
    write_extras(root)
    return root


def write_extras(root: Path) -> None:
    computer = root / "computer"
    computer.mkdir(parents=True, exist_ok=True)
    note = computer / "README.md"
    if not note.exists():
        note.write_text(
            "Agents may create files and run commands in this folder, plus any folders you add in Settings.\n",
            encoding="utf-8",
        )
    skill = root / "skills" / "local-files" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    if not skill.exists():
        skill.write_text(DEFAULT_SKILL, encoding="utf-8")
    plugin = root / "plugins" / "echo"
    plugin.mkdir(parents=True, exist_ok=True)
    manifest = plugin / "plugin.json"
    runner = plugin / "run.py"
    if not manifest.exists():
        manifest.write_text(DEFAULT_PLUGIN, encoding="utf-8")
    if not runner.exists():
        runner.write_text(DEFAULT_PLUGIN_RUN, encoding="utf-8")
