-- Skinstinct content bot — pending-state schema.
--
-- This app keeps NO permanent record of notes/drafts itself — the only
-- permanent archive is the GitHub repo committed to on approval. This
-- table exists purely to bridge Telegram's stateless webhook calls (a
-- voice note's transcript has to survive until the reply picking a
-- format arrives; a draft has to survive until Approve/Reject/Regenerate
-- is tapped) between one Vercel function invocation and the next. Rows
-- are deleted as soon as they're resolved (approved, rejected, discarded,
-- or a format is chosen), so nothing accumulates here.
--
-- If you're re-running this after the old notes/drafts/voice_skill tables
-- from an earlier version of this project: they're no longer used by the
-- app and can be dropped if you want to clean up, but nothing here
-- requires that.

create extension if not exists pgcrypto;

create table if not exists pending_items (
  id uuid primary key default gen_random_uuid(),

  -- 'awaiting_format' -> a transcribed voice note waiting for a
  --   /linkedin or /newsletter reply to say what to draft.
  -- 'awaiting_decision' -> a posted draft waiting for
  --   Approve/Regenerate/Discard.
  stage text not null check (stage in ('awaiting_format', 'awaiting_decision')),

  format text check (format in ('linkedin', 'newsletter')),
  note_text text not null,

  score int check (score between 0 and 10),
  score_reason text,

  news_query text,
  news_headline text,
  news_source text,
  news_published text,
  news_link text,
  news_summary text,

  draft_text text,
  news_used boolean not null default false,

  telegram_chat_id bigint not null,
  telegram_message_id bigint,

  created_at timestamptz not null default now()
);

create index if not exists pending_items_telegram_message_id_idx
  on pending_items (telegram_message_id);
