from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def user_home() -> Path:
    from platformdirs import user_data_dir

    return Path(user_data_dir("OpenMesh", "OpenMesh"))


def resolve_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    if is_frozen():
        return user_home()
    from .config import find_root

    return find_root()


def ensure_mesh(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "mesh.yaml").exists():
        from .scaffold import init_project

        init_project(root)
    else:
        from .scaffold import write_extras

        write_extras(root)
    return root
