from fastapi import APIRouter, Depends, WebSocket, Query
from fastapi.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from uuid import UUID, uuid4
from redis.asyncio import Redis
from core.permissions.dependencies import get_current_user, get_redis, get_redis_from_websocket, require_channel_member
from core.db import get_db
from repositories.message_repository import MessageRepository
from ws_manager.manager import manager
from models.message import Message
from models.channel import ChannelMember
from models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class MessageCreate(BaseModel):
    content: str


class WsTicketResponse(BaseModel):
    ticket: str


class MessageItem(BaseModel):
    id: str
    user_id: str
    username: str | None = None
    role: str | None = None
    content: str
    sentiment_label: str | None = None
    sentiment_score: float | None = None
    sentiment_status: str | None = None
    created_at: str


class MessagesResponse(BaseModel):
    messages: list[MessageItem]
    next_cursor: str | None = None


@router.post("/ws/ticket", response_model=WsTicketResponse)
async def get_ws_ticket(
    current_user: UUID = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    ticket = str(uuid4())
    await redis.set(f"ws:ticket:{ticket}", str(current_user), ex=30)
    return {"ticket": ticket}


@router.websocket("/ws/chat/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: UUID,
    ticket: str = Query(...),
    redis: Redis = Depends(get_redis_from_websocket),
    db: AsyncSession = Depends(get_db),
):
    user_id = await redis.get(f"ws:ticket:{ticket}")
    if user_id:
        await redis.delete(f"ws:ticket:{ticket}")
    if not user_id:
        await websocket.close(code=4001)
        return

    # Fetch user + member once at connection time, not per-message
    member = (await db.execute(
        select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == UUID(user_id),
        )
    )).scalar_one_or_none()

    if not member:
        await websocket.close(code=4003)
        return

    user = (await db.execute(
        select(User).where(User.id == UUID(user_id))
    )).scalar_one_or_none()

    # Cache these for the lifetime of the connection — they don't change
    username: str = user.username if user else "Unknown"
    role: str = member.role if member else "member"

    await manager.connect(websocket, str(channel_id), user_id)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "")

            # Pre-generate the ID so we can broadcast immediately,
            # before the DB round-trip completes.
            msg_id = uuid4()

            msg = Message(
                id=msg_id,
                channel_id=channel_id,
                user_id=UUID(user_id),
                content=content,
            )
            db.add(msg)
            await db.commit()

            broadcast_payload = {
                "id": str(msg_id),
                "user_id": user_id,
                "username": username,
                "role": role,
                "content": content,
                "sentiment_label": None,
                "sentiment_score": None,
                "sentiment_status": "pending",
                "created_at": msg.created_at.isoformat(),
            }
            asyncio.create_task(
                manager.broadcast_to_channel(str(channel_id), broadcast_payload)
            )

            await websocket.app.state.kafka_producer.enqueue_analysis(
                str(msg.id), content, str(channel_id)
            )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, str(channel_id), user_id)


@router.get("/{channel_id}/messages", response_model=MessagesResponse)
async def get_messages(
    channel_id: UUID,
    cursor: UUID | None = None,
    limit: int = 30,
    current_user: UUID = Depends(require_channel_member),
    db: AsyncSession = Depends(get_db),
):
    repo = MessageRepository(db)
    messages, next_cursor = await repo.get_messages_cursor(channel_id, cursor, limit)

    # Batch-load all member roles in one query instead of N queries
    user_ids = [m.user_id for m in messages]
    members_result = await db.execute(
        select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id.in_(user_ids),
        )
    )
    role_by_user = {
        str(cm.user_id): cm.role
        for cm in members_result.scalars().all()
    }

    message_list = [
        {
            "id": str(m.id),
            "user_id": str(m.user_id),
            "username": m.user.username if m.user else "Unknown",
            "role": role_by_user.get(str(m.user_id), "member"),
            "content": m.content,
            "sentiment_label": m.sentiment_label,
            "sentiment_score": m.sentiment_score,
            "sentiment_status": m.sentiment_status,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]

    return {
        "messages": message_list,
        "next_cursor": str(next_cursor) if next_cursor else None,
    }