from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import find_root, load_config
from .paths import is_frozen
from .scaffold import init_project


def main() -> None:
    if is_frozen() and len(sys.argv) == 1:
        from .desktop import run_desktop

        run_desktop()
        return

    parser = argparse.ArgumentParser(prog="openmesh", description="Local multi-agent workspace")
    sub = parser.add_subparsers(dest="cmd", required=False)

    serve = sub.add_parser("serve", help="Start the local web app")
    serve.add_argument("--host", default=os.environ.get("OPENMESH_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("OPENMESH_PORT", "8787")))
    serve.add_argument("--root", type=Path, default=None)

    desk = sub.add_parser("desktop", help="Open the desktop window")
    desk.add_argument("--host", default=os.environ.get("OPENMESH_HOST", "127.0.0.1"))
    desk.add_argument("--root", type=Path, default=None)

    init = sub.add_parser("init", help="Create mesh.yaml and workspaces")
    init.add_argument("path", nargs="?", default=".", type=Path)

    args = parser.parse_args()
    if args.cmd in (None, "desktop"):
        from .desktop import run_desktop

        run_desktop(getattr(args, "root", None), getattr(args, "host", "127.0.0.1"))
    elif args.cmd == "serve":
        _serve(args.host, args.port, args.root)
    elif args.cmd == "init":
        root = init_project(args.path)
        print(f"Created mesh in {root}")
        print("Then either: openmesh desktop   or   openmesh serve")


def _serve(host: str, port: int, root: Path | None) -> None:
    import uvicorn

    from .server import create_app

    config = load_config(root or find_root())
    app = create_app(config)
    print(f"OpenMesh:  http://{host}:{port}")
    print(f"Team file: {config.root / 'mesh.yaml'}")
    if not config.provider.api_key:
        print("No API key yet. Open Settings in the app.")
    uvicorn.run(app, host=host, port=port, log_level="info")
