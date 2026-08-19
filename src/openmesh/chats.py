from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .config import MeshConfig


class ChatError(ValueError):
    pass


class Chat(BaseModel):
    id: str
    kind: Literal["dm", "group"]
    title: str = ""
    members: list[str] = Field(default_factory=list)
    created_ts: float = Field(default_factory=time.time)


class GroupIn(BaseModel):
    title: str = ""
    members: list[str] = Field(default_factory=list)


def dm_id(agent_id: str) -> str:
    return f"dm:{agent_id}"


def chats_path(root: Path) -> Path:
    return root / "data" / "chats.json"


class ChatDirectory:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = chats_path(root)
        self.groups: list[Chat] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.groups = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.groups = []
            return
        self.groups = [Chat.model_validate(item) for item in raw.get("groups") or []]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"groups": [chat.model_dump() for chat in self.groups]}
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def dms(self, config: MeshConfig) -> list[Chat]:
        return [
            Chat(id=dm_id(agent.id), kind="dm", title=agent.name, members=[agent.id])
            for agent in config.agents
        ]

    def all_chats(self, config: MeshConfig) -> list[Chat]:
        return [*self.dms(config), *self.groups]

    def get(self, chat_id: str, config: MeshConfig | None = None) -> Chat | None:
        if chat_id.startswith("dm:") and config is not None:
            agent_id = chat_id[3:]
            try:
                agent = config.agent(agent_id)
            except KeyError:
                return None
            return Chat(id=chat_id, kind="dm", title=agent.name, members=[agent.id])
        for chat in self.groups:
            if chat.id == chat_id:
                return chat
        return None

    def _clean_members(self, config: MeshConfig, members: list[str]) -> list[str]:
        seen: list[str] = []
        for item in members:
            agent_id = item.strip()
            if not agent_id or agent_id in seen:
                continue
            try:
                config.agent(agent_id)
            except KeyError as exc:
                raise ChatError(f"unknown teammate: {agent_id}") from exc
            seen.append(agent_id)
        if len(seen) < 2:
            raise ChatError("a group needs at least two teammates")
        return seen

    def create_group(self, config: MeshConfig, body: GroupIn) -> Chat:
        members = self._clean_members(config, body.members)
        names = [config.agent(item).name for item in members]
        title = body.title.strip() or ", ".join(names[:3])
        chat = Chat(id=f"grp:{uuid.uuid4().hex[:8]}", kind="group", title=title, members=members)
        self.groups.append(chat)
        self.save()
        return chat

    def update_group(self, config: MeshConfig, chat_id: str, body: GroupIn) -> Chat:
        chat = self.get(chat_id)
        if chat is None or chat.kind != "group":
            raise KeyError(chat_id)
        chat.members = self._clean_members(config, body.members)
        names = [config.agent(item).name for item in chat.members]
        chat.title = body.title.strip() or ", ".join(names[:3])
        self.save()
        return chat

    def delete_group(self, chat_id: str) -> None:
        before = len(self.groups)
        self.groups = [chat for chat in self.groups if chat.id != chat_id]
        if len(self.groups) == before:
            raise KeyError(chat_id)
        self.save()

    def drop_agent(self, agent_id: str) -> None:
        kept: list[Chat] = []
        for chat in self.groups:
            chat.members = [item for item in chat.members if item != agent_id]
            if len(chat.members) >= 2:
                kept.append(chat)
        self.groups = kept
        self.save()
