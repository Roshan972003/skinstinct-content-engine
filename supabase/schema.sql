-- Skinstinct content bot — schema.
--
-- `pending_items` is a pure state bridge: only used to carry a transcribed
-- voice note across Telegram's stateless webhook calls until a
-- /linkedin or /newsletter reply says what to draft. Rows are deleted as
-- soon as that's resolved.
--
-- `notes`, `drafts`, and `voice_skill` are the PERMANENT memory layer:
-- every scored note is saved (whether it produced a draft or not), every
-- draft is saved with a status that updates on Approve/Reject rather
-- than being deleted, and rejected notes/drafts are kept on purpose —
-- they show what needs improving. The GitHub archive (see lib/github_client.py)
-- is additionally where the actual approved text gets committed on
-- approval; these tables are the audit trail, not a replacement for it.

create extension if not exists pgcrypto;

create table if not exists pending_items (
  id uuid primary key default gen_random_uuid(),
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

create table if not exists notes (
  id uuid primary key default gen_random_uuid(),
  text text not null,
  score int check (score between 0 and 10),
  score_reason text,
  news_query text,
  telegram_chat_id bigint not null,
  telegram_message_id bigint,
  created_at timestamptz not null default now()
);

create table if not exists drafts (
  id uuid primary key default gen_random_uuid(),
  note_id uuid not null references notes(id) on delete cascade,
  format text not null check (format in ('linkedin', 'newsletter')),
  draft_text text,
  news_used boolean not null default false,
  news_headline text,
  news_source text,
  news_published text,
  news_link text,
  news_summary text,
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected', 'regenerated')),
  archive_url text,
  telegram_chat_id bigint not null,
  telegram_message_id bigint,
  decided_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists drafts_telegram_message_id_idx on drafts (telegram_message_id);
create index if not exists drafts_note_id_idx on drafts (note_id);

-- Holds the voice/style reference used in every draft call. Seeded from
-- voice-skill.txt at deploy time; editable later without a redeploy.
create table if not exists voice_skill (
  id int primary key default 1,
  content text not null,
  updated_at timestamptz not null default now(),
  constraint voice_skill_singleton check (id = 1)
);
