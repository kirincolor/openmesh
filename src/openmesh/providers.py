from __future__ import annotations

import json
import uuid
from pathlib import Path

from pydantic import BaseModel

from .config import ProviderConfig


class Account(BaseModel):
    id: str
    name: str
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"


class AccountIn(BaseModel):
    name: str
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    model: str = "gpt-4o-mini"


class ProviderBook:
    def __init__(self, root: Path) -> None:
        self.path = root / "data" / "providers.json"
        self.accounts: list[Account] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.accounts = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.accounts = []
            return
        self.accounts = [Account.model_validate(item) for item in raw.get("accounts") or []]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"accounts": [item.model_dump() for item in self.accounts]}, indent=2) + "\n",
            encoding="utf-8",
        )

    def migrate_from(self, provider: ProviderConfig) -> None:
        if self.accounts:
            return
        if not provider.api_key:
            return
        self.accounts.append(
            Account(
                id="default",
                name="Default",
                base_url=provider.base_url or "https://api.openai.com/v1",
                api_key=provider.api_key,
                model=provider.model or "gpt-4o-mini",
            )
        )
        self.save()

    def get(self, account_id: str) -> Account | None:
        for item in self.accounts:
            if item.id == account_id:
                return item
        return None

    def default(self) -> Account | None:
        for item in self.accounts:
            if item.api_key:
                return item
        return self.accounts[0] if self.accounts else None

    def has_key(self) -> bool:
        return any(item.api_key for item in self.accounts)

    def public(self) -> list[dict]:
        return [
            {
                "id": item.id,
                "name": item.name,
                "base_url": item.base_url,
                "model": item.model,
                "has_key": bool(item.api_key),
            }
            for item in self.accounts
        ]

    def options(self) -> list[dict]:
        return [
            {
                "id": item.id,
                "label": f"{item.name} · {item.model}",
                "model": item.model,
            }
            for item in self.accounts
        ]

    def to_config(self, account: Account) -> ProviderConfig:
        return ProviderConfig(base_url=account.base_url, api_key=account.api_key, model=account.model)

    def add(self, body: AccountIn) -> Account:
        name = body.name.strip() or "API"
        account = Account(
            id=uuid.uuid4().hex[:8],
            name=name,
            base_url=body.base_url.strip() or "https://api.openai.com/v1",
            api_key=(body.api_key or "").strip(),
            model=body.model.strip() or "gpt-4o-mini",
        )
        self.accounts.append(account)
        self.save()
        return account

    def update(self, account_id: str, body: AccountIn) -> Account:
        account = self.get(account_id)
        if account is None:
            raise KeyError(account_id)
        account.name = body.name.strip() or account.name
        account.base_url = body.base_url.strip() or account.base_url
        if body.api_key:
            account.api_key = body.api_key.strip()
        account.model = body.model.strip() or account.model
        self.save()
        return account

    def delete(self, account_id: str) -> None:
        before = len(self.accounts)
        self.accounts = [item for item in self.accounts if item.id != account_id]
        if len(self.accounts) == before:
            raise KeyError(account_id)
        self.save()
