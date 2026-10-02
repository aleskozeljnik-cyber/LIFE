-- Keep the Context Core deny guardrails restrictive so future permissive
-- per-user policies cannot accidentally bypass the deny condition.

drop policy if exists "deny anon context_items" on public.context_items;
drop policy if exists "deny authenticated context_items" on public.context_items;
drop policy if exists "deny anon people" on public.people;
drop policy if exists "deny authenticated people" on public.people;
drop policy if exists "deny anon projects" on public.projects;
drop policy if exists "deny authenticated projects" on public.projects;
drop policy if exists "deny anon context_relationships" on public.context_relationships;
drop policy if exists "deny authenticated context_relationships" on public.context_relationships;
drop policy if exists "deny anon context_evidence" on public.context_evidence;
drop policy if exists "deny authenticated context_evidence" on public.context_evidence;

create policy "deny anon context_items" on public.context_items as restrictive for all to anon using (false) with check (false);
create policy "deny authenticated context_items" on public.context_items as restrictive for all to authenticated using (false) with check (false);
create policy "deny anon people" on public.people as restrictive for all to anon using (false) with check (false);
create policy "deny authenticated people" on public.people as restrictive for all to authenticated using (false) with check (false);
create policy "deny anon projects" on public.projects as restrictive for all to anon using (false) with check (false);
create policy "deny authenticated projects" on public.projects as restrictive for all to authenticated using (false) with check (false);
create policy "deny anon context_relationships" on public.context_relationships as restrictive for all to anon using (false) with check (false);
create policy "deny authenticated context_relationships" on public.context_relationships as restrictive for all to authenticated using (false) with check (false);
create policy "deny anon context_evidence" on public.context_evidence as restrictive for all to anon using (false) with check (false);
create policy "deny authenticated context_evidence" on public.context_evidence as restrictive for all to authenticated using (false) with check (false);
