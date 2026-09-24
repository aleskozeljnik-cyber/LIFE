create table if not exists usage_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  action text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists usage_logs_user_created_idx on usage_logs(user_id, created_at desc);
create index if not exists sources_user_provider_idx on sources(user_id, provider);