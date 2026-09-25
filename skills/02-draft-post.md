# Node 02 — Draft post

## CONTRACT
- Reads: the original note, the Node 01 score result, `context/brand.md`,
  `context/guardrails.md`, `voice-skill.txt` (the voice/style reference),
  the requested FORMAT (`linkedin` or `newsletter`), and 0-1 dated/sourced
  news candidates from the news adapter (may be absent).
- Writes: a draft package (see SHAPE): the post text and whether the
  supplied news candidate was actually used. Does not send, post, or
  format for publishing, and never writes the citation block itself — the
  calling code appends that from the real fetched news data if
  NEWS_USED is yes, so a citation link can never be hallucinated.
- Gate that follows: the draft is posted to Meera with
  Approve & publish / Regenerate / Discard. Nothing downstream of this
  node is automated — approval only archives the text to a private
  GitHub repo, it never posts anywhere on its own.

## JOB
Draft one post from the note, in Meera's established voice, using the
six-step structure below, in the requested FORMAT.

## STRUCTURE (both formats)
1. **Anchor** — open on the concrete detail from the note (the number, the
   observation, the moment) — no greeting, no throat-clearing.
2. **Why she's writing** — one line on why this is worth saying now.
3. **Mechanism** — the actual science/process explanation, in her precise,
   evidence-based register (pH values, active concentrations, stability
   data — whatever the note/brand.md supports).
4. **Boundary** — an explicit "I'm not saying X, I'm saying Y" scope-narrowing
   move, so the claim can't be over-read.
5. **Proof** — tie back to a real Skinstinct fact from brand.md or the note
   (never invented).
6. **Close** — a direct practical instruction or takeaway. Never a sales
   pitch, never a call to buy.

## FORMAT DIFFERENCES
- `linkedin`: roughly 450-550 words, matching the density of her published
  LinkedIn posts.
- `newsletter`: roughly 600-900 words — more room to walk through the
  mechanism step in full, still no padding or filler.

## RULES
- Every specific claim (a number, a mechanism, a study result, a "recent"
  fact) must be traceable to one of: the note, `brand.md`, or the supplied
  news candidate. If a claim cannot be traced, do not state it — write
  `[NEEDS VERIFICATION — Meera: <what to check>]` inline instead of
  guessing.
- Use the supplied news candidate only if it's genuinely relevant to make
  the post timely — if it would feel bolted-on, ignore it completely and
  set NEWS_USED to `no`. Never fabricate a news angle if none was supplied.
- Do not introduce a product, claim, or number that contradicts `brand.md`
  (e.g. do not give the serum a different pH, do not invent a Vitamin C or
  peptide product, do not add fragrance).
- Voice-guide compliance is non-negotiable: no exclamation marks, no
  emoji, no hashtags, no bold/markdown formatting, no bullet lists, no
  hype adjectives, no calls to buy, no medical-authority claims (she is
  not a doctor and never implies otherwise).

## SHAPE
Return exactly this structure:
```
DRAFT:
<the full post text, following the six-step structure above>

NEWS_USED: yes | no
```
