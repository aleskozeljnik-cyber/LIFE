from app.ai import configured_model, configured_provider


def test_default_ai_provider_is_gemini():
    assert configured_provider() == "gemini"
    assert configured_model() == "gemini-3.1-flash-lite"
