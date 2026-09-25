# Skinstinct content workflow — v1

Turns a raw captured note into a review-ready LinkedIn draft in Meera's
voice, with a mandatory human gate before anything is ever posted. Start
with [`DESIGN_BRIEF.md`](DESIGN_BRIEF.md) — it explains *why* this scope and
not the full end-to-end version Meera originally described.

## What this is (and isn't)

**Is:** a note-in → triage → (optional current-angle lookup) → draft →
local review file pipeline, fully traceable back to source.

**Isn't:** connected to Meera's real Telegram channel, and does not post to
LinkedIn under any circumstance. Both are deliberate cuts — see
`DESIGN_BRIEF.md` → "The Cut."

## Setup

```bash
cd skinstinct-workflow
python3 -m venv venv        # or reuse the repo root's venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example ../.env     # or point at an existing .env with GEMINI_API_KEY
```

Edit `../.env` and set a real `GEMINI_API_KEY` to get live output. Without
one, the pipeline still runs, but every triage/draft result is clearly
labeled `MOCK MODE` — useful for checking the wiring without an API key.

## Run it

```bash
python pipeline.py
```

- If `notes/inbox/*.txt` has files, it processes those.
- Otherwise it falls back to the five demo fixtures in `notes/fixtures/`
  (explicitly invented for this demo — see `notes/fixtures/README.md`;
  they are not Meera's real notes, which were not supplied).
- Each note produces one file in `review_queue/`, containing: the original
  note verbatim, the triage verdict and reason, and — only if triaged
  `DEVELOP` — a draft, its rationale, a claims ledger (every factual claim
  and where it came from), and whatever news angle was or wasn't used.

Nothing is sent anywhere. Open the files in `review_queue/` and decide.

## How the human review gate works today

Output is written to local Markdown files. That's a placeholder — the
case leaves "draft delivery/review destination" `[PENDING]`. Meera opening
and reading a file *is* the review gate; approve/edit/reject/revise are
manual actions she takes outside this tool (edit the file, or use it as a
starting point and post herself). Swapping this for a Telegram reply, an
email digest, or a small web UI later does not require changing
`skills/` or the triage/draft logic — only `pipeline.py`'s `write_output`
step.

## Project layout

```
context/          brand facts, audience, and guardrails fed into every AI call
skills/            the two node prompts (triage, draft) — contract/job/rules/shape
adapters/          swappable interfaces: note input, model calls, news lookup
notes/inbox/       drop real notes here (one .txt per note)
notes/fixtures/    demo-only invented notes, used when inbox/ is empty
review_queue/      pipeline output — the human review gate
../voice-skill.txt the voice reference (source: Case 1 seed data, 15 pieces)
```

## Known limitations (also in DESIGN_BRIEF.md)

- No live Telegram trigger — `adapters/note_source.py`'s `TelegramNoteSource`
  raises `NotImplementedError` on purpose rather than guessing at bot
  behavior with no token to test against.
- The real 60-note corpus and 40 abandoned drafts described in the case
  were never supplied to this repository — dedupe/triage quality against
  Meera's actual backlog is unverified; it's only been run against the
  five invented fixture notes.
- Google News RSS lookups are best-effort and network-dependent; a run
  with no internet access will simply omit the current angle, as designed
  — this is expected, not a bug.
- `GEMINI_MODEL` defaults to `gemini-2.0-flash` but this has not been
  confirmed as the right/available model for this account — verify before
  trusting live output.
- No tests were added or run for this change, per the task's instructions;
  the checks performed were manual — reading the pipeline's own output
  files after a mock-mode run, and inspecting the news adapter against a
  live query by hand. That is not equivalent to automated test coverage.
