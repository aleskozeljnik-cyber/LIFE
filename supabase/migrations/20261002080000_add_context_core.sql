create table if not exists public.context_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  source_id uuid references public.sources(id) on delete set null,
  external_id text,
  item_type text not null,
  provider text not null,
  account_key text,
  title text,
  body text,
  summary text,
  source_url text,
  occurred_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  unique(user_id, provider, external_id)
);
create index if not exists context_items_user_occurred_idx on public.context_items(user_id, occurred_at desc);
create index if not exists context_items_user_type_idx on public.context_items(user_id, item_type);

create table if not exists public.people (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  display_name text,
  normalized_name text,
  primary_email text,
  normalized_email text,
  phone text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists people_user_email_idx on public.people(user_id, normalized_email);
create index if not exists people_user_name_idx on public.people(user_id, normalized_name);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  name text not null,
  normalized_name text not null,
  kind text not null default 'project',
  status text not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, normalized_name)
);
create index if not exists projects_user_status_idx on public.projects(user_id, status);

create table if not exists public.context_relationships (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  from_item_id uuid references public.context_items(id) on delete cascade,
  to_item_id uuid references public.context_items(id) on delete cascade,
  from_person_id uuid references public.people(id) on delete cascade,
  to_person_id uuid references public.people(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  relationship_type text not null,
  confidence numeric,
  evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (from_item_id is not null or from_person_id is not null),
  check (to_item_id is not null or to_person_id is not null or project_id is not null)
);
create index if not exists context_rel_user_type_idx on public.context_relationships(user_id, relationship_type);
create index if not exists context_rel_project_idx on public.context_relationships(project_id);

create table if not exists public.context_evidence (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  context_item_id uuid references public.context_items(id) on delete cascade,
  obligation_id uuid references public.obligations(id) on delete cascade,
  life_item_id uuid references public.life_items(id) on delete cascade,
  evidence_type text not null,
  source_ref jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (context_item_id is not null or obligation_id is not null or life_item_id is not null)
);
create index if not exists context_evidence_user_idx on public.context_evidence(user_id, evidence_type);

alter table public.context_items enable row level security;
alter table public.people enable row level security;
alter table public.projects enable row level security;
alter table public.context_relationships enable row level security;
alter table public.context_evidence enable row level security;
