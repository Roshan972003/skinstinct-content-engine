"""
Shared score/draft logic for the live webhook pipeline (webhook_logic.py).

Deliberately kept as plain functions (no framework) so a Vercel serverless
function can import this module directly.
"""
from __future__ import annotations

import re
from pathlib import Path

from adapters.model_adapter import ModelAdapter

ROOT = Path(__file__).parent
CONTEXT_DIR = ROOT / "context"
SKILLS_DIR = ROOT / "skills"
VOICE_FILE = ROOT / "voice-skill.txt"

FIELD_NAMES = {"SCORE", "REASON", "NEWS_QUERY", "DRAFT", "NEWS_USED"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_static_context(voice_skill_override: str | None = None) -> str:
    voice = voice_skill_override if voice_skill_override is not None else read(VOICE_FILE)
    parts = [read(CONTEXT_DIR / "brand.md"), read(CONTEXT_DIR / "guardrails.md"), voice]
    return "\n\n".join(p for p in parts if p)


def parse_fields(text: str) -> dict:
    """Parse the simple 'KEY: value' / 'KEY:\\n<block>' shape the nodes return."""
    fields: dict[str, str] = {}
    current_key = None
    buffer: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^([A-Z_]+):\s*(.*)$", line)
        if m and m.group(1) in FIELD_NAMES:
            if current_key:
                fields[current_key] = "\n".join(buffer).strip()
            current_key = m.group(1)
            buffer = [m.group(2)] if m.group(2) else []
        else:
            buffer.append(line)
    if current_key:
        fields[current_key] = "\n".join(buffer).strip()
    return fields


def run_score(model: ModelAdapter, note_text: str, static_context: str) -> dict:
    node_prompt = read(SKILLS_DIR / "01-score-note.md")
    prompt = f"{node_prompt}\n\nNOTE:\n{note_text}"
    response = model.generate(static_context, prompt)
    fields = parse_fields(response.text)
    fields["_mocked"] = response.mocked
    fields["_raw"] = response.text
    return fields


def run_draft(
    model: ModelAdapter,
    note_text: str,
    news_candidate,
    format_: str,
    static_context: str,
) -> dict:
    node_prompt = read(SKILLS_DIR / "02-draft-post.md")
    if news_candidate:
        news_block = (
            f"- {news_candidate.title} — {news_candidate.source}, "
            f"{news_candidate.published} ({news_candidate.link})\n"
            f"  Summary: {news_candidate.summary or '(none)'}"
        )
    else:
        news_block = "(no news candidate found — omit current angle, do not invent one)"

    prompt = (
        f"{node_prompt}\n\n"
        f"FORMAT: {format_}\n\n"
        f"NEWS_CANDIDATE:\n{news_block}\n\n"
        f"NOTE:\n{note_text}"
    )
    response = model.generate(static_context, prompt)
    fields = parse_fields(response.text)
    fields["_mocked"] = response.mocked
    fields["_raw"] = response.text
    return fields
