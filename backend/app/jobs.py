from .db import get_connection
from fastapi import HTTPException
from .ai import ai_data_usage_status, real_data_processing_allowed
from .google import refresh_access_token
from .microsoft import refresh_access_token as microsoft_refresh_access_token
from .pipeline import sync_gmail_and_extract, sync_calendar_and_extract, sync_outlook_mail_and_extract, sync_outlook_calendar_and_extract
from .security import decrypt_token, encrypt_token
from .telemetry import record_usage_event, safe_sync_metadata

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

async def get_microsoft_access_token(user_id: str) -> str:
    if not real_data_processing_allowed():
        raise HTTPException(status_code=503, detail=f"Real-data processing blocked: AI data policy is {ai_data_usage_status()}. Configure a provider with no training use before syncing user data.")
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted,refresh_token_encrypted,expires_at from oauth_tokens where user_id=%s and provider='microsoft'", (user_id,))
            token = await cur.fetchone()
            if not token:
                raise RuntimeError("Microsoft account not connected")
            access_token = decrypt_token(token["access_token_encrypted"])
            if token["expires_at"] is not None:
                from datetime import datetime, timezone, timedelta
                if token["expires_at"] <= datetime.now(timezone.utc) + timedelta(minutes=2) and token["refresh_token_encrypted"]:
                    refreshed = await microsoft_refresh_access_token(decrypt_token(token["refresh_token_encrypted"]))
                    access_token = refreshed["access_token"]
                    await cur.execute("update oauth_tokens set access_token_encrypted=%s,expires_at=now()+(%s || ' seconds')::interval,refresh_token_encrypted=coalesce(%s,refresh_token_encrypted),updated_at=now() where user_id=%s and provider='microsoft'", (encrypt_token(access_token),refreshed.get("expires_in",3600),encrypt_token(refreshed["refresh_token"]) if refreshed.get("refresh_token") else None,user_id))
                    await conn.commit()
            return access_token


async def run_user_sync(user_id: str, provider: str | None = None) -> dict:
    try:
        result = {}
        if provider in ("outlook_mail", "outlook_calendar"):
            access_token = await get_microsoft_access_token(user_id)
            if provider == "outlook_mail": result["outlook_mail"] = await sync_outlook_mail_and_extract(user_id, access_token)
            if provider == "outlook_calendar": result["outlook_calendar"] = await sync_outlook_calendar_and_extract(user_id, access_token)
        else:
            access_token = await get_google_access_token(user_id)
            if provider in (None, "gmail"): result["gmail"] = await sync_gmail_and_extract(user_id, access_token)
            if provider in (None, "calendar"): result["calendar"] = await sync_calendar_and_extract(user_id, access_token)
        safe_metadata = safe_sync_metadata(result)
        await record_usage_event(user_id, "sync", {"provider": provider, "status": "success", **safe_metadata})
        return result
    except HTTPException as exc:
        await record_usage_event(user_id, "sync_error", {"provider": provider, "status": "blocked" if exc.status_code == 503 else "error", "status_code": exc.status_code})
        raise
    except Exception:
        await record_usage_event(user_id, "sync_error", {"provider": provider, "status": "error", "status_code": 502})
        raise
