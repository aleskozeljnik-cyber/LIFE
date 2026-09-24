from cryptography.fernet import Fernet
from .config import settings

_cipher = Fernet(settings.token_encryption_key.encode())

def encrypt_token(value: str) -> str:
    return _cipher.encrypt(value.encode()).decode()

def decrypt_token(value: str) -> str:
    return _cipher.decrypt(value.encode()).decode()
