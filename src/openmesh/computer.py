from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from .vault import VaultDenied


class ComputerIn(BaseModel):
    roots: list[str] = Field(default_factory=list)


class Computer:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / "data" / "computer.json"
        self.roots: list[Path] = []
        self._load()
        default = (root / "computer").resolve()
        default.mkdir(parents=True, exist_ok=True)
        if not self.roots:
            self.roots = [default]
            self.save()

    def _load(self) -> None:
        if not self.path.exists():
            self.roots = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.roots = []
            return
        self.roots = []
        for item in raw.get("roots") or []:
            path = Path(item)
            if not path.is_absolute():
                path = self.root / path
            self.roots.append(path.resolve())

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "roots": [str(path) for path in self.roots],
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def public(self) -> list[str]:
        return [str(path) for path in self.roots]

    def set_roots(self, roots: list[str]) -> list[str]:
        resolved: list[Path] = []
        for item in roots:
            path = Path(item.strip())
            if not path.is_absolute():
                path = (self.root / path).resolve()
            else:
                path = path.resolve()
            path.mkdir(parents=True, exist_ok=True)
            resolved.append(path)
        if not resolved:
            resolved = [(self.root / "computer").resolve()]
            resolved[0].mkdir(parents=True, exist_ok=True)
        self.roots = resolved
        self.save()
        return self.public()

    def resolve(self, rel: str) -> Path:
        raw = (rel or ".").strip() or "."
        target = Path(raw)
        if not target.is_absolute():
            target = (self.roots[0] / raw).resolve()
        else:
            target = target.resolve()
        for root in self.roots:
            if target == root or root in target.parents:
                return target
        raise VaultDenied(f"path is outside allowed computer folders: {rel}")

    def tree(self, rel: str = ".", max_depth: int = 5) -> str:
        root = self.resolve(rel)
        if root.is_file():
            return root.name
        lines: list[str] = [str(root)]
        def walk(folder: Path, prefix: str, depth: int) -> None:
            if depth > max_depth:
                return
            try:
                kids = sorted(folder.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
            except OSError as exc:
                lines.append(f"{prefix}({exc})")
                return
            for index, item in enumerate(kids[:200]):
                last = index == len(kids[:200]) - 1
                branch = "└─ " if last else "├─ "
                lines.append(f"{prefix}{branch}{item.name}{'/' if item.is_dir() else ''}")
                if item.is_dir():
                    walk(item, prefix + ("   " if last else "│  "), depth + 1)
        walk(root, "", 1)
        return "\n".join(lines)[:12_000]

    def run(self, command: str, cwd: str | None = None, timeout: int = 60) -> str:
        raw = command.strip()
        if not raw:
            return "empty command"
        try:
            argv = shlex.split(raw)
        except ValueError as exc:
            return f"bad command: {exc}"
        work = self.resolve(cwd or ".")
        if work.is_file():
            work = work.parent
        work.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                argv,
                cwd=work,
                capture_output=True,
                text=True,
                timeout=min(max(timeout, 1), 120),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "timeout"
        except OSError as exc:
            return f"exec failed: {exc}"
        out = (proc.stdout or "") + (proc.stderr or "")
        return (out or f"exit {proc.returncode}")[:12000]
