from datetime import date
from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .auth import new_state, sign_session, read_session
from .calendar import list_upcoming_events
from .config import settings
from .db import get_connection
from .google import authorization_url, exchange_code, fetch_userinfo, revoke_token
from .jobs import run_user_sync
from .security import encrypt_token, decrypt_token

app = FastAPI(title="LIFE API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def health():
    try:
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select 1 as db")
                row = await cur.fetchone()
        return {"status": "ok", "service": "life-api", "database": bool(row and row["db"] == 1)}
    except Exception as exc:
        return {"status": "degraded", "service": "life-api", "database": False, "error": str(exc)[:200]}

@app.get("/auth/google/start")
def google_start(response: Response):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = new_state()
    response.set_cookie("life_oauth_state", state, httponly=True, secure=True, samesite="lax", max_age=600)
    return {"authorization_url": authorization_url(state)}

@app.get("/auth/google/callback")
async def google_callback(code: str, state: str, life_oauth_state: str | None = Cookie(default=None)):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    if not life_oauth_state or state != life_oauth_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
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
                on conflict (user_id, provider) do update set
                    access_token_encrypted=excluded.access_token_encrypted,
                    refresh_token_encrypted=coalesce(excluded.refresh_token_encrypted, oauth_tokens.refresh_token_encrypted),
                    expires_at=excluded.expires_at, scopes=excluded.scopes, updated_at=now()
            """, (
                user_id,
                encrypt_token(tokens["access_token"]),
                encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else None,
                tokens.get("expires_in", 3600),
                tokens.get("scope", "").split(),
            ))
        await conn.commit()
    target = settings.frontend_url.rstrip("/") + "/?connected=1"
    redirect = RedirectResponse(target, status_code=303)
    redirect.set_cookie("life_session", sign_session(str(user_id)), httponly=True, secure=True, samesite="lax", max_age=60*60*24*30)
    redirect.delete_cookie("life_oauth_state")
    return redirect

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("life_session")
    return {"status": "logged_out"}

@app.post("/auth/revoke")
async def revoke(response: Response, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted from oauth_tokens where user_id=%s and provider='google'", (user_id,))
            token = await cur.fetchone()
            if token:
                try:
                    await revoke_token(decrypt_token(token["access_token_encrypted"]))
                except Exception:
                    pass
            await cur.execute("delete from oauth_tokens where user_id=%s", (user_id,))
        await conn.commit()
    response.delete_cookie("life_session")
    return {"status": "revoked"}

@app.get("/users/me")
async def me(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select id,email,name,created_at,updated_at from users where id=%s", (user_id,))
            user = await cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/me/export")
async def export_user(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            data = {}
            for name, query in [
                ("user", "select id,email,name,created_at,updated_at from users where id=%s"),
                ("sources", "select id,provider,external_id,title,last_synced_at,created_at from sources where user_id=%s"),
                ("obligations", "select id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence,status,source_id,created_at,updated_at from obligations where user_id=%s"),
                ("corrections", "select id,obligation_id,field_name,old_value,new_value,created_at from corrections where user_id=%s"),
                ("summaries", "select summary_date,content,created_at from daily_summaries where user_id=%s"),
            ]:
                await cur.execute(query, (user_id,))
                data[name] = await cur.fetchall()
    return data

@app.delete("/users/me")
async def delete_user(response: Response, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select access_token_encrypted from oauth_tokens where user_id=%s and provider='google'", (user_id,))
            token = await cur.fetchone()
            if token:
                try:
                    await revoke_token(decrypt_token(token["access_token_encrypted"]))
                except Exception:
                    pass
            await cur.execute("delete from users where id=%s", (user_id,))
        await conn.commit()
    response.delete_cookie("life_session")
    return {"status": "deleted"}

@app.get("/sources")
async def sources(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select id,provider,title,last_synced_at,created_at from sources where user_id=%s order by created_at desc", (user_id,))
            return await cur.fetchall()

@app.post("/sources/{source_id}/sync")
async def sync_source(source_id: str, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select provider from sources where id=%s and user_id=%s", (source_id, user_id))
            source = await cur.fetchone()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"source_id": source_id, "result": await run_user_sync(user_id, source["provider"])}

@app.get("/obligations")
async def obligations(target_date: date | None = None, date_param: date | None = None, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    target = target_date or date_param or date.today()
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                select id,title,summary,due_at,amount,currency,sender,category,priority,classification_reason,confidence,status,source_id
                from obligations
                where user_id=%s and (due_at is null or due_at::date=%s)
                order by case priority when 'high' then 1 when 'medium' then 2 else 3 end, due_at nulls last
            """, (user_id, target))
            return await cur.fetchall()

@app.patch("/obligations/{obligation_id}")
async def update_obligation(obligation_id: str, patch: ObligationPatch, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    allowed = {"status", "category", "title"}
    values = {k: v for k, v in patch.model_dump().items() if v is not None and k in allowed}
    if not values:
        return {"status": "unchanged"}
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select status,category,title from obligations where id=%s and user_id=%s", (obligation_id, user_id))
            old = await cur.fetchone()
            if not old:
                raise HTTPException(status_code=404, detail="Obligation not found")
            for field, value in values.items():
                await cur.execute(f"update obligations set {field}=%s, updated_at=now() where id=%s and user_id=%s", (value, obligation_id, user_id))
                await cur.execute("insert into corrections (user_id,obligation_id,field_name,old_value,new_value) values (%s,%s,%s,%s,%s)", (user_id, obligation_id, field, old[field], value))
        await conn.commit()
    return {"status": "updated"}

@app.post("/obligations/{obligation_id}/dismiss")
async def dismiss_obligation(obligation_id: str, life_session: str | None = Cookie(default=None)):
    return await update_obligation(obligation_id, ObligationPatch(status="dismissed"), life_session)

@app.get("/summaries/today")
async def today_summary(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select content,summary_date from daily_summaries where user_id=%s and summary_date=current_date", (user_id,))
            row = await cur.fetchone()
    return row or {"content": "No summary generated yet.", "summary_date": date.today()}

@app.post("/sources/gmail/sync")
async def gmail_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    result = await run_user_sync(user_id, "gmail")
    return {"provider": "gmail", "result": result["gmail"]}

@app.post("/sources/calendar/sync")
async def calendar_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    result = await run_user_sync(user_id, "calendar")
    return {"provider": "calendar", "result": result["calendar"]}
