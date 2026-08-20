# OpenMesh

A **local multi-agent workspace**. Talk in a messenger-style app. Each teammate has its own tools. Your API keys stay on this machine. Agents can write files, run commands, and follow local skills or plugins — inside folders you allow.

```
you ── private chat ──► coder
 you ── private chat ──► researcher
 you ── group chat ──► coder + researcher
              │
              └── handoff (help stays in that chat)
```

## Install (no terminal)

Download the build for your OS from [Releases](https://github.com/kirincolor/openmesh/releases):

| OS | File | What to do |
|---|---|---|
| Windows | `OpenMesh-windows-x64.zip` | Unzip and run `OpenMesh\OpenMesh.exe` |
| macOS | `OpenMesh-macos-arm64.zip` | Unzip and open `OpenMesh.app` (right-click → Open the first time) |
| Linux | `OpenMesh-linux-x64.tar.gz` | Extract and run `OpenMesh/OpenMesh` |

The first launch creates your house under the OS app-data folder (Windows: `%APPDATA%\OpenMesh`). Open **Settings** and add one or more API accounts. The chat header only lists those accounts.

If a release zip is not up yet, use the developer install below, then `openmesh desktop`.

## What it is

- **Local first.** The app binds to `127.0.0.1`. Keys never go into prompts.
- **A team, not one bot.** Each teammate has an allowlist. Coder cannot fetch the web unless you give them `http_fetch`.
- **Real chats.** A message to Coder does not appear in Researcher's inbox. A new group starts empty — it does not pull in private history.
- **This computer.** Allowed folders (default `computer/`) can be listed, written, and used as a command cwd. Skills are `SKILL.md` files. Plugins are folders with `plugin.json`.
- **A harness.** Long tool jobs, continue, **Stop**, per-chat busy, schedules.

Isolation is a directory jail, not containers. You bring an OpenAI-compatible model that supports tool calls.

## Features

| Area | What you get |
|---|---|
| Team | Add / edit / delete teammates. Changes write `mesh.yaml`. |
| Chats | One private thread per teammate. `+` → **New group**. Groups do not inherit DMs. |
| APIs | Settings: several named accounts (name, base URL, key, model). Header picker = that list only. |
| Computer | Settings folders + `pc_list` / `pc_read` / `pc_write` / `pc_run`. |
| Skills / plugins | `skills/*/SKILL.md` and `plugins/<id>/plugin.json`. |
| Vault | Per-agent tools. `fs_*` / `shell` stay in `workspaces/<id>/`. `http_fetch` blocks private networks. |
| Harness | Long jobs, auto-continue, **Stop**, per-chat busy. |
| Schedules | Settings, or `schedule_task` (interval, 5-field cron, or one-shot `at`). |
| Files | Composer `+` → upload (max 10 MB) or write a markdown doc. |

## Developer install

Python 3.11+.

```bash
git clone https://github.com/kirincolor/openmesh.git
cd openmesh
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e ".[desktop]"
openmesh desktop
```

Browser-only:

```bash
pip install -e .
openmesh serve
```

Then open [http://127.0.0.1:8787](http://127.0.0.1:8787).

Empty folder:

```bash
openmesh init my-house
cd my-house
openmesh desktop
```

## Providers

Any OpenAI-compatible Chat Completions endpoint. The model must support **tool calls**.

| Provider | Base URL | example model |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Ollama (local) | `http://127.0.0.1:11434/v1` | `qwen2.5` |

Add each one in Settings. Ollama still wants a dummy API key (any string). The header picker is the account for that chat, not a global catalog.

## How to use

1. Add at least one API in Settings.
2. Click a teammate — that is a private chat.
3. `+` in the sidebar: new teammate or new group (at least two teammates).
4. In a group, `@id` talks to one person; with no `@`, members can all reply.
5. Composer `+`: upload, write a document, or mention someone.
6. Long job: watch tool cards; **Stop** cancels that chat only.
7. Settings → folders for computer access. Put skills in `skills/`, plugins in `plugins/`.

## Default team

| id | job | tools (default) |
|---|---|---|
| `chief` | talk to you, split work, schedules | handoff, memory, inbox, docs, schedule, skill list/read, plugin list |
| `coder` | files, shell, computer, skills, plugins | workspace files + `pc_*` + `shell` + skills/plugins |
| `researcher` | look things up | `http_fetch`, inbox, docs, memory, skills |

## Tools

| tool | purpose |
|---|---|
| `handoff` | Give another teammate a concrete task |
| `memory_read` / `memory_write` | Personal notes, or `shared` |
| `fs_list` / `fs_read` / `fs_write` | Files in that agent's workspace |
| `pc_list` / `pc_read` / `pc_write` / `pc_run` | Real files and commands in allowed folders (projects, `.cpp`, `.java`, …) |
| `skill_list` / `skill_read` | Local `SKILL.md` instructions |
| `plugin_list` / `plugin_run` | Local plugins (`plugin.json` + a command) |
| `inbox_list` / `inbox_read` | Files and docs attached to **this** chat |
| `doc_write` | Attach one downloadable file to this chat (keep the real extension) |
| `office_write` | Write Word / Excel / PowerPoint on disk |
| `schedule_task` / `list_schedule` / `cancel_schedule` | Timed follow-ups |
| `http_fetch` | GET a public URL (no localhost / private IPs) |
| `shell` | Command in the agent's workspace only |

The vault denies anything not on the agent's list.

A skill is a markdown file: `skills/<name>/SKILL.md`. A plugin is `plugins/<id>/plugin.json` with a `tools[].command` list. The bundled `echo` plugin is a template.

## Layout

```
mesh.yaml                 team + vault (UI writes this)
.env                      optional default key (gitignored)
src/openmesh/             server, harness, vault
workspaces/<agent>/       per-agent disk jail
computer/                 default computer folder
skills/                   SKILL.md files
plugins/                  plugin.json + runner
data/providers.json       API accounts
data/computer.json        extra allowed folders
data/room.jsonl           messages (per chat thread)
data/chats.json           groups
data/files/               uploads and documents per chat
data/work.json            jobs, schedules, per-chat API
data/ui.json              theme + language
data/memory/              markdown notes
```

## Develop

```bash
pip install -e ".[dev]"
pytest
```

Desktop zip builds run on git tags `v*` via `.github/workflows/release.yml`.

## License

**OpenMesh Non-Commercial Share-Alike License 1.0.** See `LICENSE`.

Individuals, companies, and groups may use, study, and modify the software. They must not obtain profit from it. If you publish a modification, it must stay under this license and you must publish the source.

Selling it, offering it as commercial SaaS, or otherwise making a profit from it requires prior written consent. Ask through [the GitHub repository](https://github.com/kirincolor/openmesh).

The software is provided as is. The authors are not responsible for insecurity, loss, or accidents caused by the design or use of the code.

Tagged releases before this change were MIT; this license applies from the commit that added it onward.
