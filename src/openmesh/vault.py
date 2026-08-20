from __future__ import annotations

from pathlib import Path

from .config import AgentConfig, MeshConfig

ALL_TOOLS = {
    "handoff",
    "memory_read",
    "memory_write",
    "fs_list",
    "fs_read",
    "fs_write",
    "inbox_list",
    "inbox_read",
    "doc_write",
    "schedule_task",
    "list_schedule",
    "cancel_schedule",
    "http_fetch",
    "shell",
    "pc_list",
    "pc_read",
    "pc_write",
    "pc_run",
    "skill_list",
    "skill_read",
    "plugin_list",
    "plugin_run",
    "office_write",
}


class VaultDenied(PermissionError):
    pass


class Vault:
    """Per-agent capability gate. Keys never leave the runtime."""

    def __init__(self, config: MeshConfig) -> None:
        self.config = config

    def allowed(self, agent: AgentConfig) -> set[str]:
        granted = set(agent.tools) & ALL_TOOLS
        if granted & {"pc_write", "fs_write", "doc_write"}:
            granted.add("office_write")
        return granted

    def check(self, agent: AgentConfig, tool: str) -> None:
        if tool not in self.allowed(agent):
            raise VaultDenied(f"{agent.id} is not allowed to use '{tool}'")

    def workspace(self, agent: AgentConfig) -> Path:
        rel = agent.workspace or f"workspaces/{agent.id}"
        path = (self.config.root / rel).resolve()
        path.mkdir(parents=True, exist_ok=True)
        root = self.config.root.resolve()
        if path != root and root not in path.parents:
            raise VaultDenied(f"workspace escapes project root: {path}")
        return path

    def resolve_file(self, agent: AgentConfig, rel: str) -> Path:
        workspace = self.workspace(agent)
        target = (workspace / rel).resolve()
        if target != workspace and workspace not in target.parents:
            raise VaultDenied(f"path escapes {agent.id} workspace: {rel}")
        return target
