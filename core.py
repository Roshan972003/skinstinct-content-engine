"""
Shared triage/draft logic for the live webhook pipeline (api/webhook.py).

Reuses the same skill prompts and context files as the local demo pipeline
(pipeline.py) — the node contracts don't change just because notes now
arrive over Telegram/Supabase instead of local files. Deliberately kept as
plain functions (no framework) so a Vercel serverless function can import
this module directly.
"""
from __future__ import annotations

import re
from pathlib import Path

from adapters.model_adapter import ModelAdapter
from adapters.news_adapter import fetch_news_candidates

ROOT = Path(__file__).parent
CONTEXT_DIR = ROOT / "context"
SKILLS_DIR = ROOT / "skills"
VOICE_FILE = ROOT / "voice-skill.txt"


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
        if m and m.group(1) in {
            "VERDICT", "SCORE", "REASON", "THEME", "OVERLAPS_WITH", "CONFIDENCE",
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


def run_triage(model: ModelAdapter, note_text: str, known_themes: list[str], static_context: str) -> dict:
    node_prompt = read(SKILLS_DIR / "01-triage-note.md")
    prompt = (
        f"{node_prompt}\n\n"
        f"KNOWN_THEMES:\n{chr(10).join(known_themes) or '(none yet)'}\n\n"
        f"NOTE:\n{note_text}"
    )
    response = model.generate(static_context, prompt)
    fields = parse_fields(response.text)
    fields["_mocked"] = response.mocked
    fields["_raw"] = response.text
    return fields


def run_draft(model: ModelAdapter, note_text: str, triage: dict, static_context: str) -> dict:
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
        f"NOTE:\n{note_text}"
    )
    response = model.generate(static_context, prompt)
    fields = parse_fields(response.text)
    fields["_mocked"] = response.mocked
    fields["_raw"] = response.text
    fields["_news_count"] = len(news)
    return fields
