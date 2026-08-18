from __future__ import annotations

from pathlib import Path

from .config import MeshConfig


class Memory:
    def __init__(self, config: MeshConfig) -> None:
        self.dir = config.data_dir() / "memory"
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, scope: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in scope)
        return self.dir / f"{safe}.md"

    def read(self, scope: str) -> str:
        path = self.path(scope)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write(self, scope: str, text: str, append: bool = True) -> str:
        path = self.path(scope)
        if append and path.exists():
            existing = path.read_text(encoding="utf-8").rstrip()
            path.write_text(existing + "\n\n" + text.strip() + "\n", encoding="utf-8")
        else:
            path.write_text(text.strip() + "\n", encoding="utf-8")
        return f"wrote memory/{path.name}"
