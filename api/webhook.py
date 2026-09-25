"""
Telegram webhook entrypoint (Vercel Python serverless function).

Flow:
  channel_post (new note, no reply_to_message)
    -> insert into `notes`
    -> triage (Gemini) -> if DEVELOP, draft (Gemini + news)
    -> insert into `drafts`
    -> sendMessage back to the channel with the draft + "Reply APPROVE or
       REJECT to this message" -> store that message's id so the reply can
       be matched back to this draft

  channel_post with reply_to_message, text APPROVE/REJECT (case-insensitive)
    -> look up the draft whose telegram_reply_message_id equals
       reply_to_message.message_id -> flip its status

Every other update type (my_chat_member, edited_message, a plain private
message to the bot, etc.) is acknowledged with 200 and otherwise ignored —
Telegram retries a webhook that doesn't return 200, so failures must not be
silently swallowed as "did nothing" without a 200 response.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.model_adapter import ModelAdapter  # noqa: E402
from core import build_static_context, run_draft, run_triage  # noqa: E402
from lib.supabase_client import SupabaseClient, SupabaseError  # noqa: E402
from lib.telegram_client import TelegramError, send_message  # noqa: E402

DECISION_WORDS = {"APPROVE": "approved", "REJECT": "rejected"}


def get_known_themes(db: SupabaseClient, limit: int = 50) -> list[str]:
    rows = db.select("notes", order="created_at.desc", limit=limit, select="theme")
    return [r["theme"] for r in rows if r.get("theme")]


def get_voice_skill_override(db: SupabaseClient) -> str | None:
    try:
        rows = db.select("voice_skill", match={"id": 1}, select="content")
        return rows[0]["content"] if rows else None
    except SupabaseError:
        return None


def handle_decision(db: SupabaseClient, reply_to_message_id: int, decision_text: str) -> None:
    word = decision_text.strip().upper()
    status = DECISION_WORDS.get(word)
    if not status:
        return  # a reply that isn't literally APPROVE/REJECT — leave the draft pending

    drafts = db.select("drafts", match={"telegram_reply_message_id": reply_to_message_id})
    if not drafts:
        return  # reply to something that isn't a tracked draft message

    db.update(
        "drafts",
        match={"id": drafts[0]["id"]},
        fields={"status": status, "decided_at": datetime.now(timezone.utc).isoformat()},
    )


def handle_new_note(db: SupabaseClient, chat_id: int, message_id: int, text: str) -> None:
    note = db.insert(
        "notes",
        {
            "telegram_message_id": message_id,
            "telegram_chat_id": chat_id,
            "text": text,
        },
    )

    model = ModelAdapter()
    static_context = build_static_context(get_voice_skill_override(db))
    known_themes = get_known_themes(db)

    triage = run_triage(model, text, known_themes, static_context)
    verdict = (triage.get("VERDICT") or "").strip().upper()

    db.update(
        "notes",
        match={"id": note["id"]},
        fields={
            "verdict": verdict or None,
            "reason": triage.get("REASON"),
            "theme": triage.get("THEME"),
            "overlaps_with": triage.get("OVERLAPS_WITH"),
            "confidence": triage.get("CONFIDENCE"),
            "model_mocked": bool(triage.get("_mocked")),
            "raw_triage_response": triage.get("_raw"),
        },
    )

    if verdict != "DEVELOP":
        send_message(
            f"Skipped: {triage.get('REASON', '(no reason given)')}",
            chat_id=chat_id,
        )
        return

    draft = run_draft(model, text, triage, static_context)
    draft_row = db.insert(
        "drafts",
        {
            "note_id": note["id"],
            "draft_text": draft.get("DRAFT"),
            "rationale": draft.get("RATIONALE"),
            "claims_ledger": draft.get("CLAIMS_LEDGER"),
            "news_used": draft.get("NEWS_USED"),
            "news_candidate_count": draft.get("_news_count", 0),
            "model_mocked": bool(draft.get("_mocked")),
            "raw_draft_response": draft.get("_raw"),
            "telegram_chat_id": chat_id,
        },
    )

    sent = send_message(
        f"{draft.get('DRAFT', '(model returned no draft text)')}\n\n"
        "---\nReply APPROVE or REJECT to this message.",
        chat_id=chat_id,
    )
    db.update(
        "drafts",
        match={"id": draft_row["id"]},
        fields={"telegram_reply_message_id": sent["message_id"]},
    )


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
        got_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if expected_secret and got_secret != expected_secret:
            self._respond(401, {"ok": False, "error": "bad secret token"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            update = json.loads(raw_body or b"{}")
        except json.JSONDecodeError:
            self._respond(400, {"ok": False, "error": "invalid json"})
            return

        # Known trap: channel posts arrive as `channel_post`, not `message`.
        message = update.get("channel_post") or update.get("message")
        if not message or "text" not in message:
            self._respond(200, {"ok": True, "skipped": "no message/channel_post text"})
            return

        chat_id = message["chat"]["id"]
        allowed_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if allowed_chat_id and str(chat_id) != str(allowed_chat_id):
            self._respond(200, {"ok": True, "skipped": "chat_id not the configured capture channel"})
            return

        try:
            db = SupabaseClient()
            reply_to = message.get("reply_to_message")
            if reply_to:
                handle_decision(db, reply_to["message_id"], message["text"])
            else:
                handle_new_note(db, chat_id, message["message_id"], message["text"])
            self._respond(200, {"ok": True})
        except (SupabaseError, TelegramError) as exc:
            print(f"webhook error: {exc}", file=sys.stderr)
            self._respond(200, {"ok": False, "error": str(exc)})
        except Exception:
            print(traceback.format_exc(), file=sys.stderr)
            self._respond(200, {"ok": False, "error": "internal error, see logs"})

    def _respond(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)
