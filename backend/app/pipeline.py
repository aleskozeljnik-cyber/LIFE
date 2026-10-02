import base64
from datetime import datetime, timezone
from email.utils import getaddresses, parsedate_to_datetime
from .db import get_connection
from .extraction import extract_obligation, is_ai_candidate
from .gmail import get_message, list_recent_messages
from .calendar import list_upcoming_events
from .context import NormalizedItem, PersonRef, normalize_email, normalize_name, extract_project_hint, candidate_topic_names, candidate_topic_from_shared_person, topic_tokens, topic_anchor_tokens

def _decode(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
    except Exception:
        return ""

def _walk(part: dict) -> list[str]:
    values = []
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        values.append(_decode(part["body"]["data"]))
    for child in part.get("parts", []) or []:
        values.extend(_walk(child))
    return values

def gmail_occurred_at_from_payload(message: dict) -> datetime | None:
    """Extract Gmail message time from the provider payload."""
    internal_date = message.get("internalDate")
    if internal_date is not None:
        try:
            return datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass
    headers = {h.get("name", "").lower(): h.get("value", "") for h in message.get("payload", {}).get("headers", [])}
    raw_date = headers.get("date")
    if raw_date:
        try:
            parsed = parsedate_to_datetime(raw_date)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (TypeError, ValueError, IndexError, OverflowError):
            pass
    return None


def gmail_text(message: dict) -> str:
    payload = message.get("payload", {})
    headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}
    body = "\n".join(x for x in _walk(payload) if x.strip()) or message.get("snippet", "")
    return "\n".join(x for x in [f"From: {headers.get('from','')}", f"To: {headers.get('to','')}", f"Subject: {headers.get('subject','')}", body] if x).strip()

async def _hint(cur, user_id: str) -> str:
    await cur.execute("select field_name,new_value,count(*) as n from corrections where user_id=%s and field_name in ('category','title') group by field_name,new_value order by n desc limit 12", (user_id,))
    rows = await cur.fetchall()
    return "; ".join(f"{r['field_name']}={r['new_value']}" for r in rows)


async def _persist_context_item(cur, user_id: str, item: NormalizedItem) -> str:
    await cur.execute(
        """insert into context_items
        (user_id,source_id,external_id,item_type,provider,account_key,title,body,summary,source_url,occurred_at,metadata)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
        on conflict (user_id,provider,external_id) do update set
          title=excluded.title, body=excluded.body, summary=excluded.summary,
          source_url=excluded.source_url, occurred_at=excluded.occurred_at,
          metadata=excluded.metadata, updated_at=now()
        returning id""",
        (user_id, item.metadata.get("source_id") if item.metadata else None, item.external_id,
         item.item_type, item.provider, item.account_key, item.title, item.body, item.summary,
         item.source_url, item.occurred_at,
         __import__("json").dumps(item.metadata or {})),
    )
    row = await cur.fetchone()
    return row["id"]


async def _user_email(cur, user_id: str) -> str | None:
    await cur.execute("select email from users where id=%s", (user_id,))
    row = await cur.fetchone()
    return normalize_email(row["email"]) if row else None

async def _persist_person(cur, user_id: str, ref: PersonRef) -> str | None:
    email = normalize_email(ref.email)
    name = normalize_name(ref.display_name)
    if not email and not name:
        return None
    if email:
        await cur.execute("select id from people where user_id=%s and normalized_email=%s limit 1", (user_id, email))
    else:
        await cur.execute("select id from people where user_id=%s and normalized_name=%s limit 1", (user_id, name))
    row = await cur.fetchone()
    if row:
        await cur.execute("update people set display_name=coalesce(%s,display_name), primary_email=coalesce(%s,primary_email), normalized_email=coalesce(%s,normalized_email), updated_at=now() where id=%s and user_id=%s", (ref.display_name,email,email,row["id"],user_id))
        return row["id"]
    await cur.execute("insert into people (user_id,display_name,normalized_name,primary_email,normalized_email,phone) values (%s,%s,%s,%s,%s,%s) returning id", (user_id,ref.display_name,name,ref.email,email,ref.phone))
    return (await cur.fetchone())["id"]

async def _persist_project(cur, user_id: str, name: str) -> str | None:
    normalized = normalize_name(name)
    if not normalized:
        return None
    await cur.execute("insert into projects (user_id,name,normalized_name) values (%s,%s,%s) on conflict (user_id,normalized_name) do update set name=excluded.name, updated_at=now() returning id", (user_id,name.strip(),normalized))
    return (await cur.fetchone())["id"]

async def _link_item_person(cur, user_id: str, item_id: str, person_id: str) -> None:
    await cur.execute("insert into context_relationships (user_id,from_item_id,to_person_id,relationship_type,confidence,evidence) select %s,%s,%s,'participant',1.0,'{}'::jsonb where not exists (select 1 from context_relationships where user_id=%s and from_item_id=%s and to_person_id=%s and relationship_type='participant')", (user_id,item_id,person_id,user_id,item_id,person_id))

async def _link_item_project(cur, user_id: str, item_id: str, project_id: str) -> None:
    await cur.execute("insert into context_relationships (user_id,from_item_id,project_id,relationship_type,confidence,evidence) select %s,%s,%s,'project',1.0,'{}'::jsonb where not exists (select 1 from context_relationships where user_id=%s and from_item_id=%s and project_id=%s and relationship_type='project')", (user_id,item_id,project_id,user_id,item_id,project_id))


async def _resolve_cross_source_topics(cur, user_id: str) -> list[str]:
    await cur.execute(
        """select ci.id, ci.provider, ci.title, ci.occurred_at,
                  coalesce(array_agg(cr.to_person_id) filter (where cr.to_person_id is not null), '{}') as person_ids
           from context_items ci
           left join context_relationships cr
             on cr.user_id=ci.user_id
            and cr.from_item_id=ci.id
            and cr.relationship_type='participant'
           where ci.user_id=%s and ci.title is not null
           group by ci.id, ci.provider, ci.title, ci.occurred_at""",
        (user_id,),
    )
    rows = await cur.fetchall()
    names = sorted(set(candidate_topic_names(rows)) | set(candidate_topic_from_shared_person(rows)))
    for name in names:
        await cur.execute("insert into projects (user_id,name,normalized_name,kind,status) values (%s,%s,%s,'topic','candidate') on conflict (user_id,normalized_name) do update set updated_at=now() returning id", (user_id,name.upper(),name))
        project_id = (await cur.fetchone())["id"]
        for row in rows:
            if name in topic_tokens(row.get("title")) or name in topic_anchor_tokens(row.get("title")):
                await _link_item_project(cur, user_id, row["id"], project_id)
    return names

async def sync_gmail_and_extract(user_id: str, access_token: str) -> dict:
    messages = await list_recent_messages(access_token, days=7, max_results=100)
    created = skipped = prefilter_filtered = messages_sent_to_ai = 0
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            hint = await _hint(cur, user_id)
            user_email = await _user_email(cur, user_id)
            for summary in messages:
                external_id = summary.get("id")
                if not external_id: continue
                await cur.execute("select id from obligations where user_id=%s and external_id=%s", (user_id, external_id))
                existing_obligation = await cur.fetchone()
                if existing_obligation: skipped += 1
                await cur.execute("select id from sources where user_id=%s and provider='gmail' and external_id=%s", (user_id, external_id))
                existing_source = await cur.fetchone()
                message = await get_message(access_token, external_id)
                text = gmail_text(message)
                headers = {h.get("name", "").lower(): h.get("value", "") for h in message.get("payload", {}).get("headers", [])}
                title = headers.get("subject", "") or summary.get("subject", "") or "Gmail message"
                gmail_occurred_at = gmail_occurred_at_from_payload(message)
                item_id = await _persist_context_item(cur, user_id, NormalizedItem(
                    provider="gmail", item_type="message", external_id=external_id,
                    title=title[:300], body=text, summary=message.get("snippet", ""), occurred_at=gmail_occurred_at,
                    metadata={"gmail_message_id": external_id},
                ))
                addresses = getaddresses([headers.get("from",""), headers.get("to",""), headers.get("cc","")])
                for display_name, email in addresses:
                    email = normalize_email(email)
                    if not email or email == user_email:
                        continue
                    person_id = await _persist_person(cur, user_id, PersonRef(display_name=display_name or None, email=email))
                    if person_id:
                        await _link_item_person(cur, user_id, item_id, person_id)
                project = extract_project_hint(title)
                if project:
                    project_id = await _persist_project(cur, user_id, project.name)
                    if project_id:
                        await _link_item_project(cur, user_id, item_id, project_id)
                if existing_source:
                    source_id = existing_source["id"]
                    await cur.execute("update sources set last_synced_at=now() where id=%s and user_id=%s", (source_id,user_id))
                else:
                    await cur.execute("insert into sources (user_id,provider,external_id,title,last_synced_at) values (%s,'gmail',%s,%s,now()) returning id", (user_id,external_id,text.splitlines()[2][:300] if len(text.splitlines())>2 else "Gmail message"))
                    source_id = (await cur.fetchone())["id"]
                await cur.execute("update context_items set source_id=%s, updated_at=now() where user_id=%s and provider='gmail' and external_id=%s", (source_id,user_id,external_id))
                if existing_obligation:
                    continue
                if not is_ai_candidate(text, "email"):
                    prefilter_filtered += 1
                    continue
                messages_sent_to_ai += 1
                if messages_sent_to_ai > 8:
                    prefilter_filtered += 1
                    continue
                extracted = await extract_obligation(text, hint, "email")
                if extracted:
                    await cur.execute("insert into obligations (user_id,source_id,external_id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (user_id,external_id) do nothing returning id", (user_id,source_id,external_id,extracted.title,extracted.summary,extracted.due_at,extracted.amount,extracted.currency,extracted.sender,extracted.category,extracted.priority,extracted.classification_reason,extracted.confidence))
                    row = await cur.fetchone()
                    if row:
                        await cur.execute("insert into confidence_logs (user_id,obligation_id,model,confidence,decision) values (%s,%s,%s,%s,%s)", (user_id,row["id"],extracted.model,extracted.confidence,"extracted"))
                        created += 1
            topic_candidates = await _resolve_cross_source_topics(cur, user_id)
        await conn.commit()
    return {"messages_found":len(messages),"obligations_created":created,"messages_skipped":skipped,"prefilter_filtered":prefilter_filtered,"messages_sent_to_ai":messages_sent_to_ai,"topic_candidates":topic_candidates}

async def sync_calendar_and_extract(user_id: str, access_token: str) -> dict:
    events = await list_upcoming_events(access_token, days=14)
    created = skipped = 0
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            hint = await _hint(cur, user_id)
            user_email = await _user_email(cur, user_id)
            for event in events:
                external_id = event.get("id")
                if not external_id: continue
                await cur.execute("select id from obligations where user_id=%s and external_id=%s", (user_id,external_id))
                existing_obligation = await cur.fetchone()
                if existing_obligation: skipped += 1
                await cur.execute("select id from sources where user_id=%s and provider='calendar' and external_id=%s", (user_id,external_id))
                existing_source = await cur.fetchone()
                start = event.get("start", {})
                start_at = start.get("dateTime") or start.get("date")
                text = "\n".join(x for x in [f"Event: {event.get('summary','')}",f"Description: {event.get('description','')}",f"Start: {start_at}",f"Location: {event.get('location','')}"] if x)
                item_id = await _persist_context_item(cur, user_id, NormalizedItem(
                    provider="calendar", item_type="calendar_event", external_id=external_id,
                    title=(event.get("summary") or "Calendar event")[:300], body=event.get("description", ""),
                    summary=event.get("summary", ""), occurred_at=start_at,
                    metadata={"calendar_event_id": external_id, "location": event.get("location", "")},
                ))
                for attendee in event.get("attendees", []) or []:
                    email = normalize_email(attendee.get("email"))
                    if not email or email == user_email:
                        continue
                    person_id = await _persist_person(cur, user_id, PersonRef(display_name=attendee.get("displayName"), email=email))
                    if person_id:
                        await _link_item_person(cur, user_id, item_id, person_id)
                project = extract_project_hint(event.get("summary"))
                if project:
                    project_id = await _persist_project(cur, user_id, project.name)
                    if project_id:
                        await _link_item_project(cur, user_id, item_id, project_id)
                if existing_source:
                    source_id = existing_source["id"]
                    await cur.execute("update sources set last_synced_at=now(), title=%s where id=%s and user_id=%s", (event.get("summary","Calendar event")[:300],source_id,user_id))
                else:
                    await cur.execute("insert into sources (user_id,provider,external_id,title,last_synced_at) values (%s,'calendar',%s,%s,now()) returning id", (user_id,external_id,event.get("summary","Calendar event")[:300]))
                    source_id = (await cur.fetchone())["id"]
                await cur.execute("update context_items set source_id=%s, updated_at=now() where user_id=%s and provider='calendar' and external_id=%s", (source_id,user_id,external_id))
                if existing_obligation:
                    continue
                extracted = await extract_obligation(text, hint, "calendar")
                if extracted:
                    due_at = extracted.due_at or start_at
                    await cur.execute("insert into obligations (user_id,source_id,external_id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (user_id,external_id) do nothing returning id", (user_id,source_id,external_id,extracted.title,extracted.summary,due_at,extracted.amount,extracted.currency,extracted.sender,extracted.category,extracted.priority,extracted.classification_reason,extracted.confidence))
                    row = await cur.fetchone()
                    if row:
                        await cur.execute("insert into confidence_logs (user_id,obligation_id,model,confidence,decision) values (%s,%s,%s,%s,%s)", (user_id,row["id"],extracted.model,extracted.confidence,"extracted"))
                        created += 1
            topic_candidates = await _resolve_cross_source_topics(cur, user_id)
        await conn.commit()
    return {"events_found":len(events),"obligations_created":created,"events_skipped":skipped,"topic_candidates":topic_candidates}