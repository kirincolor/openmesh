from __future__ import annotations

import json
import subprocess
from pathlib import Path


class PluginBook:
    def __init__(self, root: Path) -> None:
        self.dir = root / "plugins"
        self.dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict]:
        items = []
        for manifest in sorted(self.dir.glob("*/plugin.json")):
            try:
                raw = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            items.append(
                {
                    "id": manifest.parent.name,
                    "name": raw.get("name") or manifest.parent.name,
                    "description": raw.get("description") or "",
                    "tools": [item.get("name") for item in raw.get("tools") or [] if item.get("name")],
                }
            )
        return items

    def run(self, plugin_id: str, tool: str, args: dict) -> str:
        ident = plugin_id.strip()
        if not ident or any(part in ident for part in ("/", "\\", "..")):
            return "bad plugin id"
        folder = (self.dir / ident).resolve()
        if self.dir.resolve() not in folder.parents and folder != self.dir.resolve():
            return "plugin path denied"
        manifest = folder / "plugin.json"
        if not manifest.is_file():
            return f"unknown plugin: {plugin_id}"
        try:
            raw = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return f"bad plugin.json: {exc}"
        spec = None
        for item in raw.get("tools") or []:
            if item.get("name") == tool:
                spec = item
                break
        if spec is None:
            return f"plugin {plugin_id} has no tool {tool}"
        command = spec.get("command")
        if not isinstance(command, list) or not command:
            return "plugin tool needs a command list"
        try:
            proc = subprocess.run(
                [str(part) for part in command],
                cwd=folder,
                input=json.dumps({"tool": tool, "args": args}, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "plugin timeout"
        except OSError as exc:
            return f"plugin failed: {exc}"
        out = (proc.stdout or "") + (proc.stderr or "")
        return (out or f"exit {proc.returncode}")[:12000]
