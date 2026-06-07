from __future__ import annotations

from io import BytesIO
from urllib.parse import quote

import httpx


class TelegramBotClientError(Exception):
    pass


class TelegramBotClient:
    def __init__(
        self,
        *,
        token: str,
        api_base_url: str,
        request_timeout_seconds: float,
    ) -> None:
        self.token = token
        self.api_base_url = api_base_url.rstrip("/")
        self.request_timeout_seconds = request_timeout_seconds

    def get_updates(self, *, offset: int | None, timeout_seconds: int) -> list[dict]:
        payload = {
            "timeout": timeout_seconds,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset

        response = self._request("getUpdates", json=payload)
        return response.get("result", [])

    def send_message(self, *, chat_id: int, text: str) -> None:
        self._request(
            "sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
        )

    def send_document(
        self,
        *,
        chat_id: int,
        file_name: str,
        content_bytes: bytes,
        caption: str | None = None,
    ) -> None:
        url = f"{self.api_base_url}/bot{quote(self.token, safe='')}/sendDocument"
        data = {
            "chat_id": str(chat_id),
        }
        if caption:
            data["caption"] = caption

        files = {
            "document": (
                file_name,
                BytesIO(content_bytes),
                "application/octet-stream",
            )
        }

        try:
            response = httpx.post(
                url,
                data=data,
                files=files,
                timeout=self.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TelegramBotClientError(f"Telegram API request failed for sendDocument: {exc}") from exc

        if not payload.get("ok"):
            raise TelegramBotClientError("Telegram API request returned ok=false for sendDocument")

    def get_file(self, *, file_id: str) -> dict:
        response = self._request(
            "getFile",
            json={
                "file_id": file_id,
            },
        )
        return response["result"]

    def download_file(self, *, file_path: str) -> bytes:
        url = f"{self.api_base_url}/file/bot{quote(self.token, safe='')}/{file_path.lstrip('/')}"

        try:
            response = httpx.get(url, timeout=self.request_timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TelegramBotClientError(f"Telegram file download failed: {exc}") from exc

        return response.content

    def _request(self, method: str, *, json: dict) -> dict:
        url = f"{self.api_base_url}/bot{quote(self.token, safe='')}/{method}"

        try:
            response = httpx.post(url, json=json, timeout=self.request_timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TelegramBotClientError(f"Telegram API request failed for {method}: {exc}") from exc

        if not payload.get("ok"):
            raise TelegramBotClientError(f"Telegram API request returned ok=false for {method}")

        return payload
