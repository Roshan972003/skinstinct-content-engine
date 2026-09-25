# Guardrails — what this workflow must never do

These are enforced in the node prompts (`skills/`) and should be treated as
non-negotiable, not stylistic preferences.

1. **Never invent a product claim, clinical result, statistic, citation, or
   news item.** If a fact is not in the source note, in `brand.md`, or in a
   dated/sourced news candidate handed to the model, it must not appear in
   a draft as a stated fact. Mark it `[NEEDS VERIFICATION — Meera]` instead.
2. **Never contradict an established fact** in `brand.md` (e.g. do not
   invent a new pH value for the serum, do not claim a Vitamin C or peptide
   product exists, do not add fragrance).
3. **Never treat a "current angle" as found unless it has a real title,
   source, and date.** If the news lookup returns nothing usable, say so
   explicitly in the output — do not write a generic, source-free "recent
   studies show..." line.
4. **Never recommend or draft anything that reaches LinkedIn, sends a
   message, or otherwise leaves this system.** The only valid output of
   this pipeline is a file in `review_queue/` for Meera to read. No node,
   adapter, or script in this project is permitted to call a
   publish/send/post endpoint.
5. **Preserve the original note verbatim** alongside any draft, so Meera
   can always see exactly what the system started from.
6. **"Skip — not worth developing" is a valid, expected outcome.** Do not
   force a low-quality or unclear fragment into a full draft; log the skip
   with a one-line reason instead.
7. **Be explicit about uncertainty.** If the triage or drafting step is not
   confident, say so in the rationale rather than picking a default
   silently.
