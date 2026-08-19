from __future__ import annotations

import asyncio
from typing import Any

from .bus import Bus, Event
from .chats import Chat, ChatDirectory, dm_id
from .files import FileStore
from .harness import Harness
from .jobs import WorkStore
from .config import AgentConfig, MeshConfig
from .llm import LLM, LLMError
from .memory import Memory
from .prefs import load_prefs
from .tools import Toolbelt
from .vault import ALL_TOOLS, Vault

MAX_HISTORY = 48
MAX_HANDOFF_DEPTH = 4
CONTEXT_KINDS = {"user", "agent", "system", "tool", "handoff", "file"}


class Mesh:
    def __init__(self, config: MeshConfig) -> None:
        self.config = config
        self.bus = Bus(config.data_dir() / "room.jsonl")
        self.chats = ChatDirectory(config.root)
        self.files = FileStore(config.root)
        self.work = WorkStore(config.root)
        self.vault = Vault(config)
        self.memory = Memory(config)
        self.tools = Toolbelt(self.vault, self.memory, self.files, self.work)
        self.llm = LLM(config.provider)
        self.harness = Harness(self.llm, self.tools)
        self.locks: dict[str, asyncio.Lock] = {}
        self.busy: set[str] = set()
        self.running = False
        self._tick_lock = asyncio.Lock()

    def snapshot(self) -> dict[str, Any]:
        return {
            "mesh": self.config.mesh.model_dump(),
            "running": self.running,
            "provider": {
                "base_url": self.config.provider.base_url,
                "model": self.config.provider.model,
                "has_key": bool(self.config.provider.api_key),
            },
            "prefs": load_prefs(self.config.root).model_dump(),
            "tools": sorted(ALL_TOOLS),
            "agents": [
                {
                    **agent.model_dump(),
                    "workspace": str(self.vault.workspace(agent).relative_to(self.config.root)),
                    "busy": agent.id in self.busy,
                }
                for agent in self.config.agents
            ],
            "chats": [self._chat_payload(chat) for chat in self._sorted_chats()],
            "events": [event.model_dump() for event in self.bus.events[-400:]],
            "busy_threads": self.work.active_threads(),
            "jobs": [item.model_dump() for item in self.work.runs[-20:]],
            "schedules": [item.model_dump() for item in self.work.schedules],
            "models": {
                "default": self.config.provider.model,
                "options": self.work.model_options(self.config.provider.model),
                "by_chat": dict(self.work.chat_models),
            },
        }

    def _sorted_chats(self) -> list[Chat]:
        chats = self.chats.all_chats(self.config)
        return sorted(chats, key=lambda chat: (-self._thread_preview(chat.id)["preview_ts"], chat.title.lower()))

    def _chat_payload(self, chat: Chat) -> dict[str, Any]:
        return {**chat.model_dump(), **self._thread_preview(chat.id)}

    def _thread_preview(self, thread: str) -> dict[str, Any]:
        for event in reversed(self.bus.events):
            if event.thread == thread and event.kind in {"user", "agent", "handoff", "file"}:
                return {"preview": (event.text or "")[:120], "preview_ts": event.ts}
        return {"preview": "", "preview_ts": 0}

    def resolve_thread(self, thread: str | None, to: str | None) -> str:
        if thread and thread != "main":
            if self.chats.get(thread, self.config) is None:
                raise ValueError(f"unknown chat: {thread}")
            return thread
        if to and any(agent.id == to for agent in self.config.agents):
            return dm_id(to)
        return dm_id(self.config.mesh.chief)

    def clear_room(self) -> None:
        self.bus.clear()

    def clear_chat(self, thread: str) -> None:
        self.bus.clear_thread(thread)

    def _lock_for(self, thread: str) -> asyncio.Lock:
        lock = self.locks.get(thread)
        if lock is None:
            lock = asyncio.Lock()
            self.locks[thread] = lock
        return lock

    def thread_busy(self, thread: str) -> bool:
        return self.work.thread_busy(thread)

    def cancel_thread(self, thread: str) -> list[str]:
        return self.work.cancel_thread(thread)

    def set_chat_model(self, thread: str, model: str) -> str:
        return self.work.set_chat_model(thread, model)

    async def user_say(
        self,
        text: str,
        thread: str = "main",
        to: str | None = None,
        model: str | None = None,
        sender: str = "you",
    ) -> Event:
        text = text.strip()
        if not text:
            raise ValueError("empty message")
        thread = self.resolve_thread(thread, to)
        if model:
            self.work.set_chat_model(thread, model)
        event = Event(kind="user", sender=sender, text=text, thread=thread)
        lock = self._lock_for(thread)
        async with lock:
            if self.work.thread_busy(thread):
                raise RuntimeError("this chat is busy")
            self.running = True
            run = self.work.start_run(
                thread,
                text,
                self.work.model_for(thread, self.config.provider.model),
            )
            try:
                await self.bus.publish(event)
                targets = self._route(text, prefer=to, thread=thread)
                await self.bus.publish(
                    Event(
                        kind="status",
                        sender="mesh",
                        text="routing",
                        thread=thread,
                        meta={"targets": targets, "model": run.model, "job": run.id},
                    )
                )
                for agent_id in targets:
                    await self._run_agent(agent_id, thread, depth=0, run_id=run.id, model=run.model)
                self.work.finish_run(run, "cancelled" if self.work.is_cancelled(run.id) else "done")
            except Exception as exc:
                self.work.finish_run(run, "error", error=str(exc))
                raise
            finally:
                self.running = bool(self.work.active_threads())
        return event

    async def tick_schedules(self) -> int:
        async with self._tick_lock:
            due = self.work.due()
            fired = 0
            for item in due:
                if self.work.thread_busy(item.thread):
                    continue
                if self.chats.get(item.thread, self.config) is None:
                    continue
                self.work.mark_fired(item)
                await self.bus.publish(
                    Event(
                        kind="system",
                        sender="mesh",
                        text=f"Scheduled: {item.title}",
                        thread=item.thread,
                        meta={"schedule": item.id},
                    )
                )
                await self.user_say(item.text, thread=item.thread, sender="schedule")
                fired += 1
            return fired

    def _mentions(self, text: str) -> list[str]:
        found: list[str] = []
        lowered = text.lower()
        for agent in self.config.agents:
            token = f"@{agent.id}".lower()
            if token in lowered or f"@{agent.name.lower()}" in lowered:
                found.append(agent.id)
        return found

    def _route(self, text: str, prefer: str | None = None, thread: str | None = None) -> list[str]:
        chat = self.chats.get(thread, self.config) if thread else None
        mentions = self._mentions(text)
        if chat and chat.kind == "dm":
            return list(chat.members)
        if chat and chat.kind == "group":
            members = [item for item in chat.members if any(agent.id == item for agent in self.config.agents)]
            named = [item for item in mentions if item in members]
            if named:
                return named
            if prefer and prefer in members:
                return [prefer]
            return members
        if mentions:
            return mentions
        if prefer and any(agent.id == prefer for agent in self.config.agents):
            return [prefer]
        return [self.config.mesh.chief]

    async def _run_agent(
        self,
        agent_id: str,
        thread: str,
        depth: int,
        run_id: str | None = None,
        model: str | None = None,
    ) -> None:
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
        chosen = model or self.work.model_for(thread, agent.model or self.config.provider.model)
        self.busy.add(agent.id)
        await self.bus.publish(
            Event(kind="status", sender=agent.id, text="thinking", thread=thread, meta={"model": chosen})
        )
        queue: asyncio.Queue[Event] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def emit(event: Event) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, event)

        async def drain() -> None:
            while True:
                event = await queue.get()
                if event.kind == "status" and event.text == "__done__":
                    return
                await self.bus.publish(event)

        drain_task = asyncio.create_task(drain())
        try:
            result = await asyncio.to_thread(
                self.harness.run,
                agent,
                self._prompt(agent, thread),
                thread,
                chosen,
                emit=emit,
                should_stop=(lambda: bool(run_id and self.work.is_cancelled(run_id))),
            )
            handoffs = result.handoffs
        except LLMError as exc:
            handoffs = []
            await self.bus.publish(Event(kind="error", sender=agent.id, text=str(exc), thread=thread))
        except Exception as exc:  # noqa: BLE001 — surface unexpected tool/runtime faults
            handoffs = []
            await self.bus.publish(
                Event(
                    kind="error",
                    sender=agent.id,
                    text=f"{type(exc).__name__}: {exc}",
                    thread=thread,
                )
            )
        emit(Event(kind="status", sender="mesh", text="__done__", thread=thread))
        await drain_task
        self.busy.discard(agent.id)
        await self.bus.publish(
            Event(kind="status", sender=agent.id, text="idle", thread=thread)
        )
        if run_id and self.work.is_cancelled(run_id):
            return
        for target, task in handoffs:
            chat = self.chats.get(thread, self.config)
            if chat and chat.kind == "group" and target not in chat.members:
                await self.bus.publish(
                    Event(
                        kind="system",
                        sender="mesh",
                        text=f"{agent.id} asked {target}, who is not in this group. Add them first.",
                        thread=thread,
                    )
                )
                continue
            await self.bus.publish(
                Event(
                    kind="handoff",
                    sender=agent.id,
                    to=target,
                    text=task,
                    thread=thread,
                )
            )
            await self._run_agent(target, thread, depth + 1, run_id=run_id, model=model)

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
        chat = self.chats.get(thread, self.config)
        if chat and chat.kind == "dm":
            place = (
                f"You are in a private 1:1 chat with the human. "
                f"Other teammates cannot see this conversation. "
                f"If you need help, hand off a concrete task. Their help stays in this chat "
                f"and is not copied into their own inbox."
            )
        elif chat and chat.kind == "group":
            names = ", ".join(chat.members)
            place = (
                f"You are in the group chat \"{chat.title}\" with: {names}. "
                f"Everyone in this group can see these messages. "
                f"Reply when you have something useful; do not speak for others. "
                f"Only hand off to people already in this group."
            )
        else:
            place = "Talk to the human. Keep answers short."
        attachments = self.files.list_thread(thread)
        inbox = "\n".join(
            f"- {item.id} {item.name} ({item.size} bytes, {item.kind})" for item in attachments
        ) or "(none)"
        system = f"""You are {agent.name} ({agent.id}) on a local Mesh named {self.config.mesh.name}.
{agent.role.strip()}

{place}

Rules:
- You are one teammate, not the whole team. Stay in your job.
- Use only your tools. The vault will block anything else.
- Keep answers short.
- Do not claim you used a tool you did not use.
- File tools only see your workspace.
- Chat attachments are listed below. Use inbox_list / inbox_read to open them.
- Use doc_write to put a markdown document into this chat for the human to download.
- Long jobs are OK. Keep using tools until the work is done. The harness will continue you if you hit a round limit.
- Use schedule_task for reminders or repeating work. cron is 5 fields (m h dom mon dow).

Teammates:
{chr(10).join(roster)}

Attachments in this chat:
{inbox}

Shared memory:
{shared or "(empty)"}

Your memory:
{own or "(empty)"}
"""
        return [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": "Chat log (oldest first):\n" + "\n".join(lines),
            },
        ]
