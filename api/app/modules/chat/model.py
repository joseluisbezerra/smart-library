from datetime import datetime
from enum import Enum
from uuid import (
    UUID,
    uuid4
)

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[ChatMessageRole] = mapped_column(
        SQLEnum(
            ChatMessageRole,
            name="chat_message_role",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    chat: Mapped[Chat] = relationship(back_populates="messages")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
