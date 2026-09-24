import httpx
from datetime import datetime, timezone, timedelta

CALENDAR_API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

async def list_upcoming_events(access_token: str, days: int = 14):
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(CALENDAR_API, params={"timeMin": now.isoformat(), "timeMax": end.isoformat(), "singleEvents": "true", "orderBy": "startTime", "maxResults": 2500}, headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        return r.json().get("items", [])
