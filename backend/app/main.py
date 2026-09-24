from datetime import date
from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .auth import new_state, sign_session, read_session
from .calendar import list_upcoming_events
from .config import settings
from .db import get_connection
from .gmail import list_recent_messages
from .google import authorization_url, exchange_code, fetch_userinfo
from .security import encrypt_token

app = FastAPI(title="LIFE API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ObligationPatch(BaseModel):
    status: str | None = None
    category: str | None = None
    title: str | None = None


def current_user(session: str | None):
    if not session:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return read_session(session)["user_id"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc

@app.get("/health")
def health():
    return {"status": "ok", "service": "life-api"}

@app.get("/auth/google/start")
def google_start():
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    return {"authorization_url": authorization_url(new_state())}

@app.get("/auth/google/callback")
async def google_callback(code: str, response: Response):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    tokens = await exchange_code(code)
    userinfo = await fetch_userinfo(tokens["access_token"])
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                insert into users (google_sub, email, name) values (%s,%s,%s)
                on conflict (google_sub) do update set email=excluded.email, name=excluded.name, updated_at=now()
                returning id
            """, (userinfo["sub"], userinfo["email"], userinfo.get("name")))
            user_id = (await cur.fetchone())["id"]
            await cur.execute("""
                insert into oauth_tokens (user_id, provider, access_token_encrypted, refresh_token_encrypted, expires_at, scopes)
                values (%s,'google',%s,%s,now() + (%s || ' seconds')::interval,%s)
                on conflict (user_id, provider) do update set access_token_encrypted=excluded.access_token_encrypted, refresh_token_encrypted=coalesce(excluded.refresh_token_encrypted, oauth_tokens.refresh_token_encrypted), expires_at=excluded.expires_at, scopes=excluded.scopes, updated_at=now()
            """, (user_id, encrypt_token(tokens["access_token"]), encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else None, tokens.get("expires_in", 3600), tokens.get("scope", "").split()))
        await conn.commit()
    response.set_cookie("life_session", sign_session(str(user_id)), httponly=True, secure=True, samesite="lax", max_age=60*60*24*30)
    return {"status": "connected"}

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("life_session")
    return {"status": "logged_out"}

@app.get("/users/me")
async def me(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select id,email,name,created_at,updated_at from users where id=%s", (user_id,))
            user = await cur.fetchone()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/sources")
async def sources(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select id,provider,title,last_synced_at,created_at from sources where user_id=%s order by created_at desc", (user_id,))
            return await cur.fetchall()

@app.get("/obligations")
async def obligations(target_date: date, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""select id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence,status,source_id from obligations where user_id=%s and (due_at is null or due_at::date=%s) order by due_at nulls last""", (user_id, target_date))
            return await cur.fetchall()

@app.patch("/obligations/{obligation_id}")
async def update_obligation(obligation_id: str, patch: ObligationPatch, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    values = {k:v for k,v in patch.model_dump().items() if v is not None}
    if not values: return {"status":"unchanged"}
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            for field, value in values.items():
                await cur.execute(f"update obligations set {field}=%s, updated_at=now() where id=%s and user_id=%s", (value, obligation_id, user_id))
                if field in {"category","status","title"}:
                    await cur.execute("insert into corrections (user_id,obligation_id,field_name,new_value) values (%s,%s,%s,%s)", (user_id, obligation_id, field, value))
        await conn.commit()
    return {"status":"updated"}

@app.get("/summaries/today")
async def today_summary(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select content,summary_date from daily_summaries where user_id=%s and summary_date=current_date", (user_id,))
            row = await cur.fetchone()
    return row or {"content":"No summary generated yet.","summary_date":date.today()}

@app.post("/sources/gmail/sync")
async def gmail_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted from oauth_tokens where user_id=%s and provider='google'", (user_id,))
            token = await cur.fetchone()
    if not token: raise HTTPException(status_code=404, detail="Google account not connected")
    from .security import decrypt_token
    messages = await list_recent_messages(decrypt_token(token["access_token_encrypted"]))
    return {"provider":"gmail","messages_found":len(messages),"status":"fetched"}

@app.post("/sources/calendar/sync")
async def calendar_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted from oauth_tokens where user_id=%s and provider='google'", (user_id,))
            token = await cur.fetchone()
    if not token: raise HTTPException(status_code=404, detail="Google account not connected")
    from .security import decrypt_token
    events = await list_upcoming_events(decrypt_token(token["access_token_encrypted"]))
    return {"provider":"calendar","events_found":len(events),"status":"fetched"}
