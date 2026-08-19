from __future__ import annotations

from typing import Any

import httpx

from .config import ProviderConfig


class LLMError(RuntimeError):
    pass


class LLM:
    def __init__(self, provider: ProviderConfig) -> None:
        self.provider = provider
        self._client = httpx.Client(timeout=180.0)

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        account: ProviderConfig | None = None,
    ) -> dict[str, Any]:
        cfg = account or self.provider
        if not cfg.api_key:
            raise LLMError("Missing API key. Open Settings and add an API account.")
        body: dict[str, Any] = {
            "model": model or cfg.model,
            "messages": messages,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        url = cfg.base_url.rstrip("/") + "/chat/completions"
        try:
            response = self._client.post(
                url,
                headers={
                    "Authorization": f"Bearer {cfg.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMError(public_llm_error(exc.response.status_code, exc.response.text)) from exc
        except httpx.HTTPError as exc:
            raise LLMError(public_llm_error(None, str(exc))) from exc
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise LLMError(f"Empty LLM response: {data!r}")
        return choices[0]["message"]


AUTH_MARKERS = (
    "401",
    "403",
    "invalid_api_key",
    "authentication",
    "unauthorized",
    "incorrect api key",
    "invalid api key",
)


def public_llm_error(status: int | None, detail: str) -> str:
    blob = f"{status or ''} {detail}".lower()
    if any(marker in blob for marker in AUTH_MARKERS):
        return "Provider rejected the API key."
    if status:
        return f"LLM HTTP {status}"
    return "LLM request failed."
