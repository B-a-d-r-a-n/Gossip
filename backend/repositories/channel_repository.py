from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from models.channel import Channel, ChannelMember, ChannelInvite


class ChannelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_channel(self, name: str, description: str | None = None) -> Channel:
        channel = Channel(name=name, description=description)
        self.db.add(channel)
        await self.db.flush()
        return channel

    async def get_channel(self, channel_id: UUID) -> Channel | None:
        return await self.db.get(Channel, channel_id)

    async def add_member(self, channel_id: UUID, user_id: UUID, role: str = "member") -> ChannelMember:
        member = ChannelMember(channel_id=channel_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.flush()
        return member

    async def get_member(self, channel_id: UUID, user_id: UUID) -> ChannelMember | None:
        stmt = select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user_id,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create_invite(self, channel_id: UUID, token: str, created_by_id: UUID, expires_at) -> ChannelInvite:
        invite = ChannelInvite(
            channel_id=channel_id,
            token=token,
            created_by_id=created_by_id,
            expires_at=expires_at,
        )
        self.db.add(invite)
        await self.db.flush()
        return invite

    async def get_invite_by_token(self, token: str) -> ChannelInvite | None:
        stmt = select(ChannelInvite).where(ChannelInvite.token == token)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def delete_channel(self, channel_id: UUID) -> None:
        channel = await self.db.get(Channel, channel_id)
        if channel:
            await self.db.delete(channel)

    async def get_channel_members(self, channel_id: UUID) -> list[ChannelMember]:
        stmt = select(ChannelMember).where(ChannelMember.channel_id == channel_id).options(selectinload(ChannelMember.user))
        return list((await self.db.execute(stmt)).scalars().all())
