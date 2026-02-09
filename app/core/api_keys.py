import secrets
import hashlib

API_KEY_PREFIX = "rc"

def generate_api_key() -> str:
    return f"{API_KEY_PREFIX}_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()