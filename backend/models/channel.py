from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UniqueConstraint
from models.base import Base, UUIDMixin, TimestampMixin
from models.message import Message


class Channel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channels"

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))

    members: Mapped[list["ChannelMember"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", cascade="all, delete-orphan"
    )


class ChannelMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channel_members"

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("channels.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="member")

    channel: Mapped["Channel"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="channel_memberships")

    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_channel_user"),)


class ChannelInvite(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channel_invites"

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column()
    used: Mapped[bool] = mapped_column(default=False)

    channel: Mapped["Channel"] = relationship()
