from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.chat.model import ChatMessageRole


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Chat unique identifier.")
    title: str = Field(description="Chat title.")
    created_at: datetime = Field(description="Chat creation timestamp.")
    updated_at: datetime = Field(description="Last chat update timestamp.")


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Message unique identifier.")
    chat_id: UUID = Field(description="Chat unique identifier.")
    role: ChatMessageRole = Field(description="Message role: user or assistant.")
    content: str = Field(description="Message content.")
    created_at: datetime = Field(description="Message creation timestamp.")


class ChatDetailRead(ChatRead):
    messages: list[ChatMessageRead] = Field(description="Chat messages ordered by creation.")


class ChatUpdate(BaseModel):
    title: str = Field(description="Updated chat title.")


class ChatConversationCreate(BaseModel):
    input: str = Field(min_length=1, description="User input.")
    chat_id: UUID | None = Field(default=None, description="Existing chat UUID.")
