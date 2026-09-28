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


def test_cloudflare_is_marked_no_training():
    from app.ai import ai_data_usage_status
    from app.config import settings
    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(settings, "ai_provider", "cloudflare")
        assert ai_data_usage_status() == "not_used_for_training"
    finally:
        monkeypatch.undo()


def test_gemini_is_blocked_without_paid_tier_verification():
    from app.ai import ai_data_usage_status, real_data_processing_allowed
    from app.config import settings
    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(settings, "ai_provider", "gemini")
        monkeypatch.setattr(settings, "gemini_paid_tier_verified", False)
        monkeypatch.setattr(settings, "gemini_api_key", "test-key")
        assert ai_data_usage_status() == "used_for_training"
        assert real_data_processing_allowed() is False
    finally:
        monkeypatch.undo()
