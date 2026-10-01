from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .db import get_connection

_STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "your", "you",
    "please", "about", "meeting", "sestanek", "vabilo", "redna", "seja",
    "fw", "fwd", "re", "to", "of", "in", "on", "a", "an", "is", "it",
}

def _tokens(value: str | None) -> set[str]:
    raw = re.findall(r"[a-zA-ZÀ-ž0-9]{3,}", (value or "").lower())
    return {x for x in raw if x not in _STOPWORDS and not x.isdigit()}

def _priority_rank(value: str | None) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get((value or "").lower(), 1)

def _cluster(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    for row in rows:
        title_tokens = _tokens(row.get("title"))
        sender_tokens = _tokens(row.get("sender"))
        best = None
        best_score = 0.0
        for i, group in enumerate(groups):
            group_tokens = set().union(*(_tokens(x.get("title")) for x in group))
            overlap = len(title_tokens & group_tokens)
            union = len(title_tokens | group_tokens) or 1
            score = overlap / union
            if sender_tokens and any(sender_tokens & _tokens(x.get("sender")) for x in group):
                score += 0.15
            if score > best_score:
                best_score, best = score, i
        if best is not None and best_score >= 0.34:
            groups[best].append(row)
        else:
            groups.append([row])
    return groups

def _next_action(rows: list[dict[str, Any]]) -> str:
    titles = " ".join((r.get("title") or "") for r in rows).lower()
    category = next((r.get("category") for r in rows if r.get("category")), "other")
    if any(x in titles for x in ("reply", "response", "odgovor", "answer", "potrd")):
        return "Odgovori oziroma potrdi naslednji korak."
    if any(x in titles for x in ("review", "preglej", "preveri", "komentar")):
        return "Preglej vse povezane informacije in potrdi naslednji korak."
    if category == "financial":
        return "Preveri finančni učinek in uredi naslednji korak."
    if category == "legal":
        return "Preglej pravni vidik in potrdi naslednji korak."
    return "Preglej povezane informacije in določi naslednji korak."

def _group_title(rows: list[dict[str, Any]]) -> str:
    ranked = sorted(rows, key=lambda r: _priority_rank(r.get("priority")), reverse=True)
    return ranked[0].get("title") or "Life item"

def _group_summary(rows: list[dict[str, Any]]) -> str:
    summaries = []
    for r in sorted(rows, key=lambda x: _priority_rank(x.get("priority")), reverse=True):
        s = (r.get("summary") or "").strip()
        if s and s not in summaries:
            summaries.append(s)
    if not summaries:
        return "LIFE je našel povezane informacije iz več virov."
    return " ".join(summaries[:2])

async def rebuild_life_items(user_id: str) -> dict[str, int]:
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                select o.id,o.title,o.summary,o.due_at,o.priority,o.category,o.status,o.sender,
                       s.provider,s.title as source_title
                from obligations o
                left join sources s on s.id=o.source_id
                where o.user_id=%s and o.status='open'
                order by o.due_at nulls last, o.created_at desc
                """,
                (user_id,),
            )
            rows = await cur.fetchall()
            groups = _cluster(rows)
            await cur.execute("delete from life_items where user_id=%s", (user_id,))
            created = 0
            cross_source = 0
            for group in groups:
                providers = sorted({r.get("provider") for r in group if r.get("provider")})
                key_tokens = sorted(set().union(*(_tokens(r.get("title")) for r in group)))
                cluster_key = "-".join(key_tokens[:8]) or f"item-{created}"
                priority = max((r.get("priority") or "low" for r in group), key=_priority_rank)
                due_values = [r.get("due_at") for r in group if r.get("due_at")]
                due_at = min(due_values) if due_values else None
                category = next((r.get("category") for r in sorted(group, key=lambda x: _priority_rank(x.get("priority")), reverse=True) if r.get("category")), "other")
                evidence = [
                    {
                        "obligation_id": str(r["id"]),
                        "provider": r.get("provider"),
                        "title": r.get("source_title") or r.get("title"),
                        "sender": r.get("sender"),
                        "due_at": r.get("due_at").isoformat() if r.get("due_at") else None,
                    }
                    for r in group
                ]
                if len(providers) > 1:
                    cross_source += 1
                await cur.execute(
                    """
                    insert into life_items
                      (user_id,cluster_key,title,summary,next_action,priority,category,due_at,status,source_count,evidence,confidence,generated_at,updated_at)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,'open',%s,%s::jsonb,%s,now(),now())
                    """,
                    (
                        user_id, cluster_key, _group_title(group), _group_summary(group),
                        _next_action(group), priority, category, due_at, len(providers),
                        __import__("json").dumps(evidence), min((r.get("confidence") or 0 for r in group), default=0),
                    ),
                )
                created += 1
        await conn.commit()
    return {"items_created": created, "cross_source_items": cross_source}

async def get_today_life_items(user_id: str, limit: int = 8) -> list[dict[str, Any]]:
    await rebuild_life_items(user_id)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                select id,title,summary,next_action,priority,category,due_at,status,source_count,evidence,confidence
                from life_items
                where user_id=%s and status='open'
                order by
                  case priority when 'high' then 1 when 'medium' then 2 else 3 end,
                  case when due_at is null then 1 else 0 end,
                  due_at asc
                limit %s
                """,
                (user_id, limit),
            )
            return await cur.fetchall()
