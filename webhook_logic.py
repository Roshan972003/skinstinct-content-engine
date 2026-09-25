"""
Telegram bot entrypoint (Vercel Python serverless function, wired up by
app.py). In short:

  /linkedin <note> or /newsletter <note>, or a voice note (transcribed,
  then asks which format) -> score gate (0-10) -> if >=6, news angle via
  Google News RSS -> draft in Meera's voice -> posted with
  Approve & publish / Regenerate / Discard buttons (or a plain
  APPROVE/REJECT reply also works) -> Approve commits a dated markdown
  file to a private GitHub archive repo.

Two kinds of Supabase state:
  - `pending_items` is a pure bridge across Telegram's stateless webhook
    calls, used only while a transcribed voice note waits for a format
    choice. Rows are deleted as soon as that's resolved.
  - `notes` and `drafts` are the permanent memory layer: every scored
    note is saved (whether it produced a draft or not), every draft is
    saved with a status that updates on Approve/Reject rather than being
    deleted — rejected notes/drafts are kept on purpose, as a record of
    what needs improving. The GitHub archive is where the actual approved
    text lands; these tables are the audit trail, not a replacement.

Known trap: channel posts arrive as `channel_post`, not `message`. Every
update this handler doesn't recognize is acknowledged with 200 and
otherwise ignored — Telegram retries a webhook that doesn't return 200,
and the bot must not respond outside its configured channel.
"""
from __future__ import annotations

import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone

from adapters.model_adapter import ModelAdapter
from adapters.news_adapter import NewsCandidate, fetch_top_news
from core import build_static_context, run_draft, run_score
from lib import github_client
from lib.supabase_client import SupabaseClient, SupabaseError
from lib.telegram_client import (
    TelegramError,
    answer_callback_query,
    decision_keyboard,
    download_telegram_file,
    edit_message_text,
    get_telegram_file_path,
    send_message,
)

SCORE_THRESHOLD = 6
FORMAT_COMMAND_RE = re.compile(r"^/(linkedin|newsletter)\b\s*(.*)$", re.IGNORECASE | re.DOTALL)
BARE_FORMAT_RE = re.compile(r"^/?(linkedin|newsletter)$", re.IGNORECASE)


def parse_score(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        return max(0, min(10, int(raw.strip().split()[0])))
    except (ValueError, IndexError):
        return None


def news_candidate_from_row(row: dict) -> NewsCandidate | None:
    if not row.get("news_headline"):
        return None
    return NewsCandidate(
        title=row["news_headline"],
        source=row.get("news_source") or "unspecified",
        published=row.get("news_published") or "",
        link=row.get("news_link") or "",
        summary=row.get("news_summary") or "",
    )


def render_citation(news: NewsCandidate) -> str:
    return f"NEWS SOURCE: {news.title}\nFROM: {news.source} {news.published}\nLINK: {news.link}"


def render_message(score: int | None, draft_text: str, news_used: bool, news: NewsCandidate | None) -> str:
    score_label = f"Score: {score}/10" if score is not None else "Score: n/a"
    text = f"{score_label}\n\n{draft_text}"
    if news_used and news:
        text += f"\n\n{render_citation(news)}\n\n▲ Check this before publishing — you are the author of this claim."
    return text


def render_final_copy(draft_text: str, news_used: bool, news: NewsCandidate | None) -> str:
    """The clean, publish-ready text sent as its own message on Approve — no
    score header, no internal review warning, just what she'd actually post."""
    text = draft_text
    if news_used and news:
        text += f"\n\n{render_citation(news)}"
    return text


def get_voice_skill_override(db: SupabaseClient) -> str | None:
    try:
        rows = db.select("voice_skill", match={"id": 1}, select="content")
        return rows[0]["content"] if rows else None
    except SupabaseError:
        return None


def run_pipeline(db: SupabaseClient, model: ModelAdapter, chat_id: int, format_: str, note_text: str) -> None:
    static_context = build_static_context(get_voice_skill_override(db))
    score_result = run_score(model, note_text, static_context)
    score = parse_score(score_result.get("SCORE"))
    reason = score_result.get("REASON", "") or "(no reason given)"
    news_query = (score_result.get("NEWS_QUERY") or "").strip()

    note_row = db.insert(
        "notes",
        {
            "text": note_text,
            "score": score,
            "score_reason": reason,
            "news_query": news_query or None,
            "telegram_chat_id": chat_id,
        },
    )

    if score is None or score < SCORE_THRESHOLD:
        score_label = f"Score: {score}/10" if score is not None else "Score: n/a"
        send_message(f"{score_label}\n{reason}", chat_id=chat_id)
        return

    news = fetch_top_news(news_query) if news_query else None

    draft_result = run_draft(model, note_text, news, format_, static_context)
    draft_text = draft_result.get("DRAFT", "(model returned no draft text)")
    news_used = news is not None and (draft_result.get("NEWS_USED") or "").strip().lower() == "yes"

    draft_row = db.insert(
        "drafts",
        {
            "note_id": note_row["id"],
            "format": format_,
            "draft_text": draft_text,
            "news_used": news_used,
            "news_headline": news.title if news else None,
            "news_source": news.source if news else None,
            "news_published": news.published if news else None,
            "news_link": news.link if news else None,
            "news_summary": news.summary if news else None,
            "telegram_chat_id": chat_id,
        },
    )

    text = render_message(score, draft_text, news_used, news)
    sent = send_message(text, chat_id=chat_id, reply_markup=decision_keyboard(draft_row["id"]))
    db.update("drafts", match={"id": draft_row["id"]}, fields={"telegram_message_id": sent["message_id"]})


def handle_voice(db: SupabaseClient, model: ModelAdapter, chat_id: int, message: dict) -> None:
    file_id = message["voice"]["file_id"]
    file_path = get_telegram_file_path(file_id)
    audio_bytes = download_telegram_file(file_path)
    transcript = model.transcribe(audio_bytes, mime_type="audio/ogg")

    if transcript.mocked:
        send_message(f"Couldn't transcribe that voice note.\n\n{transcript.text}", chat_id=chat_id)
        return

    sent = send_message(
        f"Transcribed:\n\n{transcript.text}\n\nReply with /linkedin or /newsletter to draft this.",
        chat_id=chat_id,
    )
    db.insert(
        "pending_items",
        {
            "stage": "awaiting_format",
            "note_text": transcript.text,
            "telegram_chat_id": chat_id,
            "telegram_message_id": sent["message_id"],
        },
    )


def handle_format_reply(db: SupabaseClient, model: ModelAdapter, chat_id: int, reply_to_message_id: int, format_: str) -> None:
    rows = db.select(
        "pending_items",
        match={"stage": "awaiting_format", "telegram_message_id": reply_to_message_id, "telegram_chat_id": chat_id},
    )
    if not rows:
        return
    note_text = rows[0]["note_text"]
    db.delete("pending_items", match={"id": rows[0]["id"]})
    run_pipeline(db, model, chat_id, format_, note_text)


def finalize_decision(db: SupabaseClient, model: ModelAdapter, row: dict, action: str) -> str:
    """action is one of approve / discard / regenerate. Returns a short status string."""
    chat_id = row["telegram_chat_id"]
    message_id = row.get("telegram_message_id")
    news = news_candidate_from_row(row)
    original_text = render_message(row.get("score"), row.get("draft_text") or "", bool(row.get("news_used")), news)
    now = datetime.now(timezone.utc).isoformat()

    if action == "approve":
        github_client.ensure_repo_exists()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = f"{row.get('format') or 'post'}/{timestamp}.md"
        content = f"# {(row.get('format') or 'post').capitalize()} post — {timestamp}\n\n{original_text}\n"
        file_url = github_client.commit_markdown_file(path, content, message=f"Add {row.get('format')} post {timestamp}")
        if message_id:
            edit_message_text(chat_id, message_id, f"{original_text}\n\n---\n✅ Approved & archived: {file_url}")
        final_copy = render_final_copy(row.get("draft_text") or "", bool(row.get("news_used")), news)
        send_message(f"✅ Final copy — ready to post:\n\n{final_copy}", chat_id=chat_id)
        db.update("drafts", match={"id": row["id"]}, fields={"status": "approved", "decided_at": now, "archive_url": file_url})
        return "Approved & archived"

    if action == "discard":
        if message_id:
            edit_message_text(chat_id, message_id, f"{original_text}\n\n---\n❌ Discarded")
        db.update("drafts", match={"id": row["id"]}, fields={"status": "rejected", "decided_at": now})
        return "Discarded"

    if action == "regenerate":
        if message_id:
            edit_message_text(chat_id, message_id, f"{original_text}\n\n---\n↻ Regenerating…")
        db.update("drafts", match={"id": row["id"]}, fields={"status": "regenerated", "decided_at": now})
        notes = db.select("notes", match={"id": row["note_id"]})
        note_text = notes[0]["text"] if notes else ""
        run_pipeline(db, model, chat_id, row.get("format") or "linkedin", note_text)
        return "Regenerating"

    return "Unrecognized action"


def handle_callback_query(db: SupabaseClient, model: ModelAdapter, callback_query: dict) -> None:
    data = callback_query.get("data", "")
    action, _, draft_id = data.partition(":")
    if action not in {"approve", "discard", "regenerate"} or not draft_id:
        answer_callback_query(callback_query["id"], "Unrecognized action")
        return

    rows = db.select("drafts", match={"id": draft_id, "status": "pending"})
    if not rows:
        answer_callback_query(callback_query["id"], "Draft not found")
        return

    status = finalize_decision(db, model, rows[0], action)
    answer_callback_query(callback_query["id"], status)


def handle_text_decision(db: SupabaseClient, model: ModelAdapter, chat_id: int, reply_to_message_id: int, text: str) -> None:
    word = text.strip().upper()
    action = {"APPROVE": "approve", "REJECT": "discard"}.get(word)
    if not action:
        return
    rows = db.select(
        "drafts",
        match={"status": "pending", "telegram_message_id": reply_to_message_id, "telegram_chat_id": chat_id},
    )
    if not rows:
        return
    finalize_decision(db, model, rows[0], action)


def handle(headers, raw_body: bytes) -> tuple[dict, int]:
    expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    got_secret = headers.get("X-Telegram-Bot-Api-Secret-Token")
    if expected_secret and got_secret != expected_secret:
        return {"ok": False, "error": "bad secret token"}, 401

    try:
        update = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid json"}, 400

    # Known trap: channel posts arrive as `channel_post`, not `message`.
    message = update.get("channel_post") or update.get("message")
    callback_query = update.get("callback_query")

    if not message and not callback_query:
        return {"ok": True, "skipped": "no message/channel_post/callback_query"}, 200

    allowed_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    source_chat_id = (
        message["chat"]["id"] if message else callback_query.get("message", {}).get("chat", {}).get("id")
    )
    if allowed_chat_id and source_chat_id is not None and str(source_chat_id) != str(allowed_chat_id):
        return {"ok": True, "skipped": "chat_id not the configured capture channel"}, 200

    # Figure out which (if any) action this update maps to before touching
    # Supabase/Gemini, so an update that matches nothing costs nothing.
    action = None
    if callback_query:
        action = ("callback", callback_query)
    elif "voice" in message:
        action = ("voice", message)
    else:
        text = message.get("text", "")
        reply_to = message.get("reply_to_message")
        bare_format = BARE_FORMAT_RE.match(text.strip()) if reply_to else None
        command_match = FORMAT_COMMAND_RE.match(text.strip())

        if reply_to and bare_format:
            action = ("format_reply", message["chat"]["id"], reply_to["message_id"], bare_format.group(1).lower())
        elif command_match and command_match.group(2).strip():
            action = (
                "command",
                message["chat"]["id"],
                command_match.group(1).lower(),
                command_match.group(2).strip(),
            )
        elif reply_to and text.strip().upper() in {"APPROVE", "REJECT"}:
            action = ("text_decision", message["chat"]["id"], reply_to["message_id"], text)

    if action is None:
        return {"ok": True, "skipped": "no recognized command"}, 200

    try:
        db = SupabaseClient()
        model = ModelAdapter()
        kind = action[0]

        if kind == "callback":
            handle_callback_query(db, model, action[1])
        elif kind == "voice":
            handle_voice(db, model, action[1]["chat"]["id"], action[1])
        elif kind == "format_reply":
            _, chat_id, reply_to_message_id, format_ = action
            handle_format_reply(db, model, chat_id, reply_to_message_id, format_)
        elif kind == "command":
            _, chat_id, format_, note_text = action
            run_pipeline(db, model, chat_id, format_, note_text)
        elif kind == "text_decision":
            _, chat_id, reply_to_message_id, text = action
            handle_text_decision(db, model, chat_id, reply_to_message_id, text)

        return {"ok": True}, 200
    except (SupabaseError, TelegramError, github_client.GitHubError) as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return {"ok": False, "error": str(exc)}, 200
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        return {"ok": False, "error": "internal error, see logs"}, 200
