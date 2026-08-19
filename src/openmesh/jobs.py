from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

class JobError(ValueError):
    pass


class Run(BaseModel):
    id: str
    thread: str
    status: Literal["running", "done", "error", "cancelled"] = "running"
    model: str = ""
    text: str = ""
    rounds: int = 0
    error: str = ""
    created_ts: float = Field(default_factory=time.time)
    updated_ts: float = Field(default_factory=time.time)


class Schedule(BaseModel):
    id: str
    title: str
    thread: str
    text: str
    every_seconds: int | None = None
    cron: str | None = None
    at_ts: float | None = None
    enabled: bool = True
    last_run: float | None = None
    next_run: float | None = None
    created_ts: float = Field(default_factory=time.time)


class ScheduleIn(BaseModel):
    title: str = ""
    thread: str
    text: str
    every_seconds: int | None = None
    cron: str | None = None
    at: str | None = None


class ModelIn(BaseModel):
    model: str


def cron_match(expr: str, when: datetime) -> bool:
    parts = expr.split()
    if len(parts) != 5:
        raise JobError("cron must be 5 fields: m h dom mon dow")
    minute, hour, day, month, dow = parts
    return (
        _field(minute, when.minute, 0, 59)
        and _field(hour, when.hour, 0, 23)
        and _field(day, when.day, 1, 31)
        and _field(month, when.month, 1, 12)
        and _field(dow, when.isoweekday() % 7, 0, 6)
    )


def _field(expr: str, value: int, lo: int, hi: int) -> bool:
    if expr == "*":
        return True
    for part in expr.split(","):
        part = part.strip()
        if part.startswith("*/"):
            step = int(part[2:])
            if step <= 0:
                raise JobError("cron step must be > 0")
            if value % step == 0:
                return True
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            if lo <= int(start_s) <= value <= int(end_s) <= hi:
                return True
            continue
        if int(part) == value:
            return True
    return False


def parse_at(value: str) -> float:
    text = value.strip()
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError as exc:
        raise JobError("at must be unix time or ISO datetime") from exc


class WorkStore:
    def __init__(self, root: Path) -> None:
        self.path = root / "data" / "work.json"
        self.runs: list[Run] = []
        self.schedules: list[Schedule] = []
        self.chat_models: dict[str, str] = {}
        self.cancelled: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.runs = [Run.model_validate(item) for item in raw.get("runs") or []][-80:]
        self.schedules = [Schedule.model_validate(item) for item in raw.get("schedules") or []]
        self.chat_models = {str(k): str(v) for k, v in (raw.get("chat_models") or {}).items() if v}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.runs = self.runs[-80:]
        payload = {
            "runs": [item.model_dump() for item in self.runs],
            "schedules": [item.model_dump() for item in self.schedules],
            "chat_models": self.chat_models,
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def start_run(self, thread: str, text: str, model: str) -> Run:
        run = Run(id=uuid.uuid4().hex[:12], thread=thread, text=text[:200], model=model)
        self.runs.append(run)
        self.cancelled.discard(run.id)
        self.save()
        return run

    def finish_run(self, run: Run, status: str, rounds: int = 0, error: str = "") -> None:
        run.status = status  # type: ignore[assignment]
        run.rounds = rounds
        run.error = error
        run.updated_ts = time.time()
        self.save()

    def cancel_thread(self, thread: str) -> list[str]:
        ids = [run.id for run in self.runs if run.thread == thread and run.status == "running"]
        self.cancelled.update(ids)
        return ids

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self.cancelled

    def active_threads(self) -> list[str]:
        return [run.thread for run in self.runs if run.status == "running"]

    def thread_busy(self, thread: str) -> bool:
        return any(run.thread == thread and run.status == "running" for run in self.runs)

    def set_chat_model(self, thread: str, model: str) -> str:
        model = model.strip()
        if not model or len(model) > 80:
            raise JobError("invalid model")
        self.chat_models[thread] = model
        self.save()
        return model

    def model_for(self, thread: str, fallback: str) -> str:
        return self.chat_models.get(thread) or fallback

    def add_schedule(self, body: ScheduleIn) -> Schedule:
        text = body.text.strip()
        if not text:
            raise JobError("schedule needs a message")
        thread = body.thread.strip()
        if not thread:
            raise JobError("schedule needs a chat")
        kinds = [body.every_seconds, body.cron, body.at]
        if sum(1 for item in kinds if item) != 1:
            raise JobError("set exactly one of every_seconds, cron, or at")
        at_ts = parse_at(body.at) if body.at else None
        every = int(body.every_seconds) if body.every_seconds else None
        if every is not None and every < 30:
            raise JobError("every_seconds must be at least 30")
        cron = body.cron.strip() if body.cron else None
        if cron:
            cron_match(cron, datetime.now())
        now = time.time()
        next_run = now + every if every else at_ts
        item = Schedule(
            id=uuid.uuid4().hex[:8],
            title=body.title.strip() or text[:40],
            thread=thread,
            text=text,
            every_seconds=every,
            cron=cron,
            at_ts=at_ts,
            next_run=next_run,
        )
        self.schedules.append(item)
        self.save()
        return item

    def delete_schedule(self, schedule_id: str) -> None:
        before = len(self.schedules)
        self.schedules = [item for item in self.schedules if item.id != schedule_id]
        if len(self.schedules) == before:
            raise KeyError(schedule_id)
        self.save()

    def due(self, now: float | None = None) -> list[Schedule]:
        now = time.time() if now is None else now
        when = datetime.fromtimestamp(now)
        ready: list[Schedule] = []
        for item in self.schedules:
            if not item.enabled:
                continue
            if item.at_ts is not None:
                if now >= item.at_ts and item.last_run is None:
                    ready.append(item)
                continue
            if item.every_seconds and item.next_run is not None and now >= item.next_run:
                ready.append(item)
                continue
            if item.cron:
                last_minute = int((item.last_run or 0) // 60)
                if cron_match(item.cron, when) and int(now // 60) != last_minute:
                    ready.append(item)
        return ready

    def mark_fired(self, item: Schedule, now: float | None = None) -> None:
        now = time.time() if now is None else now
        item.last_run = now
        if item.at_ts is not None:
            item.enabled = False
            item.next_run = None
        elif item.every_seconds:
            item.next_run = now + item.every_seconds
        self.save()
