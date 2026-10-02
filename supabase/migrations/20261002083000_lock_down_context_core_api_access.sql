revoke all on table public.context_items from anon, authenticated;
revoke all on table public.people from anon, authenticated;
revoke all on table public.projects from anon, authenticated;
revoke all on table public.context_relationships from anon, authenticated;
revoke all on table public.context_evidence from anon, authenticated;

create policy "deny anon context_items" on public.context_items for all to anon using (false) with check (false);
create policy "deny authenticated context_items" on public.context_items for all to authenticated using (false) with check (false);
create policy "deny anon people" on public.people for all to anon using (false) with check (false);
create policy "deny authenticated people" on public.people for all to authenticated using (false) with check (false);
create policy "deny anon projects" on public.projects for all to anon using (false) with check (false);
create policy "deny authenticated projects" on public.projects for all to authenticated using (false) with check (false);
create policy "deny anon context_relationships" on public.context_relationships for all to anon using (false) with check (false);
create policy "deny authenticated context_relationships" on public.context_relationships for all to authenticated using (false) with check (false);
create policy "deny anon context_evidence" on public.context_evidence for all to anon using (false) with check (false);
create policy "deny authenticated context_evidence" on public.context_evidence for all to authenticated using (false) with check (false);
