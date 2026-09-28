import httpx

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"


async def list_recent_messages(access_token: str, days: int = 7, max_results: int = 2500):
    q = f"newer_than:{days}d"
    messages = []
    page_token = None
    async with httpx.AsyncClient(timeout=20) as client:
        while len(messages) < max_results:
            params = {"q": q, "maxResults": min(500, max_results - len(messages))}
            if page_token:
                params["pageToken"] = page_token
            r = await client.get(
                f"{GMAIL_API}/messages",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            payload = r.json()
            messages.extend(payload.get("messages", []))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
    return messages[:max_results]


async def get_message(access_token: str, message_id: str):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"{GMAIL_API}/messages/{message_id}",
            params={"format": "full"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        r.raise_for_status()
        return r.json()
