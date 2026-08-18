from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import find_root, load_config
from .scaffold import init_project


def main() -> None:
    parser = argparse.ArgumentParser(prog="openmesh", description="Local multi-agent Mesh")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="Start the local room")
    serve.add_argument("--host", default=os.environ.get("OPENMESH_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("OPENMESH_PORT", "8787")))
    serve.add_argument("--root", type=Path, default=None)

    init = sub.add_parser("init", help="Create mesh.yaml and workspaces")
    init.add_argument("path", nargs="?", default=".", type=Path)

    args = parser.parse_args()
    if args.cmd == "serve":
        _serve(args.host, args.port, args.root)
    elif args.cmd == "init":
        root = init_project(args.path)
        print(f"Created mesh in {root}")
        print("Copy .env.example to .env, then run: openmesh serve")


def _serve(host: str, port: int, root: Path | None) -> None:
    import uvicorn

    from .server import create_app

    config = load_config(root or find_root())
    app = create_app(config)
    print(f"OpenMesh room: http://{host}:{port}")
    print(f"Team file:     {config.root / 'mesh.yaml'}")
    if not config.provider.api_key:
        print("No API key yet. Open the room and paste one, or copy .env.example to .env")
    uvicorn.run(app, host=host, port=port, log_level="info")
