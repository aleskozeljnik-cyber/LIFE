from psycopg.types.json import Jsonb
from .db import get_connection
from .google import refresh_access_token
from .pipeline import sync_gmail_and_extract, sync_calendar_and_extract
from .security import decrypt_token, encrypt_token

async def get_google_access_token(user_id: str) -> str:
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

async def run_user_sync(user_id: str, provider: str | None = None) -> dict:
    access_token = await get_google_access_token(user_id)
    result = {}
    if provider in (None, "gmail"): result["gmail"] = await sync_gmail_and_extract(user_id, access_token)
    if provider in (None, "calendar"): result["calendar"] = await sync_calendar_and_extract(user_id, access_token)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("insert into usage_logs (user_id,action,metadata) values (%s,%s,%s)", (user_id,"sync",Jsonb({"provider":provider,"result":result})))
        await conn.commit()
    return result
