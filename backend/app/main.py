from datetime import date
from fastapi import Cookie, FastAPI, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ai import ai_data_usage_status, ai_runtime_configured, configured_provider, real_data_processing_allowed
from .auth import new_state, read_session, read_state, sign_session
from .calendar import list_upcoming_events
from .config import settings
from .db import get_connection
from .google import authorization_url, exchange_code, fetch_userinfo, revoke_token
from .microsoft import authorization_url as microsoft_authorization_url, exchange_code as microsoft_exchange_code, fetch_userinfo as microsoft_fetch_userinfo
from .intelligence import get_today_life_items
from .jobs import get_google_access_token, run_user_sync
from .summary import generate_today_summary
from .security import encrypt_token, decrypt_token
from .telemetry import record_usage_event

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
        return {"status": "ok", "service": "life-api", "database": bool(row and row["db"] == 1), "google_oauth_configured": bool(settings.google_client_id and settings.google_client_secret), "ai_enabled": ai_runtime_configured(), "ai_provider": configured_provider(), "ai_data_usage": ai_data_usage_status()}
    except Exception:
        return {"status": "degraded", "service": "life-api", "database": False, "google_oauth_configured": bool(settings.google_client_id and settings.google_client_secret), "ai_enabled": ai_runtime_configured(), "ai_provider": configured_provider(), "ai_data_usage": ai_data_usage_status()}

@app.get("/auth/google/start")
def google_start():
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = new_state()
    redirect = RedirectResponse(authorization_url(state), status_code=303)
    redirect.set_cookie("life_oauth_state", state, httponly=True, secure=True, samesite="none", max_age=600)
    return redirect

@app.get("/auth/google/callback")
async def google_callback(code: str, state: str, response: Response, life_oauth_state: str | None = Cookie(default=None)):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    try:
        read_state(state)
        if not life_oauth_state or life_oauth_state != state:
            raise ValueError("OAuth state mismatch")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    tokens = await exchange_code(code)
    userinfo = await fetch_userinfo(tokens["access_token"])
    if not real_data_processing_allowed():
        raise HTTPException(
            status_code=503,
            detail=f"Privacy gate: real-data processing blocked because AI data policy is {ai_data_usage_status()}. Configure a provider with no training use before connecting user data.",
        )
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
    redirect.delete_cookie("life_oauth_state", secure=True, samesite="none")
    redirect.set_cookie("life_session", sign_session(str(user_id)), httponly=True, secure=True, samesite="none", max_age=60*60*24*30)
    await record_usage_event(str(user_id), "authorization_connected", {"provider": "google", "status": "success"})
    return redirect

@app.get("/auth/status")
async def auth_status(life_session: str | None = Cookie(default=None)):
    if not life_session:
        return {"authenticated": False, "google_connected": False}
    try:
        user_id = current_user(life_session)
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select id,email,name from users where id=%s", (user_id,))
                user = await cur.fetchone()
                await cur.execute("select provider from oauth_tokens where user_id=%s and provider in ('google','microsoft')", (user_id,))
                providers = {row["provider"] for row in await cur.fetchall()}
                connected = "google" in providers
                microsoft_connected = "microsoft" in providers
        if not user:
            return {"authenticated": False, "google_connected": False}
        return {"authenticated": True, "google_connected": connected, "microsoft_connected": microsoft_connected, "user": user}
    except HTTPException:
        return {"authenticated": False, "google_connected": False}

@app.get("/auth/microsoft/start")
def microsoft_start():
    if not settings.microsoft_client_id or not settings.microsoft_client_secret:
        raise HTTPException(status_code=503, detail="Microsoft OAuth is not configured")
    state = new_state()
    redirect = RedirectResponse(microsoft_authorization_url(state), status_code=303)
    redirect.set_cookie("life_oauth_state", state, httponly=True, secure=True, samesite="none", max_age=600)
    return redirect

@app.get("/auth/microsoft/callback")
async def microsoft_callback(code: str, state: str, response: Response, life_oauth_state: str | None = Cookie(default=None)):
    try:
        read_state(state)
        if not life_oauth_state or life_oauth_state != state:
            raise ValueError("OAuth state mismatch")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    tokens = await microsoft_exchange_code(code)
    userinfo = await microsoft_fetch_userinfo(tokens["access_token"])
    if not real_data_processing_allowed():
        raise HTTPException(status_code=503, detail=f"Privacy gate: real-data processing blocked because AI data policy is {ai_data_usage_status()}. Configure a provider with no training use before connecting user data.")
    microsoft_sub = userinfo.get("id")
    email = (userinfo.get("mail") or userinfo.get("userPrincipalName") or "").strip().lower()
    name = userinfo.get("displayName")
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select id from users where microsoft_sub=%s or (email=%s and %s <> '') limit 1", (microsoft_sub,email,email))
            existing = await cur.fetchone()
            if existing:
                user_id = existing["id"]
                await cur.execute("update users set microsoft_sub=coalesce(microsoft_sub,%s), email=coalesce(email,%s), name=coalesce(%s,name), updated_at=now() where id=%s", (microsoft_sub,email,name,user_id))
            else:
                await cur.execute("insert into users (microsoft_sub,email,name) values (%s,%s,%s) returning id", (microsoft_sub,email,name))
                user_id = (await cur.fetchone())["id"]
            await cur.execute("""insert into oauth_tokens (user_id,provider,access_token_encrypted,refresh_token_encrypted,expires_at,scopes)
                values (%s,'microsoft',%s,%s,now()+(%s || ' seconds')::interval,%s)
                on conflict (user_id,provider) do update set access_token_encrypted=excluded.access_token_encrypted,
                refresh_token_encrypted=coalesce(excluded.refresh_token_encrypted,oauth_tokens.refresh_token_encrypted),expires_at=excluded.expires_at,scopes=excluded.scopes,updated_at=now()""",
                (user_id,encrypt_token(tokens["access_token"]),encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else None,tokens.get("expires_in",3600),tokens.get("scope","").split()))
        await conn.commit()
    target = settings.frontend_url.rstrip("/") + "/?connected=microsoft"
    redirect = RedirectResponse(target,status_code=303)
    redirect.delete_cookie("life_oauth_state",secure=True,samesite="none")
    redirect.set_cookie("life_session",sign_session(str(user_id)),httponly=True,secure=True,samesite="none",max_age=60*60*24*30)
    await record_usage_event(str(user_id),"authorization_connected",{"provider":"microsoft","status":"success"})
    return redirect

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("life_session", httponly=True, secure=True, samesite="none")
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
            # Disconnect only the provider explicitly represented by this endpoint.
            # Microsoft credentials must never be deleted as a side effect of
            # revoking Google access.
            await cur.execute("delete from oauth_tokens where user_id=%s and provider='google'", (user_id,))
        await conn.commit()
    await record_usage_event(str(user_id), "authorization_revoked", {"provider": "google", "status": "success"})
    return {"status": "google_revoked"}

@app.post("/telemetry")
async def telemetry_event(payload: dict, life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    action = str(payload.get("action", ""))
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    await record_usage_event(user_id, action, metadata)
    return {"status": "accepted"}

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

# IMPORTANT: fixed-route provider sync endpoints must be declared before
# the parameterized /sources/{source_id}/sync route, otherwise "gmail" and
# "calendar" are captured as source_id and PostgreSQL rejects them as UUIDs.
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

@app.post("/sources/outlook-mail/sync")
async def outlook_mail_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    result = await run_user_sync(user_id, "outlook_mail")
    return {"provider": "outlook_mail", "result": result["outlook_mail"]}

@app.post("/sources/outlook-calendar/sync")
async def outlook_calendar_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    result = await run_user_sync(user_id, "outlook_calendar")
    return {"provider": "outlook_calendar", "result": result["outlook_calendar"]}

@app.post("/sources/teams/sync")
async def teams_sync(life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    result = await run_user_sync(user_id, "teams")
    return {"provider": "teams", "result": result["teams"]}

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

@app.get("/life-items")
async def life_items(limit: int = Query(default=3, ge=1, le=20), life_session: str | None = Cookie(default=None), response: Response = None):
    user_id = current_user(life_session)
    try:
        items = await get_today_life_items(user_id, limit=limit)
        # Enrich only from source-backed Context Core relationships.
        # No names/projects are inferred at API presentation time.
        obligation_ids = [str(item.get("id")) for item in items if item.get("id")]
        related_by_obligation = {}
        if obligation_ids:
            async with await get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """select
                             ce.obligation_id,
                             coalesce(
                               jsonb_agg(distinct jsonb_build_object(
                                 'id', p.id,
                                 'name', p.display_name,
                                 'email', p.primary_email
                               )) filter (where p.id is not null),
                               '[]'::jsonb
                             ) as related_people,
                             coalesce(
                               jsonb_agg(distinct jsonb_build_object(
                                 'id', pr.id,
                                 'name', pr.name,
                                 'kind', pr.kind
                               )) filter (where pr.id is not null),
                               '[]'::jsonb
                             ) as related_projects
                           from context_evidence ce
                           left join context_relationships cr
                             on cr.user_id=ce.user_id
                            and cr.from_item_id=ce.context_item_id
                           left join people p
                             on p.id=cr.to_person_id
                            and p.user_id=ce.user_id
                           left join projects pr
                             on pr.id=cr.project_id
                            and pr.user_id=ce.user_id
                           where ce.user_id=%s
                             and ce.obligation_id = any(%s::uuid[])
                           group by ce.obligation_id""",
                        (user_id, obligation_ids),
                    )
                    for row in await cur.fetchall():
                        related_by_obligation[str(row["obligation_id"])] = {
                            "related_people": row["related_people"] or [],
                            "related_projects": row["related_projects"] or [],
                        }
        for item in items:
            related = related_by_obligation.get(str(item.get("id")), {})
            item["related_people"] = related.get("related_people", [])
            item["related_projects"] = related.get("related_projects", [])
        if response is not None:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return items
    except Exception as exc:
        raise HTTPException(status_code=503, detail="LIFE intelligence is not ready yet. Run the database migration first.") from exc

@app.get("/obligations")
async def obligations(target_date: date | None = None, date_param: date | None = Query(default=None, alias="date"), life_session: str | None = Cookie(default=None)):
    user_id = current_user(life_session)
    target = target_date or date_param or date.today()
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                select o.id,o.title,o.summary,o.due_at,o.amount,o.currency,o.sender,s.provider, o.category,o.priority,o.classification_reason,o.confidence,o.status,o.source_id
                from obligations o
                left join sources s on s.id=o.source_id
                where o.user_id=%s and (due_at is null or due_at::date=%s)
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
    content = await generate_today_summary(user_id)
    return {"content": content, "summary_date": date.today()}

@app.get("/calendar/upcoming")
async def calendar_upcoming(
    days: int = Query(default=14, ge=1, le=14),
    life_session: str | None = Cookie(default=None),
):
    user_id = current_user(life_session)
    try:
        access_token = await get_google_access_token(user_id)
        events = await list_upcoming_events(access_token, days=days)
        return [
            {
                "id": event.get("id"),
                "summary": event.get("summary") or "Untitled event",
                "description": event.get("description") or "",
                "location": event.get("location") or "",
                "start": event.get("start") or {},
                "end": event.get("end") or {},
            }
            for event in events if event.get("id")
        ]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Calendar sync failed. Please retry.") from exc
