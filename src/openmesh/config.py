from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            return os.environ.get(match.group(1), "")

        return ENV_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


class ProviderConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"


class AgentConfig(BaseModel):
    id: str
    name: str
    role: str
    color: str = "#8B93A7"
    tools: list[str] = Field(default_factory=list)
    workspace: str | None = None
    model: str | None = None


class MeshMeta(BaseModel):
    name: str = "home"
    chief: str = "chief"


class MeshConfig(BaseModel):
    root: Path
    mesh: MeshMeta
    provider: ProviderConfig
    agents: list[AgentConfig]

    def agent(self, agent_id: str) -> AgentConfig:
        for item in self.agents:
            if item.id == agent_id:
                return item
        raise KeyError(agent_id)

    def data_dir(self) -> Path:
        path = self.root / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path


def find_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "mesh.yaml").exists():
            return candidate
    return here


def load_config(root: Path | None = None) -> MeshConfig:
    root = root or find_root()
    load_dotenv(root / ".env", override=False)
    raw_path = root / "mesh.yaml"
    if not raw_path.exists():
        raise FileNotFoundError(f"mesh.yaml not found under {root}")
    raw = _expand(yaml.safe_load(raw_path.read_text(encoding="utf-8")) or {})
    config = MeshConfig(
        root=root,
        mesh=MeshMeta.model_validate(raw.get("mesh") or {}),
        provider=ProviderConfig.model_validate(raw.get("provider") or {}),
        agents=[AgentConfig.model_validate(item) for item in raw.get("agents") or []],
    )
    if not config.provider.api_key:
        config.provider.api_key = os.environ.get("OPENMESH_API_KEY", "")
    if not config.provider.base_url:
        config.provider.base_url = os.environ.get("OPENMESH_BASE_URL") or "https://api.openai.com/v1"
    if not config.provider.model:
        config.provider.model = os.environ.get("OPENMESH_MODEL") or "gpt-4o-mini"
    return config
