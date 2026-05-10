from redis.asyncio import Redis
from jwt import decode as jwt_decode
from core.config import settings


async def revoke_token(redis: Redis, jti: str, ttl: int):
    await redis.set(f"revoked:{jti}", "1", ex=ttl)


async def is_token_revoked(redis: Redis, jti: str) -> bool:
    return await redis.exists(f"revoked:{jti}") == 1


async def get_current_user_id_from_token(token: str, redis: Redis) -> str | None:
    try:
        payload = jwt_decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        jti = payload.get("jti")
        if jti and await is_token_revoked(redis, jti):
            return None
        return payload.get("sub")
    except Exception:
        return None
