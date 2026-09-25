# Skinstinct content bot

A Telegram bot that turns a raw captured note (typed or voice) into a
review-ready LinkedIn or newsletter draft in Meera's voice, with a
mandatory human gate before anything is ever committed.

`DESIGN_BRIEF.md` documents the original, narrower v1 scope this project
started from (a local-file demo with no live Telegram trigger). This has
since been superseded end-to-end by the live bot described below.

## What it does

1. Post `/linkedin <note>` or `/newsletter <note>` in the configured
   Telegram channel — or send a voice note, and the bot transcribes it and
   asks which format to draft.
2. **Score gate**: Gemini scores the note 0-10 against Meera's master
   theme (the gap between what a label/claim says and what the
   formulation actually does). Below 6, you get the score and reason —
   nothing more, no draft, nothing stored.
3. **News angle**: for a note that scores 6+, Gemini extracts a short
   search phrase and the bot checks Google News' public RSS feed for a
   real, dated result. The draft step is told to use it only if genuinely
   relevant.
4. **Draft**: Gemini writes the full post in Meera's voice
   (`voice-skill.txt`), following a six-step structure (anchor, why she's
   writing, mechanism, boundary, proof, close). If a news item was used,
   the bot — never the model — appends the citation block from the real
   fetched data, so a link can never be hallucinated.
5. **Approval**: the draft posts with **Approve & publish** /
   **Regenerate** / **Discard** buttons (or reply `APPROVE`/`REJECT`
   directly). Approve commits the piece as a dated markdown file to a
   private GitHub archive repo (created automatically on first use) —
   this is the only permanent record the app keeps. Discard/Regenerate
   leave no trace.

Nothing is ever posted to LinkedIn or anywhere else automatically —
publishing stays entirely manual, by design.

## Project layout

```
app.py              Vercel entrypoint (Flask) — routes /api/health, /api/webhook
health_logic.py      health check: confirms every required env var is set
webhook_logic.py      the whole bot: dispatch, score gate, draft, approval
core.py              shared score/draft functions (skill prompts + parsing)
context/             brand facts and guardrails fed into every AI call
skills/              the two node prompts (score, draft) — contract/job/rules/shape
adapters/            model calls (Gemini, incl. audio transcription), news lookup
lib/                 thin clients: Supabase (pending state), Telegram, GitHub
voice-skill.txt      the voice reference (source: Case 1 seed data, 15 pieces)
supabase/schema.sql  the one table (`pending_items`) that bridges stateless
                     webhook calls — not a permanent archive
```

## Setup

See `.env.example` for every required environment variable. This runs as
a Vercel Python function, so those are set as Vercel project environment
variables, not a local `.env` file.

Apply `supabase/schema.sql` once via the Supabase SQL Editor before first
use.

## Known limitations

- The real note history and 40 abandoned drafts described in the
  original case were never supplied to this repository — triage/draft
  quality against Meera's actual backlog is unverified.
- Google News RSS lookups are best-effort and network-dependent; no
  result found simply omits the current angle, as designed.
- No automated tests — verification has been manual (unit-style checks
  with faked Supabase/Telegram/GitHub clients, plus live end-to-end runs
  against the real Telegram channel and Supabase project).
