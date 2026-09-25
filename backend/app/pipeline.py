import base64
from .db import get_connection
from .extraction import extract_obligation
from .gmail import get_message, list_recent_messages
from .calendar import list_upcoming_events

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

def gmail_text(message: dict) -> str:
    payload = message.get("payload", {})
    headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}
    body = "\n".join(x for x in _walk(payload) if x.strip()) or message.get("snippet", "")
    return "\n".join(x for x in [f"From: {headers.get('from','')}", f"To: {headers.get('to','')}", f"Subject: {headers.get('subject','')}", body] if x).strip()

async def _hint(cur, user_id: str) -> str:
    await cur.execute("select field_name,new_value,count(*) as n from corrections where user_id=%s and field_name in ('category','title') group by field_name,new_value order by n desc limit 12", (user_id,))
    rows = await cur.fetchall()
    return "; ".join(f"{r['field_name']}={r['new_value']}" for r in rows)

async def sync_gmail_and_extract(user_id: str, access_token: str) -> dict:
    messages = await list_recent_messages(access_token, days=7)
    created = skipped = 0
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            hint = await _hint(cur, user_id)
            for summary in messages:
                external_id = summary.get("id")
                if not external_id: continue
                await cur.execute("select id from sources where user_id=%s and provider='gmail' and external_id=%s", (user_id, external_id))
                if await cur.fetchone(): skipped += 1; continue
                message = await get_message(access_token, external_id)
                text = gmail_text(message)
                extracted = await extract_obligation(text, hint, "email")
                await cur.execute("insert into sources (user_id,provider,external_id,title,last_synced_at) values (%s,'gmail',%s,%s,now()) returning id", (user_id,external_id,text.splitlines()[2][:300] if len(text.splitlines())>2 else "Gmail message"))
                source_id = (await cur.fetchone())["id"]
                if extracted:
                    await cur.execute("insert into obligations (user_id,source_id,external_id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (user_id,external_id) do nothing returning id", (user_id,source_id,external_id,extracted.title,extracted.summary,extracted.due_at,extracted.amount,extracted.currency,extracted.sender,extracted.category,extracted.priority,extracted.classification_reason,extracted.confidence))
                    row = await cur.fetchone()
                    if row:
                        await cur.execute("insert into confidence_logs (user_id,obligation_id,model,confidence,decision) values (%s,%s,%s,%s,%s)", (user_id,row["id"],"claude-sonnet-4-5",extracted.confidence,"extracted"))
                        created += 1
        await conn.commit()
    return {"messages_found":len(messages),"obligations_created":created,"messages_skipped":skipped}

async def sync_calendar_and_extract(user_id: str, access_token: str) -> dict:
    events = await list_upcoming_events(access_token, days=14)
    created = skipped = 0
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            hint = await _hint(cur, user_id)
            for event in events:
                external_id = event.get("id")
                if not external_id: continue
                await cur.execute("select id from sources where user_id=%s and provider='calendar' and external_id=%s", (user_id,external_id))
                if await cur.fetchone(): skipped += 1; continue
                start = event.get("start", {})
                start_at = start.get("dateTime") or start.get("date")
                text = "\n".join(x for x in [f"Event: {event.get('summary','')}",f"Description: {event.get('description','')}",f"Start: {start_at}",f"Location: {event.get('location','')}"] if x)
                extracted = await extract_obligation(text, hint, "calendar")
                await cur.execute("insert into sources (user_id,provider,external_id,title,last_synced_at) values (%s,'calendar',%s,%s,now()) returning id", (user_id,external_id,event.get("summary","Calendar event")[:300]))
                source_id = (await cur.fetchone())["id"]
                if extracted:
                    due_at = extracted.due_at or start_at
                    await cur.execute("insert into obligations (user_id,source_id,external_id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (user_id,external_id) do nothing returning id", (user_id,source_id,external_id,extracted.title,extracted.summary,due_at,extracted.amount,extracted.currency,extracted.sender,extracted.category,extracted.priority,extracted.classification_reason,extracted.confidence))
                    row = await cur.fetchone()
                    if row:
                        await cur.execute("insert into confidence_logs (user_id,obligation_id,model,confidence,decision) values (%s,%s,%s,%s,%s)", (user_id,row["id"],"claude-sonnet-4-5",extracted.confidence,"extracted"))
                        created += 1
        await conn.commit()
    return {"events_found":len(events),"obligations_created":created,"events_skipped":skipped}