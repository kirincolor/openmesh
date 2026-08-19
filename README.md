# OpenMesh

A **local multi-agent workspace**. You talk in a messenger-style app. Each teammate is an agent with its own tools. Your API key stays on this machine.

OpenMesh is for people who want a small team of agents on their own computer — not a hosted room, not a single chatbot with every tool unlocked. Permissions are split. Chats are separate. Long jobs and schedules run in the harness.

```
you ── private chat ──► coder
 you ── private chat ──► researcher
 you ── group chat ──► coder + researcher
              │
              └── handoff (help stays in that chat)
```

## What it is

- **Local first.** `openmesh serve` binds to `127.0.0.1`. Keys go in `.env`. Nothing is uploaded by the app.
- **A team, not one bot.** Chief, Coder, Researcher (or whoever you add) each have an allowlist. Coder cannot fetch the web unless you give them `http_fetch`. Researcher cannot write Coder's files.
- **Real chats.** A message to Coder does not appear in Researcher's inbox. Collaboration is handoff or a group you create.
- **A harness.** Tool loops can run for many rounds, continue, and stop. Other chats stay usable. You can schedule follow-ups. Each dialog can pick its own model.

It is not a drop-in clone of any cloud “AI coworker” product. Isolation is a directory jail, not containers. You bring an OpenAI-compatible model that supports tool calls.

## Features

| Area | What you get |
|---|---|
| Team | Add / edit / delete teammates in the UI. Changes write `mesh.yaml`. |
| Chats | One private thread per teammate. `+` → **New group** to pull people in. |
| Vault | Per-agent tools. File/`shell` jailed to `workspaces/<id>/`. `http_fetch` blocks private networks. |
| Harness | Long tool jobs, auto-continue, **Stop**, per-chat busy (not a global lock). |
| Models | Header picker per chat (`gpt-4o`, `deepseek-chat`, `qwen2.5`, …). |
| Schedules | Settings, or `schedule_task` (interval, 5-field cron, or one-shot `at`). |
| Files | Composer `+` → upload (max 10 MB) or write a markdown doc. Stays in that chat. |
| Settings | Bottom-left: API key, base URL, model, theme (light default), language (English default). |

## Install

Python 3.11+.

```bash
git clone https://github.com/kirincolor/openmesh.git
cd openmesh
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -e .
copy .env.example .env          # then put your key in .env
openmesh serve
```

Empty folder:

```bash
openmesh init my-house
cd my-house
copy .env.example .env
openmesh serve
```

Open [http://127.0.0.1:8787](http://127.0.0.1:8787). You can also paste the key in **Settings**; it only writes local `.env`.

## Providers

Any OpenAI-compatible Chat Completions endpoint. The model must support **tool calls** or handoff will not work.

| Provider | `OPENMESH_BASE_URL` | example model |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Ollama (local) | `http://127.0.0.1:11434/v1` | `qwen2.5` |

Ollama still wants a dummy `OPENMESH_API_KEY` (any string). Switch the **chat** model in the header; the Settings model is the default for new threads.

## How to use

1. Save an API key (Settings or `.env`).
2. Click a teammate. That is a private chat. Type a job and send.
3. Use `@id` in a **group** to talk to one person; with no `@`, everyone in the group can reply.
4. `+` in the composer: upload a file, write a document, or mention someone in this chat.
5. Sidebar `+`: new teammate or new group (at least two teammates).
6. Long job: watch tool cards; **Stop** cancels that chat only.
7. Settings → **Schedules** for a repeating or one-shot ping in the current chat.

Examples:

- Open Coder: “Write `hello.py` that prints openmesh.”
- Open Researcher: look something up — that thread is not Coder’s.
- New group with both, then `@coder` to implement what Researcher found.

## Default team

| id | job | tools (default) |
|---|---|---|
| `chief` | talk to you, split work, schedules | handoff, memory, inbox, docs, schedule |
| `coder` | write files in their workspace | handoff, files, inbox, docs, memory |
| `researcher` | look things up | handoff, `http_fetch`, inbox, docs, memory |

`shell` exists but is off until you add it to an agent's tool list.

## Tools

| tool | purpose |
|---|---|
| `handoff` | Give another teammate a concrete task |
| `memory_read` / `memory_write` | Personal notes, or `shared` |
| `fs_list` / `fs_read` / `fs_write` | Files in that agent's workspace |
| `inbox_list` / `inbox_read` | Files and docs attached to **this** chat |
| `doc_write` | Write a markdown document into this chat |
| `schedule_task` / `list_schedule` / `cancel_schedule` | Timed follow-ups |
| `http_fetch` | GET a public URL (no localhost / private IPs) |
| `shell` | Command in the agent's workspace only |

The vault denies anything not on the agent's list. Keys never go into prompts, tool results, or the browser after save.

## Layout

```
mesh.yaml                 team + vault (UI writes this)
.env                      keys (gitignored)
src/openmesh/             server, harness, vault
workspaces/<agent>/       per-agent disk jail
data/room.jsonl           messages (per chat thread)
data/chats.json           groups
data/files/               uploads and documents per chat
data/work.json            jobs, schedules, per-chat models
data/ui.json              theme + language
data/memory/              markdown notes
```

## Develop

```bash
pip install -e ".[dev]"
pytest
```

MIT. See `LICENSE`.
