from __future__ import annotations

import re
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .config import AgentConfig, MeshConfig
from .vault import ALL_TOOLS

ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
RESERVED_IDS = {"you", "mesh", "system"}
FILE_TOOLS = {"fs_list", "fs_read", "fs_write", "shell"}
PALETTE = ("#5B8DEF", "#F5A14A", "#3DDC97", "#7C9CFF", "#E86B6B", "#C77DFF")
PROVIDER_PLACEHOLDERS = {
    "base_url": "${OPENMESH_BASE_URL}",
    "api_key": "${OPENMESH_API_KEY}",
    "model": "${OPENMESH_MODEL}",
}


class TeamError(ValueError):
    pass


class AgentIn(BaseModel):
    id: str | None = None
    name: str
    role: str = ""
    color: str | None = None
    tools: list[str] = Field(default_factory=list)
    workspace: str | None = None


def slug_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    slug = slug[:32] or "agent"
    if not slug[0].isalpha():
        slug = f"a-{slug}"[:32]
    return slug


def unique_id(config: MeshConfig, base: str) -> str:
    if all(agent.id != base for agent in config.agents):
        return base
    index = 2
    while any(agent.id == f"{base}-{index}" for agent in config.agents):
        index += 1
    return f"{base}-{index}"


def validate_id(agent_id: str) -> str:
    agent_id = (agent_id or "").strip().lower()
    if not ID_RE.match(agent_id):
        raise TeamError("id must be 1-32 chars: start with a letter, then a-z, 0-9, _ or -")
    if agent_id in RESERVED_IDS:
        raise TeamError(f"id '{agent_id}' is reserved")
    return agent_id


def validate_tools(tools: list[str]) -> list[str]:
    unknown = sorted(set(tools) - ALL_TOOLS)
    if unknown:
        raise TeamError(f"unknown tools: {', '.join(unknown)}")
    seen: list[str] = []
    for tool in tools:
        if tool not in seen:
            seen.append(tool)
    return seen


def validate_color(color: str | None, fallback: str) -> str:
    value = (color or fallback).strip()
    if not COLOR_RE.match(value):
        raise TeamError("color must be a hex value like #5B8DEF")
    return value.upper() if value.startswith("#") else value


def next_color(config: MeshConfig) -> str:
    used = {agent.color.upper() for agent in config.agents}
    for color in PALETTE:
        if color.upper() not in used:
            return color
    return PALETTE[len(config.agents) % len(PALETTE)]


def default_workspace(agent_id: str, tools: list[str], workspace: str | None) -> str | None:
    if workspace:
        rel = workspace.replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            raise TeamError("workspace cannot contain '..'")
        return rel
    if FILE_TOOLS & set(tools):
        return f"workspaces/{agent_id}"
    return None


def _to_yaml_agent(agent: AgentConfig) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": agent.id,
        "name": agent.name,
        "color": agent.color,
        "role": agent.role.strip(),
        "tools": list(agent.tools),
    }
    if agent.workspace:
        item["workspace"] = agent.workspace
    if agent.model:
        item["model"] = agent.model
    return item


def _safe_provider(current: dict[str, Any]) -> dict[str, str]:
    raw = dict(current.get("provider") or {})
    out: dict[str, str] = {}
    for key, placeholder in PROVIDER_PLACEHOLDERS.items():
        value = str(raw.get(key) or "")
        out[key] = value if value.startswith("${") else placeholder
    return out


def save_team(config: MeshConfig) -> None:
    path = config.root / "mesh.yaml"
    current: dict[str, Any] = {}
    if path.exists():
        current = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    payload = {
        "mesh": config.mesh.model_dump(),
        "provider": _safe_provider(current),
        "agents": [_to_yaml_agent(agent) for agent in config.agents],
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def add_agent(config: MeshConfig, body: AgentIn) -> AgentConfig:
    name = body.name.strip()
    if not name:
        raise TeamError("name is required")
    agent_id = validate_id(body.id) if body.id else unique_id(config, slug_id(name))
    if any(agent.id == agent_id for agent in config.agents):
        raise TeamError(f"teammate '{agent_id}' already exists")
    tools = validate_tools(body.tools)
    agent = AgentConfig(
        id=agent_id,
        name=name,
        role=body.role.strip() or "A teammate on this mesh.",
        color=validate_color(body.color, next_color(config)),
        tools=tools,
        workspace=default_workspace(agent_id, tools, body.workspace),
    )
    config.agents.append(agent)
    save_team(config)
    return agent


def update_agent(config: MeshConfig, agent_id: str, body: AgentIn) -> AgentConfig:
    current = config.agent(agent_id)
    name = body.name.strip()
    if not name:
        raise TeamError("name is required")
    new_id = validate_id(body.id) if body.id else current.id
    if new_id != current.id and any(agent.id == new_id for agent in config.agents):
        raise TeamError(f"teammate '{new_id}' already exists")
    tools = validate_tools(body.tools)
    current.id = new_id
    current.name = name
    current.role = body.role.strip() or current.role
    current.color = validate_color(body.color, current.color)
    current.tools = tools
    current.workspace = default_workspace(new_id, tools, body.workspace or current.workspace)
    if config.mesh.chief == agent_id:
        config.mesh.chief = new_id
    save_team(config)
    return current


def remove_agent(config: MeshConfig, agent_id: str) -> None:
    if all(agent.id != agent_id for agent in config.agents):
        raise KeyError(agent_id)
    if len(config.agents) <= 1:
        raise TeamError("cannot delete the last teammate")
    config.agents = [agent for agent in config.agents if agent.id != agent_id]
    if config.mesh.chief == agent_id:
        config.mesh.chief = config.agents[0].id
    save_team(config)
