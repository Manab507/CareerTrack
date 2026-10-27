"""
CareerTrack — Security Utilities
Password hashing + JWT tokens
"""
import bcrypt
import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from .config import settings


# ==========================================
# Password Hashing
# ==========================================

def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ==========================================
# JWT Tokens
# ==========================================

def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    """7 days refresh token"""
    return create_access_token(user_id, expires_minutes=7 * 24 * 60)


def hash_token(token: str) -> str:
    """SHA-256 hash for DB storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        return None