# OpenMesh

Local multi-agent **Mesh**: your API key, a group chat, teammates with **split permissions**.

Grok Bot already showed the UX — a room of named coworkers who hand work to each other. OpenMesh is the open, local version. The computer is yours. Keys stay in `.env`. Coder cannot fetch the web. Researcher cannot write the coder's files.

```
you ──► chief ──handoff──► coder | researcher
              ▲                    │
              └──── posts back ────┘
```

## Install

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

New folder:

```bash
openmesh init my-house
cd my-house
copy .env.example .env
openmesh serve
```

Open [http://127.0.0.1:8787](http://127.0.0.1:8787). Bottom-left **Settings** writes the key to local `.env` only. Theme defaults to light; language defaults to English.

Any OpenAI-compatible endpoint works:

| Provider | `OPENMESH_BASE_URL` | example model |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Ollama (local) | `http://127.0.0.1:11434/v1` | `qwen2.5` |

Ollama still wants a dummy `OPENMESH_API_KEY` (any string). The model must support tool calls for handoff to work.

## Vault

The left list is the team. Add, edit, or delete teammates in the page; OpenMesh writes `mesh.yaml` for you. You can still edit that file by hand. It is the team and the lock.

- Each agent lists the tools it may use. Anything else is denied.
- File tools and `shell` are jailed to that agent's `workspace/`.
- Personal memory is private. Only `shared` is a common notebook.
- `http_fetch` refuses localhost and private addresses, including redirects.
- The API key never goes into prompts, tool results, or the browser after save.
- The room log is stored in `data/room.jsonl` and comes back after restart.

Default house:

| id | job | can touch |
|---|---|---|
| `chief` | talk to you, split work | handoff, memory |
| `coder` | write files | files in `workspaces/coder`, handoff |
| `researcher` | look things up | `http_fetch`, handoff |

`shell` exists but is off unless you add it to an agent's `tools` list.

Click a teammate to talk to them. Mention someone with `@coder` to skip the selected person. Otherwise the selected teammate (or chief) routes.

## Talk to the room

- “Write hello.py that prints openmesh”
- “@researcher look up DeepSeek's OpenAI-compatible URL, then hand it to coder as a README snippet”
- Click a teammate, or use `+` in the composer to insert `@id`

## Layout

```
mesh.yaml                 team + vault
.env                      keys (gitignored)
src/openmesh/             runtime
workspaces/<agent>/       per-agent disk jail
data/room.jsonl           persisted room
data/ui.json              theme + language
data/memory/              markdown notes
```

## Develop

```bash
pip install -e ".[dev]"
pytest
```

MIT. See `LICENSE`.
