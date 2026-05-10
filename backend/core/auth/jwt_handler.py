import uuid
from datetime import datetime, timedelta
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from core.config import settings


def create_access_token(user_id: uuid.UUID) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRY_MINUTES)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expire,
        "type": "access",
    }
    return encode(payload, settings.JWT_SECRET, algorithm="HS256"), jti


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRY_DAYS)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expire,
        "type": "refresh",
    }
    return encode(payload, settings.JWT_SECRET, algorithm="HS256"), jti


def decode_token(token: str) -> dict:
    return decode(token, settings.JWT_SECRET, algorithms=["HS256"])
