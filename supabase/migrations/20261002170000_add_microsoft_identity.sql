alter table public.users add column if not exists microsoft_sub text;
create unique index if not exists users_microsoft_sub_idx on public.users(microsoft_sub) where microsoft_sub is not null;
