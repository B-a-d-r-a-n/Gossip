from fastapi import Depends, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from core.exceptions import AppException
from core.auth.jwt_handler import decode_token
from core.db import get_db
from models.channel import ChannelMember
from fastapi import Request
from redis.asyncio import Redis
import httpx


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_redis_from_websocket(websocket: WebSocket) -> Redis:
    return websocket.app.state.redis

def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

async def get_current_user(request: Request) -> UUID:
    token = request.cookies.get("access_token")

    if not token:
        raise AppException("UNAUTHORIZED", "Missing token", 401)

    try:
        payload = decode_token(token)
        # Ensure this is an access token
        if payload.get("type") != "access":
            raise Exception("Not an access token")
        return UUID(payload["sub"])
    except Exception:
        raise AppException("UNAUTHORIZED", "Invalid token", 401)


def require_channel_role(required_roles: list[str]):
    async def dependency(
        channel_id: UUID,
        current_user: UUID = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        stmt = select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user,
        )
        member = (await db.execute(stmt)).scalar_one_or_none()
        if not member or member.role not in required_roles:
            raise AppException("FORBIDDEN", "Insufficient channel permissions.", 403)
        return current_user
    return dependency


async def require_channel_member(
    channel_id: UUID,
    current_user: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user,
    )
    member = (await db.execute(stmt)).scalar_one_or_none()
    if not member:
        raise AppException("FORBIDDEN", "You are not a member of this channel.", 403)
    return current_user


async def get_user_channel_role(
    channel_id: UUID,
    current_user: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user,
    )
    member = (await db.execute(stmt)).scalar_one_or_none()
    if not member:
        raise AppException("FORBIDDEN", "You are not a member of this channel.", 403)
    return member.role
