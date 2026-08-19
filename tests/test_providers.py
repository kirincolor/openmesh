from pathlib import Path

from fastapi.testclient import TestClient

from openmesh.config import load_config
from openmesh.providers import AccountIn, ProviderBook
from openmesh.server import create_app


HOUSE = """
mesh: {name: t, chief: chief}
provider:
  base_url: https://api.openai.com/v1
  api_key: sk-old
  model: gpt-4o-mini
agents:
  - {id: chief, name: Chief, role: lead, tools: [handoff]}
"""


def test_migrate_and_crud(tmp_path: Path) -> None:
    from openmesh.config import ProviderConfig

    book = ProviderBook(tmp_path)
    book.migrate_from(ProviderConfig(api_key="sk-old", model="gpt-4o-mini"))
    assert book.has_key()
    assert book.default() is not None
    first = book.add(AccountIn(name="DeepSeek", base_url="https://api.deepseek.com/v1", api_key="sk-ds", model="deepseek-chat"))
    assert first.id in {item["id"] for item in book.public()}
    assert not any("sk-ds" in str(item) for item in book.public())
    book.update(first.id, AccountIn(name="DS", model="deepseek-reasoner"))
    assert book.get(first.id).model == "deepseek-reasoner"
    book.delete(first.id)
    assert book.get(first.id) is None


def test_api_accounts_and_picker(tmp_path: Path) -> None:
    (tmp_path / "mesh.yaml").write_text(HOUSE, encoding="utf-8")
    client = TestClient(create_app(load_config(tmp_path)))
    state = client.get("/api/state").json()
    assert state["provider"]["has_key"] is True
    assert state["models"]["options"]
    assert all(isinstance(item, dict) and "id" in item for item in state["models"]["options"])
    res = client.post(
        "/api/providers",
        json={
            "name": "Groq",
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": "gsk-test",
            "model": "llama-3.3-70b-versatile",
        },
    )
    assert res.status_code == 200
    account_id = res.json()["account"]["id"]
    again = client.get("/api/state").json()
    labels = [item["label"] for item in again["models"]["options"]]
    assert any("Groq" in label for label in labels)
    assert "gsk-test" not in str(again)
    gone = client.delete(f"/api/providers/{account_id}")
    assert gone.status_code == 200
