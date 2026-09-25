# Node 01 — Triage note

## CONTRACT
- Reads: one raw note (text + optional timestamp/source), `context/brand.md`,
  `context/guardrails.md`, and a short list of recent/published post themes
  (for duplicate detection).
- Writes: a triage verdict object (see SHAPE). Nothing else. Does not draft
  a post.
- Gate that follows: if verdict is `DEVELOP`, the pipeline calls Node 02. If
  `SKIP`, the pipeline logs the verdict and stops — this is a normal,
  expected outcome, not a failure.

## JOB
Decide whether a single raw fragment is worth developing into a LinkedIn
post, and say why in one or two sentences.

## RULES
- Base the decision only on: the note's own content, whether it overlaps
  with a theme already published or already in `review_queue/`, and whether
  it contains enough of a concrete point to be developable (a specific
  observation, number, mechanism, or story beat — not just a mood).
- Do not invent detail that isn't in the note to make it sound more
  developable than it is.
- If the note is too thin, too vague, or purely personal/off-brand, verdict
  is `SKIP` — this is not a lesser outcome, it is the correct one.
- If the note substantially overlaps a theme already covered (see
  `context/brand.md` "what already works" and any themes passed in), verdict
  is `SKIP` with reason `duplicate`.
- Never claim a note is stronger evidence than it is (e.g. do not describe a
  two-line fragment as "a strong story" if it has no concrete detail).
- SCORE reflects only how developable the note is as-is (concreteness,
  brand fit, non-duplication) — never inflate it to justify a DEVELOP
  verdict, and never deflate a genuinely strong note to justify a SKIP.
  A thin/vague/duplicate note should score low (1-3) even if the verdict
  logic elsewhere is being lenient; a concrete, on-brand, non-duplicate
  note should score high (7-10).

## SHAPE
Return exactly this structure (plain text, one field per line):
```
VERDICT: DEVELOP | SKIP
SCORE: <integer 1-10, how developable this note is>
REASON: <one or two sentences, plain language, no hedging filler>
THEME: <short topic label, e.g. "pH transparency" or "ceramide barrier">
OVERLAPS_WITH: <theme it duplicates, or "none">
CONFIDENCE: HIGH | MEDIUM | LOW
```
