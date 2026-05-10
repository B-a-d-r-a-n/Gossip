from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from core.permissions.dependencies import get_current_user, require_channel_role, require_channel_member, get_user_channel_role
from core.db import get_db
from repositories.channel_repository import ChannelRepository
from core.exceptions import AppException
from models.channel import ChannelMember, ChannelInvite
from models.message import Message
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.channel import Channel
from ws_manager.manager import manager
router = APIRouter(prefix="/channels", tags=["channels"])


class ChannelCreate(BaseModel):
    name: str
    description: str | None = None


class ChannelInviteCreate(BaseModel):
    expires_in_minutes: int = 5

class InviteResponse(BaseModel):
    token: str
    expires_at: datetime


class MessageResponse(BaseModel):
    message: str


class ChannelMemberItem(BaseModel):
    user_id: str
    username: str
    role: str
class ChannelResponse(BaseModel):
    id: str
    name: str
    description: str | None = None


class ChannelListItem(BaseModel):
    id: str
    name: str


class UserRoleResponse(BaseModel):
    role: str


class JoinResponse(BaseModel):
    message: str
    channel_id: str


@router.get("/me", response_model=list[ChannelListItem])
async def list_my_channels(
    current_user: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChannelMember).where(ChannelMember.user_id == current_user).options(selectinload(ChannelMember.channel))
    memberships = (await db.execute(stmt)).scalars().all()
    return [
        {"id": str(m.channel_id), "name": m.channel.name}
        for m in memberships
        if m.channel
    ]


@router.get("/{channel_id}/me", response_model=UserRoleResponse)
async def get_my_channel_role(
    channel_id: UUID,
    current_user: UUID = Depends(require_channel_member),
    db: AsyncSession = Depends(get_db),
):
    role = await get_user_channel_role(channel_id, current_user, db)
    return {"role": role}


@router.get("/{channel_id}/members", response_model=list[ChannelMemberItem])
async def list_channel_members(
    channel_id: UUID,
    current_user: UUID = Depends(require_channel_member),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    members = await repo.get_channel_members(channel_id)
    return [
        {"user_id": str(m.user_id), "username": m.user.username, "role": m.role}
        for m in members
    ]


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    current_user: UUID = Depends(require_channel_member),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    channel = await repo.get_channel(channel_id)
    if not channel:
        raise AppException("NOT_FOUND", "Channel not found", 404)
    return {"id": str(channel.id), "name": channel.name, "description": channel.description}


@router.delete("/{channel_id}", response_model=MessageResponse)
async def delete_channel(
    channel_id: UUID,
    current_user: UUID = Depends(require_channel_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    channel = await repo.get_channel(channel_id)
    if not channel:
        raise AppException("NOT_FOUND", "Channel not found", 404)

    await repo.delete_channel(channel_id)
    await db.commit()
    return {"message": "Channel deleted"}




@router.post("", response_model=ChannelListItem)
async def create_channel(
    data: ChannelCreate,
    current_user: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    channel = await repo.create_channel(data.name, data.description)
    await repo.add_member(channel.id, current_user, role="admin")
    await db.commit()
    
    await manager.broadcast_to_channel(
        str(channel.id),
        {
            "type": "channel_created",
            "id": str(channel.id),
            "name": channel.name,
        }
    )
    
    return {"id": str(channel.id), "name": channel.name}


@router.get("", response_model=list[ChannelListItem])
async def list_channels(db: AsyncSession = Depends(get_db)):
    stmt = select(Channel)
    channels = (await db.execute(stmt)).scalars().all()
    return [{"id": str(c.id), "name": c.name} for c in channels]


@router.post("/{channel_id}/invite", response_model=InviteResponse)
async def create_invite(
    channel_id: UUID,
    data: ChannelInviteCreate,
    current_user: UUID = Depends(require_channel_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    token = str(uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=data.expires_in_minutes)
    invite = await repo.create_invite(channel_id, token, current_user, expires_at)
    await db.commit()
    return {"token": invite.token, "expires_at": invite.expires_at}


@router.post("/join/{token}", response_model=JoinResponse)
async def join_channel(
    token: str,
    current_user: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    invite = await repo.get_invite_by_token(token)
    if not invite or invite.used or invite.expires_at < datetime.utcnow():
        raise AppException("INVALID_INVITE", "Invalid or expired invite", 400)

    existing = await repo.get_member(invite.channel_id, current_user)
    if existing:
        raise AppException("ALREADY_MEMBER", "You are already a member of this channel", 400, {"channel_id": str(invite.channel_id)})

    invite.used = True
    member = await repo.add_member(invite.channel_id, current_user)
    await db.commit()
    
    await manager.broadcast_to_channel(
        str(invite.channel_id),
        {
            "type": "member_joined",
            "user_id": str(current_user),
            "role": member.role,
        }
    )
    
    return {"message": "Joined channel", "channel_id": str(invite.channel_id)}


@router.post("/{channel_id}/members/{user_id}/kick", response_model=MessageResponse)
async def kick_member(
    channel_id: UUID,
    user_id: UUID,
    current_user: UUID = Depends(require_channel_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    member = await repo.get_member(channel_id, user_id)
    if not member:
        raise AppException("NOT_FOUND", "Member not found", 404)

    stmt = (await db.execute(
        select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user_id,
        )
    )).scalar_one_or_none()

    if stmt:
        await db.delete(stmt)
        await db.commit()

    await manager.disconnect_user(str(channel_id), str(user_id))

    await manager.broadcast_to_channel(
        str(channel_id),
        {
            "type": "member_kicked",
            "user_id": str(user_id),
        }
    )

    return {"message": "Member kicked"}


@router.post("/{channel_id}/members/{user_id}/promote", response_model=MessageResponse)
async def promote_member(
    channel_id: UUID,
    user_id: UUID,
    current_user: UUID = Depends(require_channel_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    repo = ChannelRepository(db)
    member = await repo.get_member(channel_id, user_id)
    if not member:
        raise AppException("NOT_FOUND", "Member not found", 404)

    member.role = "admin"
    await db.commit()

    await manager.broadcast_to_channel(
        str(channel_id),
        {
            "type": "member_promoted",
            "user_id": str(user_id),
            "role": "admin",
        }
    )

    return {"message": "Member promoted"}


@router.post("/{channel_id}/leave", response_model=MessageResponse)
async def leave_channel(
    channel_id: UUID,
    current_user: UUID = Depends(require_channel_member),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChannelMember).where(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user,
    )
    member = (await db.execute(stmt)).scalar_one_or_none()
    if not member:
        raise AppException("NOT_FOUND", "Member not found", 404)

    was_admin = member.role == "admin"
    await db.delete(member)
    await db.flush()

    check_stmt = select(ChannelMember).where(ChannelMember.channel_id == channel_id).order_by(ChannelMember.created_at)
    remaining = (await db.execute(check_stmt)).scalars().all()

    if not remaining:
        message_stmt = select(Message).where(Message.channel_id == channel_id)
        messages = (await db.execute(message_stmt)).scalars().all()
        for msg in messages:
            await db.delete(msg)

        invite_stmt = select(ChannelInvite).where(ChannelInvite.channel_id == channel_id)
        invites = (await db.execute(invite_stmt)).scalars().all()
        for invite in invites:
            await db.delete(invite)

        channel_stmt = select(Channel).where(Channel.id == channel_id)
        channel = (await db.execute(channel_stmt)).scalar_one_or_none()
        if channel:
            await db.delete(channel)
    elif was_admin and remaining:
        oldest_member = remaining[0]
        oldest_member.role = "admin"

    await db.commit()
    await manager.disconnect_user(str(channel_id), str(current_user))
    
    if remaining:
        await manager.broadcast_to_channel(
            str(channel_id),
            {
                "type": "member_left",
                "user_id": str(current_user),
            }
        )

    return {"message": "Left channel"}
