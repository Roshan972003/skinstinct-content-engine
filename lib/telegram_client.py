"""Minimal Telegram Bot API client, via `requests`."""
from __future__ import annotations

import os

import requests

TIMEOUT_SECONDS = 10


class TelegramError(RuntimeError):
    pass


def _post(method: str, payload: dict) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN not configured")
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )
    data = resp.json()
    if not resp.ok or not data.get("ok"):
        raise TelegramError(f"{method} failed: {resp.status_code} {data}")
    return data["result"]


def send_message(text: str, chat_id: int | str | None = None, reply_markup: dict | None = None) -> dict:
    target_chat = chat_id if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID")
    if not target_chat:
        raise TelegramError("No chat_id given and TELEGRAM_CHAT_ID not configured")
    payload = {"chat_id": target_chat, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return _post("sendMessage", payload)


def edit_message_text(chat_id: int | str, message_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    payload["reply_markup"] = reply_markup if reply_markup is not None else {"inline_keyboard": []}
    return _post("editMessageText", payload)


def answer_callback_query(callback_query_id: str, text: str | None = None) -> dict:
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    return _post("answerCallbackQuery", payload)


def decision_keyboard(pending_id: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "✅ Approve & publish", "callback_data": f"approve:{pending_id}"},
            {"text": "↻ Regenerate", "callback_data": f"regenerate:{pending_id}"},
            {"text": "❌ Discard", "callback_data": f"discard:{pending_id}"},
        ]]
    }


def get_telegram_file_path(file_id: str) -> str:
    result = _post("getFile", {"file_id": file_id})
    return result["file_path"]


def download_telegram_file(file_path: str) -> bytes:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN not configured")
    resp = requests.get(f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=TIMEOUT_SECONDS)
    if not resp.ok:
        raise TelegramError(f"file download failed: {resp.status_code}")
    return resp.content
