from __future__ import annotations

from pathlib import Path

ENV_KEYS = ("OPENMESH_API_KEY", "OPENMESH_BASE_URL", "OPENMESH_MODEL")


def redact(text: str, secret: str) -> str:
    if secret and secret in text:
        return text.replace(secret, "***")
    return text


def write_env(root: Path, updates: dict[str, str | None]) -> Path:
    path = root / ".env"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = current.splitlines()
    written: set[str] = set()
    out: list[str] = []
    for line in lines:
        key = ""
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0]
        if key in updates and updates[key] is not None:
            out.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if value is not None and key not in written:
            out.append(f"{key}={value}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return path
