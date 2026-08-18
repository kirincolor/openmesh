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
git clone https://github.com/<you>/openmesh.git
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

Open [http://127.0.0.1:8787](http://127.0.0.1:8787). The sidebar also writes the key to local `.env` only.

Any OpenAI-compatible endpoint works:

| Provider | `OPENMESH_BASE_URL` | example model |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Ollama (local) | `http://127.0.0.1:11434/v1` | `qwen2.5` |

Ollama still wants a dummy `OPENMESH_API_KEY` (any string). The model must support tool calls for handoff to work.

## Vault

`mesh.yaml` is the team and the lock.

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

Mention someone with `@coder` to skip the chief. Otherwise chief routes.

## Talk to the room

- “写一个 hello.py，打印 openmesh”
- “@researcher 查一下 DeepSeek 的 OpenAI 兼容地址，然后交给 coder 写成 README 片段”
- Click a teammate in the left rail to insert `@id`

## Layout

```
mesh.yaml                 team + vault
.env                      keys (gitignored)
src/openmesh/             runtime
workspaces/<agent>/       per-agent disk jail
data/room.jsonl           persisted room
data/memory/              markdown notes
```

## Develop

```bash
pip install -e ".[dev]"
pytest
```

MIT. See `LICENSE`.
