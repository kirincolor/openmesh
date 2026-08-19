from __future__ import annotations

import asyncio
import json
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .bus import Event
from .chats import ChatError, GroupIn
from .config import MeshConfig, load_config
from .files import DocIn, FileError
from .jobs import JobError, ModelIn, ScheduleIn
from .prefs import PrefsIn, patch_prefs
from .runtime import Mesh
from .secrets import write_env
from .team import AgentIn, TeamError, add_agent, remove_agent, update_agent

STATIC = Path(__file__).parent / "static"


class ChatIn(BaseModel):
    text: str
    thread: str | None = None
    to: str | None = None
    model: str | None = None


class SecretsIn(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def create_app(config: MeshConfig | None = None) -> FastAPI:
    config = config or load_config()
    mesh = Mesh(config)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        stop = asyncio.Event()

        async def loop() -> None:
            while not stop.is_set():
                try:
                    await mesh.tick_schedules()
                except Exception:
                    pass
                try:
                    await asyncio.wait_for(stop.wait(), timeout=5)
                except TimeoutError:
                    pass

        task = asyncio.create_task(loop())
        yield
        stop.set()
        task.cancel()

    app = FastAPI(title="OpenMesh", version="0.1.0", lifespan=lifespan)
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
        try:
            thread = mesh.resolve_thread(body.thread, body.to)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if mesh.thread_busy(thread):
            raise HTTPException(409, "this chat is busy")

        async def run() -> None:
            try:
                await mesh.user_say(text, thread=thread, to=body.to, model=body.model)
            except Exception as exc:  # noqa: BLE001 — surface to the room, not the HTTP client
                await mesh.bus.publish(
                    Event(kind="error", sender="mesh", text=str(exc), thread=thread)
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
        if mesh.work.active_threads():
            raise HTTPException(409, "a job is running")

    def _team_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(404, f"not found: {exc.args[0]}")
        if isinstance(exc, (TeamError, ChatError, FileError, JobError, ValueError)):
            return HTTPException(400, str(exc))
        raise exc

    def _require_chat(chat_id: str) -> None:
        if mesh.chats.get(chat_id, mesh.config) is None and chat_id != "main":
            raise HTTPException(404, f"unknown chat: {chat_id}")

    async def _publish_file(record, sender: str = "you") -> dict:
        await mesh.bus.publish(
            Event(
                kind="file",
                sender=sender,
                text=record.name,
                thread=record.thread,
                meta=record.model_dump(),
            )
        )
        return record.model_dump()

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
        mesh.chats.drop_agent(agent_id)
        return {"ok": True, "chief": mesh.config.mesh.chief}

    @app.post("/api/chats")
    async def create_chat(body: GroupIn) -> dict:
        try:
            chat = mesh.chats.create_group(mesh.config, body)
        except (ChatError, KeyError) as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "chat": chat.model_dump()}

    @app.put("/api/chats/{chat_id}")
    async def edit_chat(chat_id: str, body: GroupIn) -> dict:
        try:
            chat = mesh.chats.update_group(mesh.config, chat_id, body)
        except (ChatError, KeyError) as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "chat": chat.model_dump()}

    @app.delete("/api/chats/{chat_id}")
    async def delete_chat(chat_id: str) -> dict:
        try:
            mesh.chats.delete_group(chat_id)
        except KeyError as exc:
            raise _team_error(exc) from exc
        mesh.clear_chat(chat_id)
        return {"ok": True}

    @app.delete("/api/chats/{chat_id}/messages")
    async def clear_chat(chat_id: str) -> dict:
        _require_chat(chat_id)
        mesh.clear_chat(chat_id)
        return {"ok": True}

    @app.post("/api/chats/{chat_id}/files")
    async def upload_file(chat_id: str, file: UploadFile = File(...)) -> dict:
        _require_chat(chat_id)
        data = await file.read()
        try:
            record = mesh.files.save_bytes(chat_id, file.filename or "upload", data)
        except FileError as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "file": await _publish_file(record)}

    @app.post("/api/chats/{chat_id}/docs")
    async def write_doc(chat_id: str, body: DocIn) -> dict:
        _require_chat(chat_id)
        try:
            record = mesh.files.write_doc(chat_id, body.title, body.content)
        except FileError as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "file": await _publish_file(record)}

    @app.get("/api/files/{file_id}")
    async def download_file(file_id: str) -> FileResponse:
        try:
            record = mesh.files.get(file_id)
        except KeyError as exc:
            raise HTTPException(404, f"file '{file_id}' not found") from exc
        path = mesh.files.blob_path(record)
        if not path.is_file():
            raise HTTPException(404, "missing file")
        return FileResponse(path, filename=record.name, media_type=record.mime)

    @app.put("/api/chats/{chat_id}/model")
    async def set_chat_model(chat_id: str, body: ModelIn) -> dict:
        _require_chat(chat_id)
        try:
            model = mesh.set_chat_model(chat_id, body.model)
        except JobError as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "model": model}

    @app.post("/api/chats/{chat_id}/stop")
    async def stop_chat(chat_id: str) -> dict:
        _require_chat(chat_id)
        return {"ok": True, "cancelled": mesh.cancel_thread(chat_id)}

    @app.get("/api/schedules")
    async def list_schedules() -> dict:
        return {"schedules": [item.model_dump() for item in mesh.work.schedules]}

    @app.post("/api/schedules")
    async def create_schedule(body: ScheduleIn) -> dict:
        try:
            if mesh.chats.get(body.thread, mesh.config) is None:
                raise JobError("unknown chat")
            item = mesh.work.add_schedule(body)
        except JobError as exc:
            raise _team_error(exc) from exc
        return {"ok": True, "schedule": item.model_dump()}

    @app.delete("/api/schedules/{schedule_id}")
    async def delete_schedule(schedule_id: str) -> dict:
        try:
            mesh.work.delete_schedule(schedule_id)
        except KeyError as exc:
            raise _team_error(exc) from exc
        return {"ok": True}

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
