from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any
from .db import get_connection

_STOPWORDS={"the","and","for","with","from","this","that","your","you","please","about","meeting","sestanek","vabilo","redna","seja","fw","fwd","re","to","of","in","on","a","an","is","it","ali","ter","pri","za","na","je","so","se","do","od","inbox","gmail","calendar","google","reminder","mail","email"}

def _tokens(value: str | None) -> set[str]:
    return {x for x in re.findall(r"[a-zA-ZÀ-ž0-9]{3,}",(value or "").lower()) if x not in _STOPWORDS and not x.isdigit()}

def _text(row: dict[str,Any]) -> str:
    return " ".join(str(row.get(k) or "") for k in ("title","summary","sender","source_title")).lower()

def _noise(row: dict[str,Any]) -> bool:
    text=_text(row); category=(row.get("category") or "").lower()
    patterns=("security code","verification code","password reset","ponastavite vaše geslo","welcome to",
              "check out this week","unsubscribe","newsletter","hotel marina","ebike flow",
              "potrditev vašega naročila","tracking","survey in progress","marketing","promotional",
              "profesionalna it oprema","rabljeniracunalniki")
    return category in {"marketing","notification","newsletter","travel_deal"} or any(p in text for p in patterns)

def _actionability(row: dict[str,Any]) -> float:
    text=_text(row)
    if row.get("provider")=="calendar":
        # Calendar is context by default. Only pull an event into Today when it is close enough
        # to require preparation or action.
        due=row.get("due_at")
        if not due:
            return 0.15
        try:
            d=due if due.tzinfo else due.replace(tzinfo=timezone.utc)
            hours=(d-datetime.now(timezone.utc)).total_seconds()/3600
            score=0.85 if hours <= 24 else (0.65 if hours <= 48 else 0.15)
        except Exception:
            score=0.35
        if any(p in text for p in ("decision","odločit","prepare","pripravi","agenda","dnevni red","open","odprto")):
            score+=0.15
        return min(score,1.0)
    score=0.0
    # Explicit requests/actions are meaningful; generic "medium" source priority is not.
    if any(p in text for p in ("reply","respond","response","odgovor","odgovori","potrdi","confirm","review","preglej",
                               "preveri","invoice","račun","faktura","payment","plačilo","deadline","rok","request",
                               "zahteva","waiting","čakam","approve","odobri","comment","komentar","decision",
                               "rabim","potrebujem","prosim","pošlji","pošljite","oddaj","oddajte","podpi",
                               "uredi","pripravi","sporoči","potrdi")):
        score+=0.65
    if row.get("due_at"): score+=0.20
    if (row.get("priority") or "").lower()=="high": score+=0.20
    # Outbound/completed threads should not become tasks just because they mention an invoice.
    if any(p in text for p in ("will be paid","bo plačana","bo plačan","je plačano","plačano","predana računovodstvu","urejeno")):
        score=min(score,0.20)
    return min(score,1.0)

def _priority_rank(value: str | None) -> int:
    return {"high":3,"medium":2,"low":1}.get((value or "").lower(),1)

def _context_tokens(row: dict[str,Any]) -> set[str]:
    return _tokens(" ".join(str(row.get(k) or "") for k in ("title","summary","sender","source_title")))

def _title_tokens(row: dict[str,Any]) -> set[str]:
    return _tokens(str(row.get("title") or ""))


def _cluster(rows: list[dict[str,Any]]) -> list[list[dict[str,Any]]]:
    groups=[]
    for row in rows:
        tokens=_context_tokens(row); sender=_tokens(row.get("sender")); best=None; best_score=0.0
        for i,g in enumerate(groups):
            gt=set().union(*(_context_tokens(x) for x in g))
            overlap=len(tokens & gt); union=len(tokens | gt) or 1
            score=overlap/union
            if sender and any(sender & _tokens(x.get("sender")) for x in g): score+=0.20
            cross_provider=row.get("provider")!=g[0].get("provider")
            shared_people=set(row.get("person_ids") or []) & set().union(*(set(x.get("person_ids") or []) for x in g))
            shared_projects=set(row.get("project_ids") or []) & set().union(*(set(x.get("project_ids") or []) for x in g))
            distinctive={t for t in tokens & gt if len(t)>=5 and t not in {"please","today","tomorrow","google","calendar"}}
            if cross_provider:
                # Cross-source clustering must have real context linkage. Token coincidence alone
                # is not sufficient; shared canonical people/projects are strong evidence.
                if not shared_people and not shared_projects and not (len(_title_tokens(row) & set().union(*(_title_tokens(x) for x in g))) >= 2 and distinctive):
                    continue
                if shared_people or shared_projects or len(_title_tokens(row) & set().union(*(_title_tokens(x) for x in g))) >= 2: score+=0.12
                if distinctive: score+=0.10
                if shared_people: score+=0.25
                if shared_projects: score+=0.30
            if score>best_score: best_score,best=score,i
        if best is not None and best_score>=0.30: groups[best].append(row)
        else: groups.append([row])
    return groups

def _next_action(rows: list[dict[str,Any]]) -> str:
    titles=" ".join((r.get("title") or "") for r in rows).lower()
    category=next((r.get("category") for r in rows if r.get("category")),"other")
    providers={r.get("provider") for r in rows if r.get("provider")}
    titles_lower=titles
    if "calendar" in providers and len(providers)>1 and any(x in titles_lower for x in ("sestanek","meeting","appointment","vabilo","seja","event")):
        return "Pred dogodkom preglej povezane maile in pripravi ključne točke oziroma odprte odločitve."
    if any(x in titles for x in ("faktura","račun","invoice")): return "Preveri status računa/fakture in uredi naslednji korak."
    if any(x in titles for x in ("pogodba","contract","mandate","agreement")): return "Preglej odprte pripombe in pripravi/pošlji naslednji odgovor."
    if any(x in titles for x in ("waiting for","čakam","awaiting")): return "Preveri, ali je potreben tvoj odgovor ali follow-up."
    if any(x in titles for x in ("sestanek","meeting")): return "Pripravi ključne točke in odprte odločitve za sestanek."
    if any(x in titles for x in ("vabilo","seja","appointment","event")): return "Preveri dnevni red, lokacijo in ali potrebuješ pripravo."
    if category=="financial": return "Preveri finančni učinek in uredi naslednji korak."
    if category=="legal": return "Preglej pravni vidik in potrdi naslednji korak."
    if category=="work": return "Preglej povezane informacije in določi naslednji korak."
    return "Preglej in potrdi, ali je potreben tvoj naslednji korak."

def _category(rows: list[dict[str,Any]]) -> str:
    text=" ".join(_text(r) for r in rows)
    if any(x in text for x in ("račun","faktura","invoice","payment","plačilo","dividend","dividende","posojilo","loan")): return "financial"
    if any(x in text for x in ("contract","pogodba","legal","pravno","mandate","mandat","agreement","efet","isda")): return "legal"
    if any(x in text for x in ("sestanek","meeting","board","uprava","project","projekt","kolektor","sij","tab","eles","energy","energ")): return "work"
    return next((r.get("category") for r in rows if r.get("category")),"other")

def _group_title(rows: list[dict[str,Any]]) -> str:
    for r in sorted(rows,key=_actionability,reverse=True):
        title=re.sub(r"^(re|fw|fwd)\s*:\s*","",(r.get("title") or "").strip(),flags=re.I)
        if title:return title
    return "LIFE item"

def _group_summary(rows: list[dict[str,Any]]) -> str:
    # UI summary must be a compact explanation, never a dump of the raw email body.
    providers=sorted({r.get("provider") for r in rows if r.get("provider")})
    titles=[]
    for r in sorted(rows,key=_actionability,reverse=True):
        t=re.sub(r"^(re|fw|fwd)\s*:\s*","",(r.get("title") or "").strip(),flags=re.I)
        if t and t not in titles:
            titles.append(t)
    if len(providers)>1:
        return f"Povezano iz virov: {', '.join(providers)} · " + " + ".join(titles[:2])
    return titles[0] if titles else "LIFE je povezal informacije iz več virov."

def _evidence(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    """Build source-backed, user-readable evidence for a Life Item."""
    evidence = []
    for r in rows:
        evidence.append({
            "obligation_id": str(r["id"]),
            "provider": r.get("provider"),
            "title": r.get("source_title") or r.get("title"),
            "sender": r.get("sender"),
            "due_at": r.get("due_at").isoformat() if r.get("due_at") else None,
            "relationship": "direct_source",
        })
    return evidence

async def rebuild_life_items(user_id: str) -> dict[str,int]:
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""select o.id,o.title,o.summary,o.due_at,o.priority,o.category,o.status,o.sender,o.confidence,o.source_id,s.provider,s.title as source_title
                                 from obligations o left join sources s on s.id=o.source_id
                                 where o.user_id=%s and o.status='open' order by o.due_at nulls last,o.created_at desc""",(user_id,))
            rows=await cur.fetchall()
            candidates=[r for r in rows if not _noise(r)]
            groups=_cluster(candidates)
            await cur.execute("delete from life_items where user_id=%s",(user_id,))
            created=cross_source=filtered=0
            for group in groups:
                action=max((_actionability(r) for r in group),default=0)
                if action<0.55:
                    filtered+=1
                    continue
                providers=sorted({r.get("provider") for r in group if r.get("provider")})
                category=_category(group)
                priority="high" if action>=0.85 or any((r.get("priority") or "").lower()=="high" for r in group) else ("medium" if action>=0.55 else "low")
                due_values=[r.get("due_at") for r in group if r.get("due_at")]
                due_at=min(due_values) if due_values else None
                if due_at:
                    try:
                        d=due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
                        if (d-datetime.now(timezone.utc)).total_seconds()<=24*3600: priority="high"
                    except Exception: pass
                # A Life Item without traceable source evidence is not useful enough
                # for the main Today view. Keep the evidence requirement explicit.
                evidence_rows = _evidence(group)
                if not evidence_rows:
                    filtered += 1
                    continue
                key_tokens=sorted(set().union(*(_context_tokens(r) for r in group)))
                cluster_key="-".join(key_tokens[:10]) or f"item-{created}"
                if len(providers)>1: cross_source+=1
                await cur.execute("""insert into life_items
                  (user_id,cluster_key,title,summary,next_action,priority,category,due_at,status,source_count,evidence,confidence,generated_at,updated_at)
                  values (%s,%s,%s,%s,%s,%s,%s,%s,'open',%s,%s::jsonb,%s,now(),now())
                  returning id""",
                  (user_id,cluster_key,_group_title(group),_group_summary(group),_next_action(group),priority,category,due_at,
                   len(providers),__import__("json").dumps(evidence_rows),max((r.get("confidence") or 0 for r in group),default=0)))
                life_item_id=(await cur.fetchone())["id"]
                for row in group:
                    if row.get("id") and row.get("source_id"):
                        await cur.execute(
                            """insert into context_evidence (user_id,context_item_id,obligation_id,life_item_id,evidence_type,source_ref)
                               select %s,ci.id,%s,%s,'life_item_source',
                                      jsonb_build_object('provider',ci.provider,'external_id',ci.external_id)
                               from context_items ci
                               where ci.user_id=%s and ci.source_id=%s
                                 and not exists (
                                   select 1 from context_evidence ce
                                   where ce.user_id=%s and ce.life_item_id=%s
                                     and ce.context_item_id=ci.id
                                     and ce.evidence_type='life_item_source'
                                 )""",
                            (user_id,row["id"],life_item_id,user_id,row["source_id"],user_id,life_item_id),
                        )
                created+=1
        await conn.commit()
    return {"items_created":created,"cross_source_items":cross_source,"filtered_noise":filtered}

async def get_today_life_items(user_id: str,limit: int=3) -> list[dict[str,Any]]:
    await rebuild_life_items(user_id)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""select id,title,summary,next_action,priority,category,due_at,status,source_count,evidence,confidence
                                 from life_items where user_id=%s and status='open'
                                 order by case priority when 'high' then 1 when 'medium' then 2 else 3 end,
                                          case when due_at is null then 1 else 0 end,due_at asc limit %s""",(user_id,limit))
            return await cur.fetchall()
