import httpx
from datetime import datetime, timezone, timedelta

CALENDAR_API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


async def list_upcoming_events(access_token: str, days: int = 14, max_results: int = 2500):
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    events = []
    page_token = None
    async with httpx.AsyncClient(timeout=20) as client:
        while len(events) < max_results:
            params = {
                "timeMin": now.isoformat(),
                "timeMax": end.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": min(2500, max_results - len(events)),
            }
            if page_token:
                params["pageToken"] = page_token
            r = await client.get(
                CALENDAR_API,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            payload = r.json()
            events.extend(payload.get("items", []))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
    return events[:max_results]
