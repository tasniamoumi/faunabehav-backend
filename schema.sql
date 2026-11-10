-- FaunaBehav database schema (PostgreSQL / Supabase).
-- Run once in the Supabase SQL editor. Safe to re-run: uses IF NOT EXISTS.

create table if not exists devices (
  device_id    serial primary key,
  device_name  text not null,
  location     text not null,
  status       text not null default 'Active',          -- Active | Inactive
  api_key_hash text unique,                              -- sha256 of the device API key
  created_at   timestamptz not null default now()
);

create table if not exists users (
  user_id       serial primary key,
  username      text not null unique,
  password_hash text not null,                          -- bcrypt
  role          text not null default 'operator',       -- operator | admin
  created_at    timestamptz not null default now()
);

create table if not exists events (
  event_id          serial primary key,
  device_id         integer not null references devices(device_id),
  animal            text not null,
  behaviour         text not null,
  confidence        real not null check (confidence between 0 and 1),
  risk_level        text not null,                      -- Low | Medium | High
  deterrence_action text not null,                      -- Monitor | Flash Light | Siren
  frame_path        text,
  created_at        timestamptz not null default now()
);

create table if not exists alerts (
  alert_id          serial primary key,
  event_id          integer not null references events(event_id),
  risk_level        text not null,
  deterrence_action text not null,
  status            text not null default 'Active',     -- Active | Acknowledged | Resolved
  acknowledged_by   integer references users(user_id),
  triggered_at      timestamptz not null default now()
);

create table if not exists feedback (
  feedback_id         serial primary key,
  event_id            integer not null references events(event_id),
  user_id             integer not null references users(user_id),
  corrected_behaviour text not null,
  note                text,
  created_at          timestamptz not null default now()
);

-- Columns added in v1.0 for databases created by the original FYP build:
alter table devices  add column if not exists api_key_hash text unique;
alter table devices  add column if not exists created_at timestamptz not null default now();
alter table feedback add column if not exists note text;
alter table users    add column if not exists password_hash text;

create index if not exists events_created_at_idx on events (created_at desc);
create index if not exists alerts_status_idx     on alerts (status);
