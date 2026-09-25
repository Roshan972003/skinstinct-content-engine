"""Minimal Telegram Bot API client — just sendMessage, via `requests`."""
from __future__ import annotations

import os

import requests

TIMEOUT_SECONDS = 10


class TelegramError(RuntimeError):
    pass


def send_message(text: str, chat_id: int | str | None = None) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN not configured")
    target_chat = chat_id if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID")
    if not target_chat:
        raise TelegramError("No chat_id given and TELEGRAM_CHAT_ID not configured")

    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": target_chat, "text": text},
        timeout=TIMEOUT_SECONDS,
    )
    data = resp.json()
    if not resp.ok or not data.get("ok"):
        raise TelegramError(f"sendMessage failed: {resp.status_code} {data}")
    return data["result"]
