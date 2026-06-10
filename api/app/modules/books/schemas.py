from datetime import (
    date,
    datetime
)
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)

from app.modules.books.model import BookType, ProcessingStatus


class BookCreate(BaseModel):
    title: str = Field(description="Book title.")
    author: str = Field(description="Book author name.")
    summary: str = Field(description="Brief book summary.")
    publication_date: date = Field(description="Book publication date.")
    type: BookType = Field(description="Book type: common or technical.")


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, description="Updated book title.")
    author: str | None = Field(default=None, description="Updated book author name.")
    summary: str | None = Field(default=None, description="Updated book summary.")
    publication_date: date | None = Field(
        default=None,
        description="Updated book publication date.",
    )


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Book unique identifier.")
    title: str = Field(description="Book title.")
    author: str = Field(description="Book author name.")
    summary: str = Field(description="Brief book summary.")
    publication_date: date = Field(description="Book publication date.")
    file_extension: str = Field(description="Stored book file extension.")
    type: BookType = Field(description="Book type: common or technical.")
    processing_attempts: int = Field(description="Manual processing retry attempts.")
    processing_status: ProcessingStatus = Field(description="Current processing status.")
    created_at: datetime = Field(description="Book creation timestamp.")
    updated_at: datetime = Field(description="Last book update timestamp.")
