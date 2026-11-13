"""Small, explicit local authentication layer for the academic prototype."""
import hashlib
import secrets
from typing import Optional

ITERATIONS = 210_000
ACTIVE_TOKENS: dict[str, int] = {}

def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"{salt}${digest}"

def verify_password(password: str, stored: str) -> bool:
    salt, expected = stored.split("$", 1)
    actual = hash_password(password, salt).split("$", 1)[1]
    return secrets.compare_digest(actual, expected)

def create_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    ACTIVE_TOKENS[token] = user_id
    return token

def get_user_id(token: str) -> Optional[int]:
    return ACTIVE_TOKENS.get(token)

def revoke_token(token: str) -> None:
    ACTIVE_TOKENS.pop(token, None)

