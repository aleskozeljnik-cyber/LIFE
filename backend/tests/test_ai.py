from app.ai import configured_model, configured_provider


def test_default_ai_provider_is_gemini():
    assert configured_provider() == "gemini"
    assert configured_model() == "gemini-3.1-flash-lite"

def test_ai_provider_can_switch_to_claude(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "ai_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_model", "claude-sonnet-4-5")
    assert configured_provider() == "anthropic"
    assert configured_model() == "claude-sonnet-4-5"
