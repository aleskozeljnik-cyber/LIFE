from urllib.parse import urlencode
import httpx
from fastapi import HTTPException
from .config import settings

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
MS_AUTH_BASE = "https://login.microsoftonline.com"
MS_SCOPES = ["openid", "profile", "email", "offline_access", "User.Read", "Mail.Read", "Calendars.Read", "Chat.Read"]


def authorization_url(state: str) -> str:
    if not settings.microsoft_client_id:
        raise HTTPException(status_code=503, detail="Microsoft OAuth is not configured")
    params = {
        "client_id": settings.microsoft_client_id,
        "response_type": "code",
        "redirect_uri": settings.microsoft_redirect_uri,
        "response_mode": "query",
        "scope": " ".join(MS_SCOPES),
        "state": state,
        "prompt": "select_account",
    }
    return f"{MS_AUTH_BASE}/{settings.microsoft_tenant}/oauth2/v2.0/authorize?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{MS_AUTH_BASE}/{settings.microsoft_tenant}/oauth2/v2.0/token",
            data={
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "code": code,
                "redirect_uri": settings.microsoft_redirect_uri,
                "grant_type": "authorization_code",
                "scope": " ".join(MS_SCOPES),
            },
        )
        if response.is_error:
            try:
                payload = response.json()
            except Exception:
                payload = {}
            raise HTTPException(status_code=502, detail={"provider":"microsoft","message":"OAuth token exchange failed","error":payload.get("error"),"error_description":payload.get("error_description")})
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{MS_AUTH_BASE}/{settings.microsoft_tenant}/oauth2/v2.0/token",
            data={
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": " ".join(MS_SCOPES),
            },
        )
        response.raise_for_status()
        return response.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{GRAPH_BASE}/me", headers={"Authorization": f"Bearer {access_token}"})
        response.raise_for_status()
        return response.json()


async def graph_get(access_token: str, path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{GRAPH_BASE}{path}", headers={"Authorization": f"Bearer {access_token}", "Prefer": 'IdType="ImmutableId"'}, params=params)
        response.raise_for_status()
        return response.json()


async def list_messages(access_token: str, limit: int = 100) -> list[dict]:
    params = {"$top": min(limit, 100), "$select": "id,subject,bodyPreview,receivedDateTime,from,toRecipients,ccRecipients,webLink,isRead"}
    data = await graph_get(access_token, "/me/mailFolders/inbox/messages", params)
    return data.get("value", [])


async def list_events(access_token: str, days: int = 14, limit: int = 100) -> list[dict]:
    from datetime import datetime, timezone, timedelta
    start = datetime.now(timezone.utc)
    end = start + timedelta(days=days)
    params = {
        "startDateTime": start.isoformat(),
        "endDateTime": end.isoformat(),
        "$top": min(limit, 100),
        "$select": "id,subject,bodyPreview,start,end,location,attendees,webLink,organizer,isOnlineMeeting,onlineMeetingUrl",
        "$orderby": "start/dateTime",
    }
    data = await graph_get(access_token, "/me/calendarView", params)
    return data.get("value", [])


async def list_chats(access_token: str, limit: int = 50) -> list[dict]:
    params = {
        "$top": min(limit, 50),
        "$select": "id,topic,chatType,webUrl,lastUpdatedDateTime",
    }
    data = await graph_get(access_token, "/me/chats", params)
    return data.get("value", [])


async def list_chat_messages(access_token: str, chat_id: str, limit: int = 50) -> list[dict]:
    params = {
        "$top": min(limit, 50),
        "$select": "id,replyToId,etag,messageType,createdDateTime,lastModifiedDateTime,from,body,webUrl",
        "$orderby": "createdDateTime desc",
    }
    data = await graph_get(access_token, f"/me/chats/{chat_id}/messages", params)
    return data.get("value", [])
