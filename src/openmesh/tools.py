from __future__ import annotations

import shlex
import subprocess
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import AgentConfig
from .memory import Memory
from .ssrf import blocked_reason
from .vault import Vault, VaultDenied


SCHEMAS: dict[str, dict[str, Any]] = {
    "handoff": {
        "name": "handoff",
        "description": "Give a teammate a concrete task. They will post back in the room.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Teammate id, e.g. coder"},
                "task": {"type": "string", "description": "What they should do"},
            },
            "required": ["agent_id", "task"],
        },
    },
    "memory_read": {
        "name": "memory_read",
        "description": "Read shared or personal notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "description": "shared, or an agent id",
                }
            },
            "required": ["scope"],
        },
    },
    "memory_write": {
        "name": "memory_write",
        "description": "Write a durable note the team can reuse later.",
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {"type": "string"},
                "text": {"type": "string"},
                "append": {"type": "boolean", "default": True},
            },
            "required": ["scope", "text"],
        },
    },
    "fs_list": {
        "name": "fs_list",
        "description": "List files in your workspace (relative path).",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "default": "."}},
        },
    },
    "fs_read": {
        "name": "fs_read",
        "description": "Read a file from your workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    "fs_write": {
        "name": "fs_write",
        "description": "Write a file in your workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    "http_fetch": {
        "name": "http_fetch",
        "description": "GET a public URL and return text (truncated).",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    "shell": {
        "name": "shell",
        "description": "Run a command inside your workspace only. No shell expansion.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}


class Toolbelt:
    def __init__(self, vault: Vault, memory: Memory) -> None:
        self.vault = vault
        self.memory = memory

    def openai_tools(self, agent: AgentConfig) -> list[dict[str, Any]]:
        return [
            {"type": "function", "function": SCHEMAS[name]}
            for name in agent.tools
            if name in SCHEMAS
        ]

    def run(self, agent: AgentConfig, name: str, args: dict[str, Any]) -> str:
        self.vault.check(agent, name)
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            raise VaultDenied(f"unknown tool: {name}")
        return handler(agent, args)

    def _tool_handoff(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        target = str(args.get("agent_id") or "").strip()
        task = str(args.get("task") or "").strip()
        if not target or not task:
            return "handoff needs agent_id and task"
        if target == agent.id:
            return "cannot hand off to yourself"
        try:
            self.vault.config.agent(target)
        except KeyError:
            return f"unknown teammate: {target}"
        return f"HANDOFF::{target}::{task}"

    def _tool_memory_read(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        scope = str(args.get("scope") or agent.id)
        if scope not in {agent.id, "shared"}:
            return f"vault: {agent.id} can only read shared or own memory"
        text = self.memory.read(scope)
        return text or "(empty)"

    def _tool_memory_write(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        scope = str(args.get("scope") or agent.id)
        if scope not in {agent.id, "shared"}:
            return "vault: can only write own or shared memory"
        return self.memory.write(
            scope,
            str(args.get("text") or ""),
            append=bool(args.get("append", True)),
        )

    def _tool_fs_list(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        target = self.vault.resolve_file(agent, str(args.get("path") or "."))
        if not target.exists():
            return "(missing)"
        if target.is_file():
            return target.name
        names = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
        return "\n".join(names) or "(empty)"

    def _tool_fs_read(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        target = self.vault.resolve_file(agent, str(args["path"]))
        if not target.is_file():
            return "not a file"
        text = target.read_text(encoding="utf-8", errors="replace")
        return text[:20_000]

    def _tool_fs_write(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        target = self.vault.resolve_file(agent, str(args["path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(args.get("content") or ""), encoding="utf-8")
        return f"wrote {args['path']}"

    def _tool_http_fetch(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        url = str(args.get("url") or "")
        for _ in range(4):
            reason = blocked_reason(url)
            if reason:
                return reason
            try:
                response = httpx.get(
                    url,
                    timeout=20.0,
                    follow_redirects=False,
                    headers={"User-Agent": "openmesh/0.1"},
                )
            except httpx.HTTPError as exc:
                return f"fetch failed: {exc}"
            if response.is_redirect:
                location = response.headers.get("location") or ""
                if not location:
                    return "redirect without location"
                url = urljoin(url, location)
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPError as exc:
                return f"fetch failed: {exc}"
            return response.text[:12_000]
        return "too many redirects"

    def _tool_shell(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        raw = str(args.get("command") or "").strip()
        if not raw:
            return "empty command"
        try:
            argv = shlex.split(raw)
        except ValueError as exc:
            return f"bad command: {exc}"
        cwd = self.vault.workspace(agent)
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "timeout"
        except OSError as exc:
            return f"exec failed: {exc}"
        out = (proc.stdout or "") + (proc.stderr or "")
        return (out or f"exit {proc.returncode}")[:8000]
