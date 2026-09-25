#!/usr/bin/env python3
"""
Skinstinct content pipeline — v1 (see DESIGN_BRIEF.md for scope and why).

Trigger  -> a .txt note appears in notes/inbox/ (stand-in for a Telegram
            message; see adapters/note_source.py for why Telegram itself
            isn't wired yet)
Input    -> the note text + basic metadata
Context  -> context/brand.md, context/guardrails.md, voice-skill.txt,
            and themes already sitting in review_queue/ (dedupe)
Processing -> Node 01 (triage): DEVELOP or SKIP, with a reason
AI       -> Gemini, via adapters/model_adapter.py (falls back to a labeled
            mock if no API key is configured)
Output   -> a Markdown package in review_queue/, containing the draft (if
            any), the full rationale, the claims ledger, and the original
            note — nothing is sent, posted, or published by this script.

Run:
    python pipeline.py
"""
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

from adapters.note_source import FileNoteSource, Note
from adapters.model_adapter import ModelAdapter
from adapters.news_adapter import fetch_news_candidates

ROOT = Path(__file__).parent
NOTES_INBOX = ROOT / "notes" / "inbox"
NOTES_FIXTURES = ROOT / "notes" / "fixtures"
REVIEW_QUEUE = ROOT / "review_queue"
CONTEXT_DIR = ROOT / "context"
SKILLS_DIR = ROOT / "skills"
VOICE_FILE = ROOT.parent / "voice-skill.txt"

load_dotenv(ROOT.parent / ".env")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_static_context() -> str:
    parts = [
        read(CONTEXT_DIR / "brand.md"),
        read(CONTEXT_DIR / "guardrails.md"),
        read(VOICE_FILE),
    ]
    return "\n\n".join(p for p in parts if p)


def existing_themes() -> list[str]:
    """Cheap dedupe signal: THEME: lines already written to review_queue/."""
    themes = []
    for path in REVIEW_QUEUE.glob("*.md"):
        text = read(path)
        for line in text.splitlines():
            if line.startswith("THEME:"):
                themes.append(line.split("THEME:", 1)[1].strip())
    return themes


def parse_fields(text: str) -> dict:
    """Parse the simple 'KEY: value' / 'KEY:\\n<block>' shape nodes return."""
    fields: dict[str, str] = {}
    current_key = None
    buffer: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^([A-Z_]+):\s*(.*)$", line)
        if m and m.group(1) in {
            "VERDICT", "REASON", "THEME", "OVERLAPS_WITH", "CONFIDENCE",
            "DRAFT", "RATIONALE", "CLAIMS_LEDGER", "NEWS_USED",
        }:
            if current_key:
                fields[current_key] = "\n".join(buffer).strip()
            current_key = m.group(1)
            buffer = [m.group(2)] if m.group(2) else []
        else:
            buffer.append(line)
    if current_key:
        fields[current_key] = "\n".join(buffer).strip()
    return fields


def run_triage(model: ModelAdapter, note: Note, static_context: str) -> dict:
    node_prompt = read(SKILLS_DIR / "01-triage-note.md")
    known_themes = existing_themes()
    prompt = (
        f"{node_prompt}\n\n"
        f"KNOWN_THEMES:\n{chr(10).join(known_themes) or '(none yet)'}\n\n"
        f"NOTE:\n{note.text}"
    )
    response = model.generate(static_context, prompt)
    fields = parse_fields(response.text)
    fields["_mocked"] = response.mocked
    fields["_raw"] = response.text
    return fields


def run_draft(model: ModelAdapter, note: Note, triage: dict, static_context: str) -> dict:
    node_prompt = read(SKILLS_DIR / "02-draft-post.md")
    news = fetch_news_candidates(triage.get("THEME", ""))
    news_block = (
        "\n".join(f"- {c.title} — {c.source}, {c.published} ({c.link})" for c in news)
        or "(no news candidates found — omit current angle, do not invent one)"
    )
    prompt = (
        f"{node_prompt}\n\n"
        f"TRIAGE_VERDICT:\n{triage.get('_raw', '')}\n\n"
        f"NEWS_CANDIDATES:\n{news_block}\n\n"
        f"NOTE:\n{note.text}"
    )
    response = model.generate(static_context, prompt)
    fields = parse_fields(response.text)
    fields["_mocked"] = response.mocked
    fields["_raw"] = response.text
    fields["_news_count"] = len(news)
    return fields


def write_output(note: Note, triage: dict, draft: dict | None) -> Path:
    REVIEW_QUEUE.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = REVIEW_QUEUE / f"{ts}__{note.id}.md"

    lines = [
        f"# Review item — note `{note.id}`",
        "",
        f"- Source: {note.source}",
        f"- Captured: {note.captured_at}",
        f"- Pipeline run: {ts}",
        f"- Model call mocked: {triage.get('_mocked')}",
        "",
        "## Original note (verbatim)",
        "```",
        note.text,
        "```",
        "",
        "## Triage",
        f"VERDICT: {triage.get('VERDICT', 'UNKNOWN')}",
        f"REASON: {triage.get('REASON', '')}",
        f"THEME: {triage.get('THEME', '')}",
        f"OVERLAPS_WITH: {triage.get('OVERLAPS_WITH', '')}",
        f"CONFIDENCE: {triage.get('CONFIDENCE', '')}",
        "",
    ]

    if draft is None:
        lines += ["## Draft", "_Skipped — not developed into a draft. See triage reason above._"]
    else:
        lines += [
            "## Draft (REQUIRES YOUR REVIEW — not published, not sent anywhere)",
            "",
            draft.get("DRAFT", "(model returned no draft text)"),
            "",
            "## Rationale",
            draft.get("RATIONALE", ""),
            "",
            "## Claims ledger",
            draft.get("CLAIMS_LEDGER", ""),
            "",
            "## News angle used",
            draft.get("NEWS_USED", ""),
            "",
            f"_News candidates considered: {draft.get('_news_count', 0)}_",
        ]

    lines += [
        "",
        "---",
        "**Human review gate.** Nothing above has been posted or sent.",
        "Approve, edit, reject, or request a revision yourself before this",
        "goes anywhere near LinkedIn.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    model = ModelAdapter()
    if not model.is_live:
        print(
            "NOTE: no live GEMINI_API_KEY/model configured — running in MOCK "
            "MODE. Output will be clearly labeled as mocked, not a real "
            "triage/draft result.\n"
        )

    inbox = NOTES_INBOX if any(NOTES_INBOX.glob("*.txt")) else NOTES_FIXTURES
    if inbox is NOTES_FIXTURES:
        print(f"notes/inbox/ is empty — using demo fixtures in {NOTES_FIXTURES}\n")

    notes = list(FileNoteSource(inbox).fetch_new_notes())
    if not notes:
        print("No notes found. Drop .txt files into notes/inbox/ and re-run.")
        return

    static_context = build_static_context()

    for note in notes:
        print(f"--- Processing note: {note.id} ---")
        triage = run_triage(model, note, static_context)
        verdict = triage.get("VERDICT", "").strip().upper()
        print(f"  VERDICT: {verdict or 'UNKNOWN'} — {triage.get('REASON', '')}")

        draft = None
        if verdict == "DEVELOP":
            draft = run_draft(model, note, triage, static_context)

        out_path = write_output(note, triage, draft)
        print(f"  -> {out_path.relative_to(ROOT.parent)}\n")


if __name__ == "__main__":
    main()
