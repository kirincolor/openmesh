from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .bus import Event
from .config import MeshConfig, load_config
from .prefs import PrefsIn, patch_prefs
from .runtime import Mesh
from .secrets import write_env
from .team import AgentIn, TeamError, add_agent, remove_agent, update_agent

STATIC = Path(__file__).parent / "static"


class ChatIn(BaseModel):
    text: str
    thread: str = "main"
    to: str | None = None


class SecretsIn(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def create_app(config: MeshConfig | None = None) -> FastAPI:
    config = config or load_config()
    mesh = Mesh(config)
    app = FastAPI(title="OpenMesh", version="0.1.0")
    app.state.mesh = mesh

    @app.get("/api/state")
    async def state() -> dict:
        return mesh.snapshot()

    @app.post("/api/chat")
    async def chat(body: ChatIn) -> dict:
        text = body.text.strip()
        if not text:
            raise HTTPException(400, "empty message")
        if not mesh.config.provider.api_key:
            raise HTTPException(400, "missing API key")
        if mesh.running:
            raise HTTPException(409, "mesh is busy")

        async def run() -> None:
            try:
                await mesh.user_say(text, thread=body.thread, to=body.to)
            except Exception as exc:  # noqa: BLE001 — surface to the room, not the HTTP client
                await mesh.bus.publish(
                    Event(kind="error", sender="mesh", text=str(exc), thread=body.thread)
                )

        asyncio.create_task(run())
        return {"ok": True}

    @app.get("/api/stream")
    async def stream() -> StreamingResponse:
        queue: asyncio.Queue = asyncio.Queue()

        async def listener(event) -> None:
            await queue.put(event)

        mesh.bus.on(listener)

        async def gen():
            try:
                yield f"data: {json.dumps({'hello': True})}\n\n"
                while True:
                    event = await queue.get()
                    yield f"data: {event.model_dump_json()}\n\n"
            finally:
                mesh.bus.off(listener)

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/secrets")
    async def secrets(body: SecretsIn) -> dict:
        write_env(
            config.root,
            {
                "OPENMESH_API_KEY": body.api_key,
                "OPENMESH_BASE_URL": body.base_url,
                "OPENMESH_MODEL": body.model,
            },
        )
        if body.api_key is not None:
            mesh.config.provider.api_key = body.api_key
            mesh.llm.provider.api_key = body.api_key
        if body.base_url is not None:
            mesh.config.provider.base_url = body.base_url
            mesh.llm.provider.base_url = body.base_url
        if body.model is not None:
            mesh.config.provider.model = body.model
            mesh.llm.provider.model = body.model
        return {"ok": True, "has_key": bool(mesh.config.provider.api_key)}

    @app.put("/api/prefs")
    async def prefs(body: PrefsIn) -> dict:
        return {"ok": True, "prefs": patch_prefs(config.root, body).model_dump()}

    def _busy() -> None:
        if mesh.running:
            raise HTTPException(409, "mesh is busy")

    def _team_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(404, f"teammate '{exc.args[0]}' not found")
        if isinstance(exc, TeamError):
            return HTTPException(400, str(exc))
        raise exc

    @app.post("/api/agents")
    async def create_agent(body: AgentIn) -> dict:
        _busy()
        try:
            agent = add_agent(mesh.config, body)
        except (TeamError, KeyError) as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "agent": agent.model_dump()}

    @app.put("/api/agents/{agent_id}")
    async def edit_agent(agent_id: str, body: AgentIn) -> dict:
        _busy()
        try:
            agent = update_agent(mesh.config, agent_id, body)
        except (TeamError, KeyError) as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "agent": agent.model_dump()}

    @app.delete("/api/agents/{agent_id}")
    async def delete_agent(agent_id: str) -> dict:
        _busy()
        try:
            remove_agent(mesh.config, agent_id)
        except (TeamError, KeyError) as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "chief": mesh.config.mesh.chief}

    @app.delete("/api/room")
    async def clear_room() -> dict:
        mesh.clear_room()
        return {"ok": True}

    favicon = STATIC / "favicon.svg"

    @app.get("/favicon.ico")
    async def favicon_ico() -> FileResponse:
        if not favicon.exists():
            raise HTTPException(404, "missing favicon")
        return FileResponse(favicon, media_type="image/svg+xml")

    if STATIC.exists():
        app.mount("/static", StaticFiles(directory=STATIC), name="static")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(STATIC / "index.html")

    return app
