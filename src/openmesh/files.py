from __future__ import annotations

import json
import mimetypes
import re
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

MAX_BYTES = 10 * 1024 * 1024
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".xml",
    ".toml",
    ".ini",
    ".rst",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".m",
    ".mm",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    ".r",
    ".lua",
    ".vue",
    ".svelte",
    ".gradle",
    ".cmake",
    ".makefile",
}
SAFE_THREAD = re.compile(r"[^a-zA-Z0-9._-]+")
UNSAFE_NAME = re.compile(r"[\\/]+")


class FileError(ValueError):
    pass


class FileRecord(BaseModel):
    id: str
    thread: str
    name: str
    size: int
    mime: str = "application/octet-stream"
    kind: Literal["upload", "doc"] = "upload"
    ts: float = Field(default_factory=time.time)


class DocIn(BaseModel):
    title: str
    content: str = ""
    filename: str | None = None


def sanitize_name(name: str) -> str:
    name = UNSAFE_NAME.sub("_", Path(name).name).strip().strip(".")
    name = name[:120] or "file"
    if name in {".", ".."}:
        raise FileError("invalid file name")
    return name


def slug_title(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", title.strip()).strip("-")
    return (slug[:60] or "document") + ".md"


def filename_for(title: str, filename: str | None = None) -> str:
    if filename and filename.strip():
        return sanitize_name(filename)
    raw = title.strip()
    suffix = Path(raw).suffix
    if suffix and suffix != ".":
        return sanitize_name(raw)
    return slug_title(raw)


class FileStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / "data" / "files"
        self.index_path = self.base / "index.json"
        self.files: dict[str, FileRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.index_path.exists():
            self.files = {}
            return
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.files = {}
            return
        self.files = {
            item["id"]: FileRecord.model_validate(item) for item in raw.get("files") or [] if item.get("id")
        }

    def _save(self) -> None:
        self.base.mkdir(parents=True, exist_ok=True)
        payload = {"files": [item.model_dump() for item in self.files.values()]}
        self.index_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def thread_dir(self, thread: str) -> Path:
        key = SAFE_THREAD.sub("_", thread)[:80] or "chat"
        path = (self.base / key).resolve()
        root = self.base.resolve()
        root.mkdir(parents=True, exist_ok=True)
        if path != root and root not in path.parents:
            raise FileError("invalid chat path")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def blob_path(self, record: FileRecord) -> Path:
        return self.thread_dir(record.thread) / record.id

    def get(self, file_id: str) -> FileRecord:
        record = self.files.get(file_id)
        if record is None:
            raise KeyError(file_id)
        return record

    def list_thread(self, thread: str) -> list[FileRecord]:
        return [item for item in self.files.values() if item.thread == thread]

    def save_bytes(
        self,
        thread: str,
        name: str,
        data: bytes,
        *,
        kind: Literal["upload", "doc"] = "upload",
        mime: str | None = None,
    ) -> FileRecord:
        if len(data) > MAX_BYTES:
            raise FileError("file too large (max 10 MB)")
        name = sanitize_name(name)
        guessed, _ = mimetypes.guess_type(name)
        record = FileRecord(
            id=uuid.uuid4().hex[:12],
            thread=thread,
            name=name,
            size=len(data),
            mime=mime or guessed or "application/octet-stream",
            kind=kind,
        )
        self.blob_path(record).write_bytes(data)
        self.files[record.id] = record
        self._save()
        return record

    def write_doc(self, thread: str, title: str, content: str, filename: str | None = None) -> FileRecord:
        title = title.strip() or "Untitled"
        name = filename_for(title, filename)
        body = content if content.endswith("\n") else content + "\n"
        guessed, _ = mimetypes.guess_type(name)
        return self.save_bytes(
            thread,
            name,
            body.encode("utf-8"),
            kind="doc",
            mime=guessed or ("text/markdown" if name.endswith(".md") else "text/plain"),
        )

    def read_text(self, file_id: str, thread: str | None = None) -> str:
        record = self.get(file_id)
        if thread and record.thread != thread:
            raise FileError("that file is not in this chat")
        path = self.blob_path(record)
        if not path.is_file():
            raise FileError("missing file")
        suffix = Path(record.name).suffix.lower()
        if suffix not in TEXT_SUFFIXES and not record.mime.startswith("text/"):
            return f"{record.name} is binary ({record.size} bytes). Download it from the chat."
        return path.read_text(encoding="utf-8", errors="replace")[:20_000]

    def find_in_thread(self, thread: str, name_or_id: str) -> FileRecord:
        key = name_or_id.strip()
        if key in self.files and self.files[key].thread == thread:
            return self.files[key]
        matches = [item for item in self.list_thread(thread) if item.name == key]
        if not matches:
            raise FileError(f"no file named {key} in this chat")
        return matches[-1]
