"""
Telegram webhook handler logic. Framework-agnostic (takes headers + raw
body, returns a (dict, status) pair) so it can be wired up from Flask
(app.py) or tested directly without spinning up a server.

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

from adapters.model_adapter import ModelAdapter
from core import build_static_context, run_draft, run_triage
from lib.supabase_client import SupabaseClient, SupabaseError
from lib.telegram_client import (
    TelegramError,
    answer_callback_query,
    approve_reject_keyboard,
    edit_message_text,
    send_message,
)

DECISION_WORDS = {"APPROVE": "approved", "REJECT": "rejected"}
CALLBACK_ACTIONS = {"approve": "approved", "reject": "rejected"}


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
        draft.get("DRAFT", "(model returned no draft text)"),
        chat_id=chat_id,
        reply_markup=approve_reject_keyboard(draft_row["id"]),
    )
    db.update(
        "drafts",
        match={"id": draft_row["id"]},
        fields={"telegram_reply_message_id": sent["message_id"]},
    )


def handle_callback_query(db: SupabaseClient, callback_query: dict) -> None:
    data = callback_query.get("data", "")
    action, _, draft_id = data.partition(":")
    status = CALLBACK_ACTIONS.get(action)
    if not status or not draft_id:
        answer_callback_query(callback_query["id"], "Unrecognized action")
        return

    drafts = db.select("drafts", match={"id": draft_id})
    if not drafts:
        answer_callback_query(callback_query["id"], "Draft not found")
        return
    draft = drafts[0]

    db.update(
        "drafts",
        match={"id": draft_id},
        fields={"status": status, "decided_at": datetime.now(timezone.utc).isoformat()},
    )

    label = "✅ Approved" if status == "approved" else "❌ Rejected"
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    if chat_id and message_id:
        edit_message_text(
            chat_id,
            message_id,
            f"{draft.get('draft_text', '')}\n\n---\n{label}",
        )
    answer_callback_query(callback_query["id"], label)


def handle(headers, raw_body: bytes) -> tuple[dict, int]:
    expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    got_secret = headers.get("X-Telegram-Bot-Api-Secret-Token")
    if expected_secret and got_secret != expected_secret:
        return {"ok": False, "error": "bad secret token"}, 401

    try:
        update = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid json"}, 400

    callback_query = update.get("callback_query")
    if callback_query:
        try:
            handle_callback_query(SupabaseClient(), callback_query)
            return {"ok": True}, 200
        except (SupabaseError, TelegramError) as exc:
            print(f"webhook error: {exc}", file=sys.stderr)
            return {"ok": False, "error": str(exc)}, 200
        except Exception:
            print(traceback.format_exc(), file=sys.stderr)
            return {"ok": False, "error": "internal error, see logs"}, 200

    # Known trap: channel posts arrive as `channel_post`, not `message`.
    message = update.get("channel_post") or update.get("message")
    if not message or "text" not in message:
        return {"ok": True, "skipped": "no message/channel_post text"}, 200

    chat_id = message["chat"]["id"]
    allowed_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if allowed_chat_id and str(chat_id) != str(allowed_chat_id):
        return {"ok": True, "skipped": "chat_id not the configured capture channel"}, 200

    try:
        db = SupabaseClient()
        reply_to = message.get("reply_to_message")
        if reply_to:
            handle_decision(db, reply_to["message_id"], message["text"])
        else:
            handle_new_note(db, chat_id, message["message_id"], message["text"])
        return {"ok": True}, 200
    except (SupabaseError, TelegramError) as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return {"ok": False, "error": str(exc)}, 200
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        return {"ok": False, "error": "internal error, see logs"}, 200
