from .db import get_connection
from .extraction import extract_obligation
from .gmail import get_message, list_recent_messages
from .security import decrypt_token

def gmail_text(message: dict) -> str:
    payload = message.get("payload", {})
    headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}
    return "\n".join(x for x in [f"From: {headers.get('from','')}", f"Subject: {headers.get('subject','')}", message.get("snippet", "")] if x)

async def sync_gmail_and_extract(user_id: str, access_token: str) -> dict:
    messages = await list_recent_messages(access_token, days=7)
    created = skipped = 0
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            for summary in messages:
                external_id = summary.get("id")
                if not external_id: continue
                await cur.execute("select id from sources where user_id=%s and provider='gmail' and external_id=%s", (user_id, external_id))
                if await cur.fetchone(): skipped += 1; continue
                message = await get_message(access_token, external_id)
                extracted = await extract_obligation(gmail_text(message))
                await cur.execute("insert into sources (user_id,provider,external_id,title,last_synced_at) values (%s,'gmail',%s,%s,now()) returning id", (user_id, external_id, (gmail_text(message).splitlines()[1] if len(gmail_text(message).splitlines())>1 else "Gmail message")[:300]))
                source_id = (await cur.fetchone())["id"]
                if extracted:
                    await cur.execute("insert into obligations (user_id,source_id,external_id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (user_id,external_id) do nothing", (user_id,source_id,external_id,extracted.title,extracted.summary,extracted.due_at,extracted.amount,extracted.currency,extracted.sender,extracted.category,extracted.priority,extracted.classification_reason,extracted.confidence))
                    await cur.execute("insert into confidence_logs (user_id,obligation_id,model,confidence,decision) select %s,id,'claude-sonnet-4-5',%s,'extracted' from obligations where user_id=%s and external_id=%s", (user_id,extracted.confidence,user_id,external_id))
                    created += 1
        await conn.commit()
    return {"messages_found":len(messages),"obligations_created":created,"messages_skipped":skipped}
