from .db import get_connection
from .pipeline import sync_gmail_and_extract
from .security import decrypt_token

async def run_user_sync(user_id: str) -> dict:
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted from oauth_tokens where user_id=%s and provider='google'", (user_id,))
            token = await cur.fetchone()
    if not token: raise RuntimeError("Google account not connected")
    return await sync_gmail_and_extract(user_id, decrypt_token(token["access_token_encrypted"]))
