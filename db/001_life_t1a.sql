create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  google_sub text unique not null,
  email text unique not null,
  name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists oauth_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  provider text not null check (provider = 'google'),
  access_token_encrypted text not null,
  refresh_token_encrypted text,
  expires_at timestamptz,
  scopes text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, provider)
);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  provider text not null,
  external_id text not null,
  title text,
  last_synced_at timestamptz,
  created_at timestamptz not null default now(),
  unique(user_id, provider, external_id)
);

create table if not exists obligations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  source_id uuid references sources(id) on delete set null,
  external_id text,
  title text not null,
  summary text,
  due_at timestamptz,
  amount numeric(14,2),
  currency text,
  sender text,
  category text,
  priority text not null default 'medium',
  classification_reason text not null,
  status text not null default 'open',
  confidence numeric(5,4),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, external_id)
);

create table if not exists corrections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  obligation_id uuid references obligations(id) on delete cascade,
  field_name text not null,
  old_value text,
  new_value text not null,
  created_at timestamptz not null default now()
);

create table if not exists daily_summaries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  summary_date date not null,
  content text not null,
  created_at timestamptz not null default now(),
  unique(user_id, summary_date)
);

create table if not exists confidence_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  obligation_id uuid references obligations(id) on delete cascade,
  model text,
  confidence numeric(5,4),
  decision text,
  created_at timestamptz not null default now()
);

create index if not exists obligations_user_due_idx on obligations(user_id, due_at);
create index if not exists obligations_user_status_idx on obligations(user_id, status);
create index if not exists corrections_user_field_idx on corrections(user_id, field_name);
