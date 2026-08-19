from __future__ import annotations

from pathlib import Path


class SkillBook:
    def __init__(self, root: Path) -> None:
        self.dir = root / "skills"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _files(self) -> list[Path]:
        if not self.dir.exists():
            return []
        found = list(self.dir.glob("*/SKILL.md")) + list(self.dir.glob("*.md"))
        return sorted({path.resolve() for path in found if path.is_file()})

    def list(self) -> list[dict[str, str]]:
        items = []
        for path in self._files():
            text = path.read_text(encoding="utf-8", errors="replace")
            title = path.parent.name if path.name == "SKILL.md" else path.stem
            first = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip()), title)
            items.append({"id": title, "title": first, "path": str(path.relative_to(self.dir))})
        return items

    def read(self, skill_id: str) -> str:
        key = skill_id.strip()
        if not key or any(part in key for part in ("/", "\\", "..")):
            return "bad skill id"
        for path in self._files():
            ident = path.parent.name if path.name == "SKILL.md" else path.stem
            if ident == key or path.stem == key:
                return path.read_text(encoding="utf-8", errors="replace")[:20_000]
        return f"unknown skill: {key}"
