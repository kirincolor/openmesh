from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

Listener = Callable[["Event"], Awaitable[None] | None]
PERSIST_KINDS = {"user", "agent", "system", "tool", "handoff", "error", "file"}


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: float = Field(default_factory=time.time)
    thread: str = "main"
    kind: Literal[
        "user",
        "agent",
        "system",
        "tool",
        "handoff",
        "error",
        "status",
        "file",
    ] = "system"
    sender: str
    to: str | None = None
    text: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)


class Bus:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[Event] = []
        self._listeners: list[Listener] = []
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        self.events.append(Event.model_validate_json(line))

    def on(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def off(self, listener: Listener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def clear(self) -> None:
        self.events.clear()
        self._rewrite()

    def clear_thread(self, thread: str) -> None:
        self.events = [event for event in self.events if event.thread != thread]
        self._rewrite()

    def _rewrite(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [event.model_dump_json() for event in self.events if event.kind in PERSIST_KINDS]
        self.path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")

    async def publish(self, event: Event) -> Event:
        self.events.append(event)
        if self.path and event.kind in PERSIST_KINDS:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(event.model_dump_json() + "\n")
        for listener in list(self._listeners):
            result = listener(event)
            if asyncio.iscoroutine(result):
                await result
        return event
