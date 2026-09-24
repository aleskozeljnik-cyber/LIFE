import secrets
from itsdangerous import URLSafeTimedSerializer
from .config import settings

_serializer = URLSafeTimedSerializer(settings.session_secret)

def new_state() -> str:
    return secrets.token_urlsafe(32)

def sign_session(user_id: str) -> str:
    return _serializer.dumps({"user_id": user_id})

def read_session(value: str, max_age: int = 60 * 60 * 24 * 30) -> dict:
    return _serializer.loads(value, max_age=max_age)
