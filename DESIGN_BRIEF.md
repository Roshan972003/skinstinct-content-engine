# Case 1 — Meera / Skinstinct: Design Brief

Source evidence: `MESA_Case 01_Problem Statement.pdf` (case narrative) and
`MESA Case 1_Seed Data_Published.pdf` (the 15 voice-reference pieces, already
distilled into [`../voice-skill.txt`](../voice-skill.txt)). Where a number or
target is not stated in the case, it is marked **[ASSUMPTION]** rather than
presented as fact.

---

## 1. Automation Brief

**Pain**
Meera captures ideas constantly but almost none of them become posts.
- 60 raw fragments dropped into a personal Telegram channel over 8 months
  (≈2–3/week) — **zero** converted to a post.
- 40 Google Drive drafts, most abandoned within the first two paragraphs.
- The pieces that *did* get published took her 90 minutes to 3 hours each,
  and by her own account that time was "stall time," not writing time.
- She hired a content writer for 6 weeks. Output was clean and accurate but
  not in her voice; she spent more time rewriting than she would have spent
  writing from scratch, and stopped after 4 posts.
- Net result: 6,200 LinkedIn followers, but no post in 11 weeks — despite
  evidence that her voice works (4 posts → 47,000 combined impressions; her
  last post → 340 profile visits in 48 hours and 3 wholesale enquiries).

The cost is opportunity cost, not a hard cash figure: proven top-of-funnel
demand (profile visits, wholesale enquiries) is going uncollected because the
bottleneck is turning a raw observation into a first draft, not distribution
or audience.

**User**
Meera Pillai — solo founder. She is simultaneously the only capturer, the
only voice reference, the only reviewer, and the only publisher. There is no
content team and no second reviewer described in the case.

**Outcome**
Stated target (her words): "three posts a week, without it consuming her
time." That is a goal she has set, not a validated business metric, so
success should be tracked on two layers:
- **Process metrics the system can actually see:** notes triaged/week,
  drafts reaching her review queue/week, her approve/edit/reject rate, time
  from note capture to a reviewable draft. **[ASSUMPTION: initial target —
  a steady flow of 3–5 draft candidates/week is enough to sustain 3
  posts/week after her edits.]**
- **Outcome metrics the system cannot see or own:** posts actually
  published, impressions, profile visits, wholesale enquiries. These stay
  under Meera's control because publishing stays manual (see Check 7). The
  system can only be judged on whether it gets a good draft in front of her
  fast enough to act on — not on whether she posts it.

**Journey Today**
1. Something happens (a manufacturing observation, a customer DM, an 11pm
   read) → she drops a note into her personal Telegram channel. This step
   works and she does not want it changed.
2. The note sits there. Nothing acts on it.
3. Occasionally she opens a Google Doc to develop one into a post.
4. She writes a couple of lines, decides it isn't good enough, closes the
   doc. ("By the time I come back to it two weeks later, the moment has
   passed.") → 40 stalled drafts.
5. Rarely, she pushes one all the way through unassisted → 4 posts in 8
   months, each costing 90 min–3 hrs of stall time.
6. She tried outsourcing step 3–5 to a hired writer. The output required
   more rewriting than writing from scratch because it wasn't in her voice
   → she cancelled after 4 posts.
7. Two no-code consultants proposed automating the entire journey, including
   publishing. She declined both — she wants to keep the final judgment call.

---

## 2. The Nine Checks

### Kill switches — any "No" means do not build that scope

**01 — Problem Real — PASS**
*Evidence:* 60 unconverted Telegram fragments, 40 abandoned drafts, 11 weeks
of silence, a failed 6-week writer engagement that made things worse, not
better.
*Rationale:* This is documented, repeated, and ongoing — not a one-off
complaint.
*Scope implication:* Build is justified.

**02 — Workflow Repeated — PASS**
*Evidence:* She captures 2–3 notes/week as an ongoing habit she explicitly
does not want to change; her target cadence (3 posts/week) is also
recurring, not a single campaign.
*Rationale:* A recurring input feeding a recurring output is exactly the
shape automation should target.
*Scope implication:* Build a standing pipeline, not a one-time script.

**03 — Input Available — CONDITIONAL (splits the scope)**
*Evidence:*
- `published/` — the 15 self-written pieces (4 LinkedIn + 11 newsletters) —
  **is** available now and has already been distilled into
  [`voice-skill.txt`](../voice-skill.txt). This input is real and usable
  today.
- `notes/` — the 60 raw Telegram fragments described in the case — is
  **not** present as actual files in this repository or session. Only the
  case narrative describes them.
- A live Telegram bot connected to her real capture channel does not exist
  yet — the case's own action item for the student is "create a Telegram
  account and one bot," i.e. this is infrastructure to be built, not an
  input that exists today.
- A live news/industry-data source is not yet wired to anything.
- A model API key exists in this repository, but it was provisioned for a
  different app (`Pre-Read Companion`) — its availability for this
  workflow is not confirmed, and the model name/version to use is
  unconfirmed.
*Rationale:* This check is a kill switch, and it genuinely fails for the
**live, end-to-end, Telegram-triggered** version of the workflow — that
cannot be built today because its primary input source is not connected.
It does **not** fail for the **drafting-and-triage engine** built on the
voice reference, which is real, present, and sufficient to build and
demonstrate against.
*Scope implication:* This is the check that drives **The Cut** below —
build the engine now, behind an interface that accepts notes however they
arrive; wire the live Telegram trigger only once the bot token exists.

### Sizing — any "No" means build something smaller

**04 — Output Valuable — PASS**
*Evidence:* Her own writing, in her own voice, has already converted
attention into business outcomes (340 profile visits/48h, 3 wholesale
enquiries from one post). She explicitly asked for drafts "ready for her to
look at" — she has already told us she would act on this output, in
contrast to the writer's drafts, which she rejected.
*Rationale:* A draft she can approve, edit, or reject in her own voice is a
qualitatively different (and higher-value) artifact than a generic AI post.
*Scope implication:* Full-quality drafting is worth building; a "just
summarize the note" shortcut is not — the value is specifically in
voice-matched, review-ready drafts.

**05 — Impact Measurable — CONDITIONAL**
*Evidence:* The case gives no built-in analytics pipeline back from
LinkedIn into this system.
*Rationale:* Process metrics (notes triaged, drafts produced, her approval
rate, time-to-draft) are directly measurable by the tool. Outcome metrics
(impressions, profile visits, enquiries) are only knowable if Meera reports
them back or connects LinkedIn analytics separately — out of scope for v1.
*Scope implication:* Instrument the process metrics now
**[ASSUMPTION: targets, not case facts]**; treat outcome metrics as a
future, opt-in feedback loop, not a v1 dependency.

**08 — ROI Worth It — CONDITIONAL / assumption-dependent**
*Evidence:* No cost figures are given for building or running this. Revenue
context (₹14–16 lakh/month) establishes the business is real and funded,
but no explicit budget for this tool is stated.
*Rationale:* Build cost for the scope in this brief is low (a Gemini call
per note/draft plus a free RSS lookup); the demonstrated upside of even one
good post (3 wholesale enquiries) plausibly clears that bar, but this is an
inference, not a stated ROI figure.
*Scope implication:* Keep the build cheap and adapter-based so cost stays
low regardless of how the ROI question is ultimately answered
**[ASSUMPTION]**.

### Boundary — any "No" means the human keeps that judgment or action

**06 — Failure Risk OK — CONDITIONAL, and this drives the guardrail design**
*Evidence:* Meera's entire brand differentiator is scientific precision (pH
levels, actives, clinical data). The case explicitly warns the workflow
"must not invent product claims, clinical evidence, statistics, citations,
or news."
*Rationale:* Two different risk tiers exist here, and they need different
treatment:
  - Wrongly recommending a weak note as worth developing → low cost,
    reversible in seconds (she skips it at the review gate).
  - A fabricated or unverifiable scientific/clinical claim slipping into a
    draft and being approved without scrutiny → high cost and hard to
    reverse once posted, and directly undermines the credibility the whole
    brand is built on.
*Scope implication:* Failure risk is acceptable **only if** every claim in
a draft is traceable to the source note, to `voice-skill.txt`'s established
facts, or to a cited, dated external source — anything else must be
flagged, not asserted. This is enforced in the node contracts, not left to
the model's discretion.

**07 — Judgment Protected — PASS (by design requirement)**
*Evidence:* Meera declined two consultants' end-to-end automation proposals
specifically because they removed her from the loop.
*Rationale:* The case treats this as non-negotiable, not a trade-off to
weigh.
*Scope implication:* No path in this system reaches LinkedIn, sends an
external message, or takes any consequential action without an explicit,
visible human approval step. This is a hard architectural constraint, not a
configurable option.

**09 — Owner Clear — PASS**
*Evidence:* Meera is the sole founder, sole capturer, sole reviewer, and
sole LinkedIn account holder in the case.
*Rationale:* No approvals-by-committee, no ambiguity about who signs off.
*Scope implication:* Single-reviewer design is sufficient — no multi-user
approval workflow is needed for v1.

---

## 3. The Cut

**Which check killed the scope:** Check 03 — Input Available.

Meera's full stated wish is an always-on pipeline: a message lands in her
real Telegram channel → the system reacts immediately → pulls in a live
news/industry angle → produces a draft, with no manual step to get a note
*into* the system. That live, end-to-end trigger path cannot be built today
because its inputs — a connected Telegram bot, a wired news source, and a
confirmed model configuration for this workflow — do not exist yet in this
repository or session. Under the stated rule ("Checks 1–3 are kill
switches: a No means do not build that scope"), that live-trigger scope is
cut from v1.

**What is cut, specifically:**
- Automatic, always-on listening on Meera's real Telegram channel (webhook
  or polling loop that reacts to new messages with no manual step).
- Live fetching of a news/industry-data angle wired unconditionally into
  every draft.
- Any path to LinkedIn itself — not deferred as "pending API," but
  structurally excluded as an action this system is ever allowed to take
  on its own, per Check 07.

**What remains — the safer, smaller v1 that the available evidence
supports:**
A drafting-and-triage engine that:
- Accepts a note through a simple, swappable input interface (a file, a
  pasted string, or — once available — a live Telegram adapter behind the
  same interface, so wiring the real bot later requires no change to the
  core logic).
- Triages it against Meera's voice/brand context and flags duplicates
  against known published themes, using the one input source that *is*
  available now (`voice-skill.txt`).
- Attempts a **best-effort, clearly-labeled** current-angle lookup via
  Google News RSS (public, keyless, so it does not require an
  unprovisioned API) and omits the angle entirely, with a visible note,
  if nothing verifiable is found — rather than inventing one.
- Produces a draft with every claim traceable to the note, to
  `voice-skill.txt`, or to a dated source link, with unverifiable claims
  explicitly flagged for Meera.
- Writes the draft plus its full evidence trail to a local review queue —
  the "review gate" — that Meera opens and acts on herself. Nothing beyond
  this point is automated.

---

## 4. Components Map

Legend: **●** = handoff to the next actor/stage. Cells marked
*(unavailable — pending)* are conceptual only per the case's own
`[PENDING]` list and are not implemented as live integrations in this
build.

| Actor | Trigger | Input | Context | Processing | AI | Output |
|---|---|---|---|---|---|---|
| **Meera (Founder)** | Has an observation (manufacturing floor, customer DM, 11pm read) | Types a free-text note | Her own judgment / nothing structured yet | — | — | ● Sends note into her Telegram channel |
| **Telegram** | ● Receives Meera's message *(live bot — unavailable, pending token; v1 uses a file/paste adapter behind the same interface)* | Raw note text + timestamp/source metadata | — | Passes note through unchanged, preserved verbatim for traceability | — | ● Hands note to the pipeline as `Input` |
| **Pipeline / triage node** (not in template's actor list, but the connective tissue) | ● New note received | Note text + metadata | `voice-skill.txt` (voice/brand), published-theme list (dedupe), guardrail rules | Normalize note → check against recent/published themes → decide DEVELOP / SKIP with a written reason | ● Calls **Gemini** for the triage judgment | DEVELOP → continues to drafting; SKIP → logged with reason, nothing further happens |
| **Google News RSS** | ● Called only if note is DEVELOP | Search query derived from the note's topic | Public RSS feed (keyless) | Fetch candidate headlines, keep only ones with a real title/source/date | — | ● Returns 0–N dated, sourced candidates, or an explicit "no verified current angle" signal *(live network call implemented; treat as best-effort — omit rather than invent if it fails or returns nothing usable)* | 
| **Gemini** | ● Called by the pipeline for triage, and again for drafting if DEVELOP | Note + voice reference + guardrails + (if found) dated news candidates | System instructions built from `voice-skill.txt` + brand/guardrail context | Draft a LinkedIn post in Meera's voice; mark any claim not directly sourced from the note/voice file/news candidate as `[NEEDS VERIFICATION]` | Generates draft text + a short, auditable rationale (not hidden chain-of-thought) | ● Draft + rationale + full evidence trail passed to the Review Gate *(model call implemented behind an adapter; requires `GEMINI_API_KEY`/`GEMINI_MODEL` — falls back to a labeled mock if not configured)* |
| **Review Gate** | ● Draft package arrives | Draft, source note, triage rationale, any news source used, flagged claims | Meera's own judgment | Presents everything needed to decide, with nothing pre-approved | — | Meera **approves / edits / rejects / requests revision** — *this is the only path to anything leaving the system, and this build sends nothing further automatically* |

**Draft delivery/review destination:** `[PENDING]` per the case — v1
implements this as local files in `review_queue/` (draft + evidence, in
plain Markdown) since no review surface (chat reply, email, dashboard) has
been specified yet. This is a placeholder, chosen because it requires no
additional credentials and preserves full traceability; swapping it for a
Telegram reply, an email, or a small UI later does not require touching the
triage/draft logic.
