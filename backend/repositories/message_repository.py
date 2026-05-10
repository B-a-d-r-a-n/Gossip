from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, tuple_
from sqlalchemy.orm import selectinload
from uuid import UUID
from models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_messages_cursor(
        self,
        channel_id: UUID,
        cursor: UUID | None,
        limit: int = 30,
    ) -> tuple[list[Message], UUID | None]:
        stmt = (
            select(Message)
            .options(selectinload(Message.user))
            .where(Message.channel_id == channel_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit + 1)
        )

        if cursor:
            cursor_msg = await self.db.get(Message, cursor)
            if cursor_msg:
                # Correct approach for SQLAlchemy
                stmt = stmt.where(
                    tuple_(Message.created_at, Message.id) < (cursor_msg.created_at, cursor_msg.id)
                )

        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        next_cursor: UUID | None = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = rows[-1].id

        return rows, next_cursor
