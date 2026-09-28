from app.ai import configured_model, configured_provider


def test_default_ai_provider_is_cloudflare():
    assert configured_provider() == "cloudflare"
    assert configured_model() == "@cf/zai-org/glm-4.7-flash"

def test_ai_provider_can_switch_to_claude(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "ai_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_model", "claude-sonnet-4-5")
    assert configured_provider() == "anthropic"
    assert configured_model() == "claude-sonnet-4-5"


def test_cloudflare_is_marked_no_training(monkeypatch):
    from app.ai import ai_data_usage_status
    from app.config import settings
    monkeypatch.setattr(settings, "ai_provider", "cloudflare")
    monkeypatch.setattr(settings, "cloudflare_account_id", "test-account")
    monkeypatch.setattr(settings, "cloudflare_api_token", "test-token")
    assert ai_data_usage_status() == "not_used_for_training"


def test_gemini_is_blocked_without_paid_tier_verification(monkeypatch):
    from app.ai import ai_data_usage_status, real_data_processing_allowed
    from app.config import settings
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_paid_tier_verified", False)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    assert ai_data_usage_status() == "used_for_training"
    assert real_data_processing_allowed() is False

def test_sync_telemetry_allowlist_never_keeps_source_content():
    from app.telemetry import safe_sync_metadata
    result = {
        "gmail": {
            "messages_found": 10,
            "obligations_created": 2,
            "messages_skipped": 3,
            "prefilter_filtered": 5,
            "subject": "Private invoice",
            "sender": "person@example.com",
            "body": "PRIVATE BODY",
        }
    }
    safe = safe_sync_metadata(result)
    assert safe == {"gmail": {"messages_found": 10, "obligations_created": 2, "messages_skipped": 3, "prefilter_filtered": 5}}
    assert "Private invoice" not in repr(safe)
    assert "person@example.com" not in repr(safe)
    assert "PRIVATE BODY" not in repr(safe)


def test_real_google_sync_hard_gate_blocks_before_db_or_google(monkeypatch):
    import pytest
    from fastapi import HTTPException
    from app.config import settings
    from app.jobs import get_google_access_token

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_paid_tier_verified", False)
    async def fail_if_connection_attempted():
        raise AssertionError("DB/Google access must not be attempted while privacy gate is blocked")
    monkeypatch.setattr("app.jobs.get_connection", fail_if_connection_attempted)

    with pytest.raises(HTTPException) as exc:
        import asyncio
        asyncio.run(get_google_access_token("user-1"))
    assert exc.value.status_code == 503


def test_cloudflare_policy_is_unknown_when_not_configured(monkeypatch):
    from app.ai import ai_data_usage_status, real_data_processing_allowed
    from app.config import settings
    monkeypatch.setattr(settings, "ai_provider", "cloudflare")
    monkeypatch.setattr(settings, "cloudflare_account_id", "")
    monkeypatch.setattr(settings, "cloudflare_api_token", "")
    assert ai_data_usage_status() == "unknown"
    assert real_data_processing_allowed() is False
