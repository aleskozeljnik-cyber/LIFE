from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings

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

@app.get("/health")
def health():
    return {"status": "ok", "service": "life-api"}

@app.get("/users/me")
def me():
    raise HTTPException(status_code=401, detail="Authentication required")

@app.get("/sources")
def sources():
    raise HTTPException(status_code=401, detail="Authentication required")

@app.get("/obligations")
def obligations(target_date: date):
    raise HTTPException(status_code=401, detail="Authentication required")

@app.patch("/obligations/{obligation_id}")
def update_obligation(obligation_id: str, patch: ObligationPatch):
    raise HTTPException(status_code=401, detail="Authentication required")

@app.get("/summaries/today")
def today_summary():
    raise HTTPException(status_code=401, detail="Authentication required")

@app.get("/auth/google/start")
def google_start():
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    from urllib.parse import urlencode
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent",
    })
    return {"authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}
