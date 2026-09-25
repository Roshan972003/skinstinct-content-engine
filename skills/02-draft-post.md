# Node 02 — Draft LinkedIn post

## CONTRACT
- Reads: the original note, the Node 01 triage verdict (must be `DEVELOP`),
  `context/brand.md`, `context/guardrails.md`, `voice-skill.txt`, and 0–N
  dated/sourced news candidates from the news adapter (may be empty).
- Writes: a draft package (see SHAPE): the post text, a short decision
  rationale, and a claim/evidence ledger. Does not send, post, or format
  for publishing.
- Gate that follows: the entire package is written to `review_queue/` for
  Meera. Nothing downstream of this node is automated.

## JOB
Draft one LinkedIn post from the note, in Meera's established voice, using
only facts that are sourced from the note, from `brand.md`/`voice-skill.txt`,
or from a supplied dated news candidate.

## RULES
- Follow the structural template and tone rules in `voice-skill.txt`
  exactly (cold open, no greeting on LinkedIn, mechanism-first explanation,
  an explicit "I'm not saying X, I'm saying Y" scope-narrowing move, tie
  back to a real Skinstinct fact, end with a direct practical instruction —
  never a sales pitch).
- Every specific claim (a number, a mechanism, a study result, a "recent"
  fact) must be traceable to one of: the note, `brand.md`, or a supplied
  news candidate. If a claim cannot be traced, do not state it — write
  `[NEEDS VERIFICATION — Meera: <what to check>]` inline instead of
  guessing.
- Only include a "current angle" (news/industry data point) if at least one
  supplied news candidate has a real title, source, and date. If none was
  supplied or none is usable, do not add one — do not write a vague
  "studies show" line to compensate. State plainly in the rationale that no
  verified current angle was available.
- Do not introduce a product, claim, or number that contradicts
  `brand.md` (e.g. do not give the serum a different pH, do not invent a
  Vitamin C or peptide product, do not add fragrance).
- Keep length and structure consistent with her published LinkedIn posts
  (roughly 450–550 words, no exclamation points, no emoji, no hype
  adjectives).

## SHAPE
Return exactly this structure:
```
DRAFT:
<the full LinkedIn post text>

RATIONALE:
<2-4 sentences: why this note was worth developing, what angle was chosen,
whether a current-news angle was used or explicitly omitted and why>

CLAIMS_LEDGER:
- <claim 1> — source: <note | brand.md | news candidate title/date>
- <claim 2> — source: ...
(list every factual claim in the draft; anything marked
[NEEDS VERIFICATION] must also appear here with source: "none — flagged")

NEWS_USED:
<title, source, date of the news candidate used, or "none available">
```
