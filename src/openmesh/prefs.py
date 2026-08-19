from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class UiPrefs(BaseModel):
    theme: Literal["light", "dark"] = "light"
    language: Literal["en", "zh"] = "en"


class PrefsIn(BaseModel):
    theme: Literal["light", "dark"] | None = None
    language: Literal["en", "zh"] | None = None


def prefs_path(root: Path) -> Path:
    return root / "data" / "ui.json"


def load_prefs(root: Path) -> UiPrefs:
    path = prefs_path(root)
    if not path.exists():
        return UiPrefs()
    try:
        return UiPrefs.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        return UiPrefs()


def save_prefs(root: Path, prefs: UiPrefs) -> UiPrefs:
    path = prefs_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prefs.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return prefs


def patch_prefs(root: Path, body: PrefsIn) -> UiPrefs:
    current = load_prefs(root)
    data = current.model_dump()
    if body.theme is not None:
        data["theme"] = body.theme
    if body.language is not None:
        data["language"] = body.language
    return save_prefs(root, UiPrefs.model_validate(data))
