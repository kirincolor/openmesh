import asyncio

from openmesh.bus import Bus, Event


def test_persists_and_reloads(tmp_path) -> None:
    path = tmp_path / "room.jsonl"

    async def run() -> None:
        bus = Bus(path)
        await bus.publish(Event(kind="user", sender="you", text="hi"))
        await bus.publish(Event(kind="status", sender="mesh", text="thinking"))

    asyncio.run(run())
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    reloaded = Bus(path)
    assert len(reloaded.events) == 1
    assert reloaded.events[0].text == "hi"


def test_clear_wipes_log(tmp_path) -> None:
    path = tmp_path / "room.jsonl"

    async def run() -> None:
        bus = Bus(path)
        await bus.publish(Event(kind="error", sender="mesh", text="LLM HTTP 401: invalid_api_key"))
        bus.clear()

    asyncio.run(run())
    assert Bus(path).events == []
    assert path.read_text(encoding="utf-8") == ""
