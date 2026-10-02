create unique index if not exists context_evidence_obligation_source_unique
  on public.context_evidence(user_id, obligation_id, context_item_id, evidence_type)
  where obligation_id is not null
    and context_item_id is not null
    and evidence_type = 'obligation_source';

create unique index if not exists context_evidence_life_item_source_unique
  on public.context_evidence(user_id, life_item_id, context_item_id, evidence_type)
  where life_item_id is not null
    and context_item_id is not null
    and evidence_type = 'life_item_source';
