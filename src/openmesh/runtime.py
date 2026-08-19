from __future__ import annotations

import asyncio
import json
from typing import Any

from .bus import Bus, Event
from .config import AgentConfig, MeshConfig
from .llm import LLM, LLMError
from .memory import Memory
from .tools import Toolbelt
from .vault import Vault, VaultDenied

MAX_HISTORY = 36
MAX_TOOL_ROUNDS = 6
MAX_HANDOFF_DEPTH = 4
CONTEXT_KINDS = {"user", "agent", "system", "tool", "handoff"}


class Mesh:
    def __init__(self, config: MeshConfig) -> None:
        self.config = config
        self.bus = Bus(config.data_dir() / "room.jsonl")
        self.vault = Vault(config)
        self.memory = Memory(config)
        self.tools = Toolbelt(self.vault, self.memory)
        self.llm = LLM(config.provider)
        self.lock = asyncio.Lock()
        self.busy: set[str] = set()
        self.running = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "mesh": self.config.mesh.model_dump(),
            "running": self.running,
            "provider": {
                "base_url": self.config.provider.base_url,
                "model": self.config.provider.model,
                "has_key": bool(self.config.provider.api_key),
            },
            "agents": [
                {
                    **agent.model_dump(),
                    "workspace": str(self.vault.workspace(agent).relative_to(self.config.root)),
                    "busy": agent.id in self.busy,
                }
                for agent in self.config.agents
            ],
            "events": [event.model_dump() for event in self.bus.events[-200:]],
        }

    def clear_room(self) -> None:
        self.bus.clear()

    async def user_say(self, text: str, thread: str = "main") -> Event:
        text = text.strip()
        if not text:
            raise ValueError("empty message")
        event = Event(kind="user", sender="you", text=text, thread=thread)
        async with self.lock:
            if self.running:
                raise RuntimeError("mesh is busy")
            self.running = True
            try:
                await self.bus.publish(event)
                targets = self._route(text)
                await self.bus.publish(
                    Event(
                        kind="status",
                        sender="mesh",
                        text="routing",
                        thread=thread,
                        meta={"targets": targets},
                    )
                )
                for agent_id in targets:
                    await self._run_agent(agent_id, thread, depth=0)
            finally:
                self.running = False
        return event

    def _route(self, text: str) -> list[str]:
        found: list[str] = []
        lowered = text.lower()
        for agent in self.config.agents:
            token = f"@{agent.id}".lower()
            if token in lowered or f"@{agent.name.lower()}" in lowered:
                found.append(agent.id)
        if found:
            return found
        return [self.config.mesh.chief]

    async def _run_agent(self, agent_id: str, thread: str, depth: int) -> None:
        if depth > MAX_HANDOFF_DEPTH:
            await self.bus.publish(
                Event(
                    kind="error",
                    sender="mesh",
                    text=f"handoff depth exceeded, dropped work for {agent_id}",
                    thread=thread,
                )
            )
            return
        agent = self.config.agent(agent_id)
        self.busy.add(agent.id)
        await self.bus.publish(
            Event(kind="status", sender=agent.id, text="thinking", thread=thread)
        )
        try:
            traces, handoffs = await asyncio.to_thread(self._turn, agent, thread)
        except LLMError as exc:
            traces, handoffs = (
                [Event(kind="error", sender=agent.id, text=str(exc), thread=thread)],
                [],
            )
        except Exception as exc:  # noqa: BLE001 — surface unexpected tool/runtime faults
            traces, handoffs = (
                [
                    Event(
                        kind="error",
                        sender=agent.id,
                        text=f"{type(exc).__name__}: {exc}",
                        thread=thread,
                    )
                ],
                [],
            )
        for item in traces:
            await self.bus.publish(item)
        self.busy.discard(agent.id)
        await self.bus.publish(
            Event(kind="status", sender=agent.id, text="idle", thread=thread)
        )
        for target, task in handoffs:
            await self.bus.publish(
                Event(
                    kind="handoff",
                    sender=agent.id,
                    to=target,
                    text=task,
                    thread=thread,
                )
            )
            await self._run_agent(target, thread, depth + 1)

    def _turn(self, agent: AgentConfig, thread: str) -> tuple[list[Event], list[tuple[str, str]]]:
        messages = self._prompt(agent, thread)
        tools = self.tools.openai_tools(agent)
        handoffs: list[tuple[str, str]] = []
        traces: list[Event] = []
        final = ""
        for _ in range(MAX_TOOL_ROUNDS):
            message = self.llm.complete(messages, tools=tools or None, model=agent.model)
            tool_calls = message.get("tool_calls") or []
            content = (message.get("content") or "").strip()
            if content:
                final = content
            messages.append(message)
            if not tool_calls:
                break
            for call in tool_calls:
                fn = call.get("function") or {}
                name = fn.get("name") or ""
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                except json.JSONDecodeError:
                    args = {}
                    result = f"invalid tool arguments: {raw_args}"
                else:
                    try:
                        result = self.tools.run(agent, name, args)
                    except VaultDenied as exc:
                        result = f"vault denied: {exc}"
                if result.startswith("HANDOFF::"):
                    _, target, task = result.split("::", 2)
                    handoffs.append((target, task))
                    result = f"handed off to {target}"
                traces.append(
                    Event(
                        kind="tool",
                        sender=agent.id,
                        text=f"{name} → {result[:400]}",
                        thread=thread,
                        meta={"tool": name, "args": args},
                    )
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id") or name,
                        "content": result,
                    }
                )
        if final:
            traces.append(Event(kind="agent", sender=agent.id, text=final, thread=thread))
        elif handoffs:
            traces.append(
                Event(
                    kind="agent",
                    sender=agent.id,
                    text="Handed off: " + ", ".join(f"{t}" for t, _ in handoffs),
                    thread=thread,
                )
            )
        return traces, handoffs

    def _prompt(self, agent: AgentConfig, thread: str) -> list[dict[str, Any]]:
        roster = []
        for mate in self.config.agents:
            roster.append(
                f"- {mate.id} ({mate.name}): tools={','.join(mate.tools) or 'none'}"
            )
        shared = self.memory.read("shared")
        own = self.memory.read(agent.id)
        history = [
            e
            for e in self.bus.events
            if e.thread == thread and e.kind in CONTEXT_KINDS
        ]
        lines = []
        for event in history[-MAX_HISTORY:]:
            dest = f" → {event.to}" if event.to else ""
            lines.append(f"[{event.kind}] {event.sender}{dest}: {event.text}")
        system = f"""You are {agent.name} ({agent.id}) on a local Mesh named {self.config.mesh.name}.
{agent.role.strip()}

Rules:
- You are one teammate, not the whole team. Stay in your job.
- Use only your tools. The vault will block anything else.
- Talk to the human in the room. Keep answers short.
- Use handoff for work that belongs to someone else. Give them a concrete task.
- Do not claim you used a tool you did not use.
- File tools only see your workspace.

Teammates:
{chr(10).join(roster)}

Shared memory:
{shared or "(empty)"}

Your memory:
{own or "(empty)"}
"""
        return [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": "Room log (oldest first):\n" + "\n".join(lines),
            },
        ]
