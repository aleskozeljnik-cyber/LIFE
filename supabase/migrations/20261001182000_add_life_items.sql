create table if not exists public.life_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  cluster_key text not null,
  title text not null,
  summary text,
  next_action text,
  priority text not null default 'medium',
  category text,
  due_at timestamptz,
  status text not null default 'open',
  source_count integer not null default 0,
  evidence jsonb not null default '[]'::jsonb,
  confidence numeric,
  generated_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, cluster_key)
);

create index if not exists life_items_user_status_due_idx
  on public.life_items(user_id, status, due_at);

alter table public.life_items enable row level security;
