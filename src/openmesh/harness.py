from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .bus import Event
from .config import AgentConfig
from .llm import LLM
from .tools import Toolbelt
from .vault import VaultDenied

DEFAULT_ROUNDS = 32
DEFAULT_SECONDS = 600
DEFAULT_CONTINUES = 2


@dataclass
class TurnResult:
    traces: list[Event] = field(default_factory=list)
    handoffs: list[tuple[str, str]] = field(default_factory=list)
    rounds: int = 0
    stopped: bool = False
    timed_out: bool = False
    final: str = ""


class Harness:
    """Tool-calling loop for long jobs: budgets, continue, cancel."""

    def __init__(
        self,
        llm: LLM,
        tools: Toolbelt,
        *,
        max_rounds: int = DEFAULT_ROUNDS,
        max_seconds: float = DEFAULT_SECONDS,
        max_continues: int = DEFAULT_CONTINUES,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_rounds = max_rounds
        self.max_seconds = max_seconds
        self.max_continues = max_continues

    def run(
        self,
        agent: AgentConfig,
        messages: list[dict[str, Any]],
        thread: str,
        model: str | None = None,
        *,
        emit: Callable[[Event], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> TurnResult:
        tools = self.tools.openai_tools(agent)
        result = TurnResult()
        started = time.monotonic()
        continues = 0

        def push(event: Event) -> None:
            result.traces.append(event)
            if emit:
                emit(event)

        while True:
            used_tools = False
            for _ in range(self.max_rounds):
                if should_stop and should_stop():
                    result.stopped = True
                    push(Event(kind="system", sender="mesh", text="Stopped.", thread=thread))
                    return result
                if time.monotonic() - started > self.max_seconds:
                    result.timed_out = True
                    push(
                        Event(
                            kind="system",
                            sender="mesh",
                            text="Time budget reached. Say continue to keep going.",
                            thread=thread,
                        )
                    )
                    return self._finish(result, thread, agent.id, emit)
                message = self.llm.complete(messages, tools=tools or None, model=model)
                tool_calls = message.get("tool_calls") or []
                content = (message.get("content") or "").strip()
                if content:
                    result.final = content
                messages.append(message)
                result.rounds += 1
                if not tool_calls:
                    used_tools = False
                    break
                used_tools = True
                for call in tool_calls:
                    if should_stop and should_stop():
                        result.stopped = True
                        push(Event(kind="system", sender="mesh", text="Stopped.", thread=thread))
                        return result
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""
                    raw_args = fn.get("arguments") or "{}"
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                    except json.JSONDecodeError:
                        args = {}
                        tool_result = f"invalid tool arguments: {raw_args}"
                    else:
                        try:
                            tool_result = self.tools.run(agent, name, args, thread=thread)
                        except VaultDenied as exc:
                            tool_result = f"vault denied: {exc}"
                    if tool_result.startswith("HANDOFF::"):
                        _, target, task = tool_result.split("::", 2)
                        result.handoffs.append((target, task))
                        tool_result = f"handed off to {target}"
                    if tool_result.startswith("FILE::"):
                        parts = tool_result.split("::", 3)
                        if len(parts) == 4:
                            _, file_id, filename, size = parts
                            push(
                                Event(
                                    kind="file",
                                    sender=agent.id,
                                    text=filename,
                                    thread=thread,
                                    meta={
                                        "file_id": file_id,
                                        "name": filename,
                                        "size": int(size or 0),
                                        "kind": "doc",
                                    },
                                )
                            )
                        tool_result = f"wrote document {parts[2] if len(parts) > 2 else ''}"
                    push(
                        Event(
                            kind="tool",
                            sender=agent.id,
                            text=f"{name} → {tool_result[:400]}",
                            thread=thread,
                            meta={"tool": name, "args": args, "round": result.rounds},
                        )
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id") or name,
                            "content": tool_result,
                        }
                    )
            else:
                if used_tools and continues < self.max_continues:
                    continues += 1
                    messages.append(
                        {
                            "role": "user",
                            "content": "Continue the same job. Use tools until it is finished. Do not restart from scratch.",
                        }
                    )
                    push(
                        Event(
                            kind="status",
                            sender=agent.id,
                            text=f"continuing ({continues})",
                            thread=thread,
                        )
                    )
                    continue
                if used_tools:
                    push(
                        Event(
                            kind="system",
                            sender="mesh",
                            text="Round budget reached. Say continue to keep going.",
                            thread=thread,
                        )
                    )
            break
        return self._finish(result, thread, agent.id, emit)

    def _finish(
        self,
        result: TurnResult,
        thread: str,
        agent_id: str,
        emit: Callable[[Event], None] | None,
    ) -> TurnResult:
        event = None
        if result.final:
            event = Event(kind="agent", sender=agent_id, text=result.final, thread=thread)
        elif result.handoffs and not result.stopped:
            event = Event(
                kind="agent",
                sender=agent_id,
                text="Handed off: " + ", ".join(target for target, _ in result.handoffs),
                thread=thread,
            )
        if event:
            result.traces.append(event)
            if emit:
                emit(event)
        return result
