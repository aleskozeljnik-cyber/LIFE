from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # AI provider is explicitly switchable. Cloudflare Workers AI is the safe,
    # zero-training free-tier default for real-data testing.
    ai_provider: str = "cloudflare"
    ai_timeout_seconds: int = 20

    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    cloudflare_model: str = "@cf/zai-org/glm-4.7-flash"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    # Only set to true after independently verifying the project is on Gemini
    # Paid Tier. Unknown/unverified Gemini status must block real-data access.
    gemini_paid_tier_verified: bool = False

    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_data_usage_verified: bool = False

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    anthropic_data_usage_verified: bool = False

    token_encryption_key: str
    session_secret: str
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
