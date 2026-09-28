from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # AI is provider-switchable. T1a uses Gemini for temporary/dev use;
    # Claude remains the production target and can be enabled by env only.
    ai_provider: str = "gemini"
    ai_timeout_seconds: int = 20
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    token_encryption_key: str
    session_secret: str
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
