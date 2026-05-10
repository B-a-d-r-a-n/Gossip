from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text
from models.base import Base, UUIDMixin, TimestampMixin
from core.encryption.encrypted_type import EncryptedString


class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(EncryptedString)
    sentiment_label: Mapped[str | None] = mapped_column()
    sentiment_score: Mapped[float | None] = mapped_column()
    sentiment_status: Mapped[str] = mapped_column(default="pending")

    user: Mapped["User"] = relationship("User", back_populates="messages")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="messages")
