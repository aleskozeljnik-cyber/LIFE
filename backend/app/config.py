from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    anthropic_api_key: str = ""
    token_encryption_key: str
    session_secret: str
    frontend_url: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
