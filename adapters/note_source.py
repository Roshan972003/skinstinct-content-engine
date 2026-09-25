"""
Note input adapter.

The case's real trigger is a live Telegram bot on Meera's personal capture
channel. That bot does not exist yet (see DESIGN_BRIEF.md, Check 03 / The
Cut) — no TELEGRAM_BOT_TOKEN, no chat to poll, no webhook.

This adapter defines the interface the rest of the pipeline depends on,
independent of where a note actually comes from. Today it reads notes from
local files (fixtures or anything you drop in notes/inbox/). Once a bot
token exists, a TelegramNoteSource implementing the same interface can
replace FileNoteSource without changing pipeline.py, skills/, or the
adapters that come after it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass
class Note:
    id: str
    text: str
    source: str  # e.g. "file", "telegram" (future), "fixture"
    captured_at: str  # ISO timestamp; best-effort if unknown


class NoteSource:
    """Interface every note source must satisfy."""

    def fetch_new_notes(self) -> Iterable[Note]:
        raise NotImplementedError


class FileNoteSource(NoteSource):
    """
    Reads one note per .txt file from a directory. This is today's stand-in
    for "a message landed in Telegram" — drop a .txt file in, it's treated
    as a captured note.
    """

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def fetch_new_notes(self) -> Iterable[Note]:
        if not self.directory.exists():
            return []
        notes = []
        for path in sorted(self.directory.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            notes.append(
                Note(
                    id=path.stem,
                    text=text,
                    source=f"file:{path.name}",
                    captured_at=mtime.isoformat(),
                )
            )
        return notes


class TelegramNoteSource(NoteSource):
    """
    Not implemented. Placeholder so the interface and the missing
    dependency are explicit rather than silently absent.

    Wiring this for real needs, at minimum: TELEGRAM_BOT_TOKEN, the bot
    added to Meera's capture channel, and a decision on polling vs.
    webhook. All [PENDING] per the task's API-details list.
    """

    def __init__(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError(
                "TelegramNoteSource requires TELEGRAM_BOT_TOKEN, which is not "
                "configured. This is expected in v1 — see DESIGN_BRIEF.md "
                "'The Cut'. Use FileNoteSource until the bot is wired up."
            )
        # Intentionally not implemented further: no bot token exists to
        # test against, and guessing at Telegram API behavior would violate
        # "do not invent ... successful integration behavior."
        raise NotImplementedError(
            "Telegram polling/webhook is not implemented yet. Provide API "
            "details (bot token, chat id, polling vs. webhook) to complete "
            "this adapter."
        )

    def fetch_new_notes(self) -> Iterable[Note]:
        raise NotImplementedError
