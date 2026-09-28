import asyncio

import pytest
from fastapi import HTTPException

from app import main


def test_calendar_upcoming_preserves_privacy_gate_status(monkeypatch):
    async def blocked(_user_id: str):
        raise HTTPException(
            status_code=503,
            detail="Real-data processing blocked: AI data policy is unknown.",
        )

    async def fail_if_calendar_called(*args, **kwargs):
        raise AssertionError("Calendar provider must not be called when privacy gate blocks access")

    monkeypatch.setattr(main, "get_google_access_token", blocked)
    monkeypatch.setattr(main, "list_upcoming_events", fail_if_calendar_called)
    monkeypatch.setattr(main, "current_user", lambda _session: "user-1")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.calendar_upcoming(days=14, life_session="session"))

    assert exc.value.status_code == 503
    assert "privacy" in exc.value.detail.lower()


def test_calendar_upcoming_maps_safe_event_fields(monkeypatch):
    async def access_token(_user_id: str):
        return "token"

    async def calendar_events(_token: str, days: int):
        assert days == 14
        return [
            {
                "id": "event-1",
                "summary": "Board meeting",
                "description": "private description",
                "location": "Ljubljana",
                "start": {"dateTime": "2026-09-28T15:00:00+02:00"},
                "end": {"dateTime": "2026-09-28T16:00:00+02:00"},
                "unexpected_sensitive_field": "must not leak",
            },
            {"summary": "missing id"},
        ]

    monkeypatch.setattr(main, "get_google_access_token", access_token)
    monkeypatch.setattr(main, "list_upcoming_events", calendar_events)
    monkeypatch.setattr(main, "current_user", lambda _session: "user-1")

    result = asyncio.run(main.calendar_upcoming(days=14, life_session="session"))

    assert result == [
        {
            "id": "event-1",
            "summary": "Board meeting",
            "description": "private description",
            "location": "Ljubljana",
            "start": {"dateTime": "2026-09-28T15:00:00+02:00"},
            "end": {"dateTime": "2026-09-28T16:00:00+02:00"},
        }
    ]
