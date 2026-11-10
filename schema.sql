-- FaunaBehav database schema (PostgreSQL / Supabase).
--
-- Two uses:
--   * A fresh database: run the whole file once in the Supabase SQL editor.
--   * The original capstone database: the CREATE statements are skipped
--     (IF NOT EXISTS) and the ALTER / RLS sections at the end bring it up to
--     what v1.0 of the API expects. Safe to re-run.
--
-- Column names follow the capstone database as it exists (events.timestamp,
-- feedback.submitted_at, devices.farm_id ...). The API maps them to its own
-- field names in app/storage/supabase_storage.py.

create table if not exists users (
  user_id       serial primary key,
  username      varchar not null unique,
  password_hash varchar not null,                      -- bcrypt
  role          varchar not null default 'farmer',     -- admin | farmer | operator
  email         text,
  created_at    timestamp not null default now()
);

create table if not exists farms (
  farm_id    serial primary key,
  farm_name  text not null,
  location   text,
  owner_id   integer references users(user_id),
  created_at timestamptz not null default now()
);

create table if not exists devices (
  device_id         serial primary key,
  device_name       varchar not null,
  location          varchar,
  status            varchar not null default 'active',  -- active | inactive
  farm_id           integer references farms(farm_id),
  deterrence_active boolean not null default false,
  api_key_hash      text unique,                        -- sha256 of the device API key (v1.0)
  created_at        timestamp not null default now()
);

create table if not exists events (
  event_id             serial primary key,
  device_id            integer not null references devices(device_id),
  "timestamp"          timestamp not null default now(),
  animal               varchar,
  behaviour            varchar,
  confidence           double precision,
  risk_level           varchar,                         -- Low | Medium | High
  deterrence_action    text,                            -- Monitor | Flash Light | Siren
  frame_path           varchar,
  -- detection details from the edge model (YOLOv8)
  species_confidence   numeric,
  bounding_box         jsonb,
  frame_width          integer,
  frame_height         integer,
  -- operator review workflow
  outcome              text default 'pending_review',
  farmer_notes         text,
  resolution_timestamp timestamptz,
  notify_farmer        boolean default false,
  escalation           boolean default false,
  action_status        text
);

create table if not exists alerts (
  alert_id          serial primary key,
  event_id          integer not null references events(event_id),
  triggered_at      timestamp not null default now(),
  status            varchar not null default 'Active', -- Active | Acknowledged | Resolved
  deterrence_action text,
  acknowledged_by   integer references users(user_id),
  risk_level        varchar,
  is_read           boolean not null default false
);

create table if not exists feedback (
  feedback_id         serial primary key,
  event_id            integer not null references events(event_id),
  user_id             integer not null references users(user_id),
  corrected_behaviour varchar not null,
  note                text,
  submitted_at        timestamp not null default now()
);

-- ---------------------------------------------------------------------------
-- Upgrade an existing capstone database to v1.0 (all additive, safe to re-run)
alter table devices  add column if not exists api_key_hash text unique;
alter table feedback add column if not exists note text;
alter table users    add column if not exists email text;

create index if not exists events_timestamp_idx on events ("timestamp" desc);
create index if not exists events_device_idx    on events (device_id);
create index if not exists alerts_status_idx    on alerts (status);
create index if not exists alerts_event_idx     on alerts (event_id);

-- ---------------------------------------------------------------------------
-- Row Level Security.
-- The API connects with the service-role key, which bypasses RLS. Enabling RLS
-- with no policies means the public anon key can read or write NOTHING, so the
-- tables are only reachable through the API. (Before v1.0 they were "UNRESTRICTED".)
alter table users    enable row level security;
alter table farms    enable row level security;
alter table devices  enable row level security;
alter table events   enable row level security;
alter table alerts   enable row level security;
alter table feedback enable row level security;
