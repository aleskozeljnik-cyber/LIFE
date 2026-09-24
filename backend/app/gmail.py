import httpx

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"

async def list_recent_messages(access_token: str, days: int = 7, max_results: int = 100):
    q = f"newer_than:{days}d"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{GMAIL_API}/messages", params={"q": q, "maxResults": max_results}, headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        return r.json().get("messages", [])

async def get_message(access_token: str, message_id: str):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{GMAIL_API}/messages/{message_id}", params={"format": "full"}, headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        return r.json()
