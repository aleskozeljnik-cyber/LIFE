from psycopg.types.json import Jsonb
from .db import get_connection
from fastapi import HTTPException
from .ai import ai_data_usage_status, real_data_processing_allowed
from .google import refresh_access_token
from .pipeline import sync_gmail_and_extract, sync_calendar_and_extract
from .security import decrypt_token, encrypt_token

async def get_google_access_token(user_id: str) -> str:
    if not real_data_processing_allowed():
        raise HTTPException(status_code=503, detail=f"Real-data processing blocked: AI data policy is {ai_data_usage_status()}. Configure a provider with no training use before syncing user data.")
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted,refresh_token_encrypted,expires_at from oauth_tokens where user_id=%s and provider='google'", (user_id,))
            token = await cur.fetchone()
            if not token: raise RuntimeError("Google account not connected")
            access_token = decrypt_token(token["access_token_encrypted"])
            if token["expires_at"] is not None:
                from datetime import datetime, timezone, timedelta
                if token["expires_at"] <= datetime.now(timezone.utc) + timedelta(minutes=2) and token["refresh_token_encrypted"]:
                    refreshed = await refresh_access_token(decrypt_token(token["refresh_token_encrypted"]))
                    access_token = refreshed["access_token"]
                    await cur.execute("update oauth_tokens set access_token_encrypted=%s,expires_at=now()+(%s || ' seconds')::interval,updated_at=now() where user_id=%s and provider='google'", (encrypt_token(access_token), refreshed.get("expires_in",3600), user_id))
                    await conn.commit()
            return access_token

def safe_sync_metadata(result: dict) -> dict:
    """Allow-list only numeric/technical sync telemetry; never source content."""
    safe_result = {}
    for source_name in ("gmail", "calendar"):
        item = result.get(source_name)
        if not isinstance(item, dict):
            continue
        safe_result[source_name] = {
            key: int(item[key])
            for key in (
                "messages_found", "events_found", "obligations_created",
                "messages_skipped", "events_skipped", "prefilter_filtered", "messages_sent_to_ai",
            )
            if key in item
        }
    return {"result": safe_result}

async def run_user_sync(user_id: str, provider: str | None = None) -> dict:
    access_token = await get_google_access_token(user_id)
    result = {}
    if provider in (None, "gmail"): result["gmail"] = await sync_gmail_and_extract(user_id, access_token)
    if provider in (None, "calendar"): result["calendar"] = await sync_calendar_and_extract(user_id, access_token)
    safe_metadata = safe_sync_metadata(result)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("insert into usage_logs (user_id,action,metadata) values (%s,%s,%s)", (user_id,"sync",Jsonb({"provider": provider, "status": "success", **safe_metadata})))
        await conn.commit()
    return result
