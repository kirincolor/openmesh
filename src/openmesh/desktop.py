from __future__ import annotations

import logging
import socket
import threading
import time
import webbrowser
from pathlib import Path

import httpx

from .paths import ensure_mesh, resolve_root


def _free_port(host: str) -> int:
    sock = socket.socket()
    sock.bind((host, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_up(url: str, tries: int = 60) -> bool:
    for _ in range(tries):
        try:
            httpx.get(url, timeout=0.3)
            return True
        except httpx.HTTPError:
            time.sleep(0.1)
    return False


def _log_to(root: Path) -> None:
    path = root / "openmesh.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )


def run_desktop(root: Path | None = None, host: str = "127.0.0.1") -> None:
    home = ensure_mesh(resolve_root(root))
    _log_to(home)
    logging.info("starting desktop at %s", home)

    import uvicorn

    from .config import load_config
    from .server import create_app

    port = _free_port(host)
    url = f"http://{host}:{port}/"
    config = load_config(home)
    app = create_app(config)
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    if not _wait_up(url):
        logging.error("local server did not start")
        raise RuntimeError(f"OpenMesh failed to start at {url}")

    opened = False
    try:
        import webview

        webview.create_window("OpenMesh", url, width=1180, height=780, min_size=(860, 560))
        webview.start()
        opened = True
    except Exception as exc:  # noqa: BLE001 — fall back to the system browser
        logging.warning("desktop window unavailable: %s", exc)

    if not opened:
        webbrowser.open(url)
        print(f"OpenMesh is running at {url}")
        print("Close this window to stop the app.")
        try:
            while thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

    server.should_exit = True
