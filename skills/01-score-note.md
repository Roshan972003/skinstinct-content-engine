# Node 01 — Score note

## CONTRACT
- Reads: one raw note (text, and how it arrived — typed or transcribed from
  voice), `context/brand.md`, `context/guardrails.md`.
- Writes: a score object (see SHAPE). Nothing else. Does not draft a post.
- Gate that follows: score 6-10 continues to Node 02 (draft). Score 0-5
  stops here — Meera gets the score and reason, nothing more. This is a
  normal, expected outcome, not a failure.

## JOB
Score the note 0-10 against Meera's master theme: the gap between what a
label or marketing claim says and what the formulation actually does. Give
a one-line reason. Also extract a 3-5 word search phrase suitable for a
news search, if the note has a topic a current news item could plausibly
speak to (otherwise leave it empty).

## RULES
- A specific claim, number, mechanism, or lived experience (hers or a
  customer's) scores high (7-10).
- A logistics reminder, a task, a topic brief with no concrete point yet,
  or an abandoned fragment with no developable content scores low (0-3).
- A note that's on-topic but thin, generic, or missing a concrete anchor
  scores in the middle (4-6).
- Do not invent detail that isn't in the note to justify a higher score.
- Do not deflate a genuinely concrete, on-brand note to justify a lower
  score, and do not inflate a thin one to justify a higher score.
- NEWS_QUERY should be a real, searchable phrase (e.g. "niacinamide skincare
  regulation India") — never a vague word ("skincare") and never invented
  to force a match. Leave it blank if nothing in the note suggests a
  sensible news angle.

## SHAPE
Return exactly this structure (plain text, one field per line):
```
SCORE: <integer 0-10>
REASON: <one line, plain language, no hedging filler>
NEWS_QUERY: <3-5 word search phrase, or blank>
```
