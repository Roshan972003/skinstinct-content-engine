-- Skinstinct content engine — schema for live Telegram -> Supabase pipeline.
-- Run this once in the Supabase SQL Editor (Project -> SQL Editor -> New query).

create extension if not exists pgcrypto;

create table if not exists notes (
  id uuid primary key default gen_random_uuid(),
  telegram_message_id bigint,
  telegram_chat_id bigint,
  text text not null,
  captured_at timestamptz not null default now(),
  verdict text,
  reason text,
  theme text,
  overlaps_with text,
  confidence text,
  model_mocked boolean not null default false,
  raw_triage_response text,
  created_at timestamptz not null default now()
);

create index if not exists notes_theme_idx on notes (theme);

create table if not exists drafts (
  id uuid primary key default gen_random_uuid(),
  note_id uuid not null references notes(id) on delete cascade,
  draft_text text,
  rationale text,
  claims_ledger text,
  news_used text,
  news_candidate_count int not null default 0,
  model_mocked boolean not null default false,
  raw_draft_response text,
  telegram_chat_id bigint,
  telegram_reply_message_id bigint,
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  decided_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists drafts_telegram_reply_message_id_idx
  on drafts (telegram_reply_message_id);

-- Holds the voice/style reference used in every draft call. Seeded from
-- voice-skill.txt at deploy time; editable later without a redeploy.
create table if not exists voice_skill (
  id int primary key default 1,
  content text not null,
  updated_at timestamptz not null default now(),
  constraint voice_skill_singleton check (id = 1)
);
