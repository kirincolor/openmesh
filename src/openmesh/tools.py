from __future__ import annotations

import shlex
import subprocess
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import AgentConfig
from .files import FileError, FileStore
from .jobs import JobError, ScheduleIn, WorkStore
from .memory import Memory
from .office import OfficeError, ensure_suffix, infer_kind, safe_office_path, write_office
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
        "description": "Write a real file in your workspace (use the correct extension: .cpp, .java, .py, …).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    "inbox_list": {
        "name": "inbox_list",
        "description": "List files and documents attached to this chat.",
        "parameters": {"type": "object", "properties": {}},
    },
    "inbox_read": {
        "name": "inbox_read",
        "description": "Read a text file or document from this chat by id or filename.",
        "parameters": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "File id or filename"},
            },
            "required": ["file"],
        },
    },
    "doc_write": {
        "name": "doc_write",
        "description": "Attach a file to this chat for download. Use filename with the real extension (.cpp, .java, .py). Not for full projects — those go on disk with pc_write.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "filename": {"type": "string", "description": "hello.cpp, notes.md, data.csv, …"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    "office_write": {
        "name": "office_write",
        "description": "Write a Word (.docx), Excel (.xlsx), or PowerPoint (.pptx) file on this computer.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path under an allowed folder, e.g. reports/plan.docx"},
                "kind": {"type": "string", "description": "docx, xlsx, or pptx (optional if the path has a suffix)"},
                "title": {"type": "string"},
                "body": {"type": "string", "description": "Word text, CSV/table for Excel, or slides split by ---"},
                "rows": {"description": "Excel rows: a list of lists, or CSV text"},
                "slides": {"description": "PowerPoint slides: [{title, body}, …]"},
            },
            "required": ["path"],
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
    "schedule_task": {
        "name": "schedule_task",
        "description": "Schedule a follow-up message in this chat. Set exactly one of every_seconds, cron, or at.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "text": {"type": "string", "description": "What to send when it fires"},
                "every_seconds": {"type": "integer", "description": "Repeat interval, min 30"},
                "cron": {"type": "string", "description": "5-field cron, e.g. 0 9 * * 1"},
                "at": {"type": "string", "description": "ISO datetime or unix timestamp, once"},
            },
            "required": ["text"],
        },
    },
    "list_schedule": {
        "name": "list_schedule",
        "description": "List scheduled tasks for this mesh.",
        "parameters": {"type": "object", "properties": {}},
    },
    "cancel_schedule": {
        "name": "cancel_schedule",
        "description": "Cancel a scheduled task by id.",
        "parameters": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    "pc_list": {
        "name": "pc_list",
        "description": "List files in an allowed computer folder. Set recursive to see a project tree.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "recursive": {"type": "boolean", "default": False},
            },
        },
    },
    "pc_read": {
        "name": "pc_read",
        "description": "Read a text file from an allowed computer folder.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    "pc_write": {
        "name": "pc_write",
        "description": "Write a real file on disk (use .cpp, .java, .py, …). Creates parent folders. Use this for projects.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    "pc_run": {
        "name": "pc_run",
        "description": "Run a command in an allowed computer folder. No shell expansion.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string", "description": "Folder inside an allowed root"},
                "timeout": {"type": "integer", "default": 60},
            },
            "required": ["command"],
        },
    },
    "skill_list": {
        "name": "skill_list",
        "description": "List installed local skills (SKILL.md files).",
        "parameters": {"type": "object", "properties": {}},
    },
    "skill_read": {
        "name": "skill_read",
        "description": "Read a local skill so you can follow its instructions.",
        "parameters": {
            "type": "object",
            "properties": {"skill": {"type": "string"}},
            "required": ["skill"],
        },
    },
    "plugin_list": {
        "name": "plugin_list",
        "description": "List local plugins and the tools they expose.",
        "parameters": {"type": "object", "properties": {}},
    },
    "plugin_run": {
        "name": "plugin_run",
        "description": "Run a tool from a local plugin.",
        "parameters": {
            "type": "object",
            "properties": {
                "plugin": {"type": "string"},
                "tool": {"type": "string"},
                "args": {"type": "object"},
            },
            "required": ["plugin", "tool"],
        },
    },
}


class Toolbelt:
    def __init__(
        self,
        vault: Vault,
        memory: Memory,
        files: FileStore,
        work: WorkStore,
        computer: Any = None,
        skills: Any = None,
        plugins: Any = None,
    ) -> None:
        self.vault = vault
        self.memory = memory
        self.files = files
        self.work = work
        self.computer = computer
        self.skills = skills
        self.plugins = plugins
        self.thread = "main"

    def openai_tools(self, agent: AgentConfig) -> list[dict[str, Any]]:
        names = list(agent.tools)
        if "office_write" not in names and {"pc_write", "fs_write", "doc_write"} & set(names):
            names.append("office_write")
        return [
            {"type": "function", "function": SCHEMAS[name]}
            for name in names
            if name in SCHEMAS
        ]

    def run(self, agent: AgentConfig, name: str, args: dict[str, Any], thread: str = "main") -> str:
        self.vault.check(agent, name)
        self.thread = thread
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

    def _local(self, path) -> str:
        return f"LOCAL::{path.stat().st_size}::{path}"

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
        return self._local(target)

    def _tool_inbox_list(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        items = self.files.list_thread(self.thread)
        if not items:
            return "(no files in this chat)"
        return "\n".join(f"{item.id}  {item.name}  {item.size}B  {item.kind}" for item in items)

    def _tool_inbox_read(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        key = str(args.get("file") or args.get("path") or "").strip()
        if not key:
            return "inbox_read needs file id or name"
        try:
            record = self.files.find_in_thread(self.thread, key)
            return self.files.read_text(record.id, self.thread)
        except (FileError, KeyError) as exc:
            return str(exc)

    def _tool_doc_write(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        title = str(args.get("title") or "").strip()
        content = str(args.get("content") or "")
        if not title:
            return "doc_write needs a title"
        filename = str(args.get("filename") or args.get("name") or "").strip() or None
        try:
            record = self.files.write_doc(self.thread, title, content, filename=filename)
        except FileError as exc:
            return str(exc)
        return f"FILE::{record.id}::{record.name}::{record.size}"

    def _output_path(self, agent: AgentConfig, rel: str):
        raw = (rel or "").strip()
        if not raw:
            raise OfficeError("path is required")
        if self.computer is not None:
            try:
                return self.computer.resolve(raw)
            except VaultDenied:
                pass
        return self.vault.resolve_file(agent, raw)

    def _tool_office_write(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        rel = str(args.get("path") or "").strip()
        try:
            kind = infer_kind(rel, str(args.get("kind") or "") or None)
            target = ensure_suffix(safe_office_path(self._output_path(agent, rel)), kind)
            write_office(
                target,
                kind,
                title=str(args.get("title") or ""),
                body=str(args.get("body") or args.get("content") or ""),
                rows=args.get("rows"),
                slides=args.get("slides"),
            )
        except (OfficeError, VaultDenied) as exc:
            return str(exc)
        except Exception as exc:  # noqa: BLE001 — library/import faults stay in the tool result
            return f"office write failed: {type(exc).__name__}: {exc}"
        return self._local(target)

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

    def _tool_schedule_task(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        every = args.get("every_seconds")
        try:
            item = self.work.add_schedule(
                ScheduleIn(
                    title=str(args.get("title") or ""),
                    thread=self.thread,
                    text=str(args.get("text") or ""),
                    every_seconds=int(every) if every not in (None, "") else None,
                    cron=str(args["cron"]) if args.get("cron") else None,
                    at=str(args["at"]) if args.get("at") else None,
                )
            )
        except JobError as exc:
            return str(exc)
        when = item.cron or (f"every {item.every_seconds}s" if item.every_seconds else f"at {item.at_ts}")
        return f"scheduled {item.id} ({when}): {item.title}"

    def _tool_list_schedule(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if not self.work.schedules:
            return "(no schedules)"
        lines = []
        for item in self.work.schedules:
            state = "on" if item.enabled else "off"
            when = item.cron or (f"every {item.every_seconds}s" if item.every_seconds else f"at {item.at_ts}")
            lines.append(f"{item.id}  {state}  {when}  {item.thread}  {item.title}")
        return "\n".join(lines)

    def _tool_cancel_schedule(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        schedule_id = str(args.get("id") or "").strip()
        if not schedule_id:
            return "cancel_schedule needs id"
        try:
            self.work.delete_schedule(schedule_id)
        except KeyError:
            return f"unknown schedule: {schedule_id}"
        return f"cancelled {schedule_id}"

    def _tool_pc_list(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.computer is None:
            return "computer is not available"
        try:
            target = self.computer.resolve(str(args.get("path") or "."))
        except VaultDenied as exc:
            return str(exc)
        if not target.exists():
            return "(missing)"
        if target.is_file():
            return target.name
        if args.get("recursive"):
            return self.computer.tree(str(args.get("path") or "."))
        names = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
        return "\n".join(names) or "(empty)"

    def _tool_pc_read(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.computer is None:
            return "computer is not available"
        try:
            target = self.computer.resolve(str(args.get("path") or ""))
        except VaultDenied as exc:
            return str(exc)
        if not target.is_file():
            return "not a file"
        return target.read_text(encoding="utf-8", errors="replace")[:20_000]

    def _tool_pc_write(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.computer is None:
            return "computer is not available"
        rel = str(args.get("path") or "")
        try:
            target = self.computer.resolve(rel)
        except VaultDenied as exc:
            return str(exc)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(args.get("content") or ""), encoding="utf-8")
        return self._local(target)

    def _tool_pc_run(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.computer is None:
            return "computer is not available"
        timeout = args.get("timeout")
        try:
            seconds = int(timeout) if timeout not in (None, "") else 60
        except (TypeError, ValueError):
            seconds = 60
        try:
            return self.computer.run(
                str(args.get("command") or ""),
                cwd=str(args["cwd"]) if args.get("cwd") else None,
                timeout=seconds,
            )
        except VaultDenied as exc:
            return str(exc)

    def _tool_skill_list(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.skills is None:
            return "skills are not available"
        items = self.skills.list()
        if not items:
            return "(no skills). Put SKILL.md files in the skills/ folder."
        return "\n".join(f"{item['id']}: {item['title']}" for item in items)

    def _tool_skill_read(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.skills is None:
            return "skills are not available"
        return self.skills.read(str(args.get("skill") or args.get("id") or ""))

    def _tool_plugin_list(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.plugins is None:
            return "plugins are not available"
        items = self.plugins.list()
        if not items:
            return "(no plugins). Each plugin is a folder with plugin.json."
        lines = []
        for item in items:
            tools = ", ".join(item.get("tools") or []) or "no tools"
            lines.append(f"{item['id']}: {item['name']} — {item['description']} [{tools}]")
        return "\n".join(lines)

    def _tool_plugin_run(self, agent: AgentConfig, args: dict[str, Any]) -> str:
        if self.plugins is None:
            return "plugins are not available"
        extra = args.get("args")
        payload = extra if isinstance(extra, dict) else {}
        return self.plugins.run(str(args.get("plugin") or ""), str(args.get("tool") or ""), payload)
