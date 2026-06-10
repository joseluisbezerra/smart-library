from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status
)

from app.core.database import get_db
from app.modules.chat import service
from app.modules.chat.schemas import (
    ChatConversationCreate,
    ChatDetailRead,
    ChatRead,
    ChatUpdate,
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatRead], summary="List chats")
def list_chats(
    title: Annotated[
        str | None,
        Query(description="Optional partial title filter, case-insensitive and accent-insensitive."),
    ] = None,
    db: Session = Depends(get_db),
) -> list[ChatRead]:
    return service.list_chats(db, title=title)


@router.get("/{chat_id}", response_model=ChatDetailRead, summary="Get chat")
def get_chat(
    chat_id: Annotated[UUID, Path(description="Chat UUID.")],
    db: Session = Depends(get_db),
) -> ChatDetailRead:
    chat = service.get_chat(db, chat_id)

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    return chat


@router.put("/{chat_id}", response_model=ChatRead, summary="Update chat title")
def update_chat(
    chat_id: Annotated[UUID, Path(description="Chat UUID.")],
    payload: Annotated[ChatUpdate, Body(description="Chat title update.")],
    db: Session = Depends(get_db),
) -> ChatRead:
    chat = service.get_chat(db, chat_id)

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    return service.update_chat(db, chat, payload)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete chat")
def delete_chat(
    chat_id: Annotated[UUID, Path(description="Chat UUID.")],
    db: Session = Depends(get_db),
) -> Response:
    chat = service.get_chat(db, chat_id)

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    service.delete_chat(db, chat)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/conversation",
    summary="Chat with library context",
    description=(
        "Streams an assistant response using SSE. If chat_id is omitted, creates a new chat "
        "and generates its title with the LLM. The user input is embedded and used to retrieve "
        "relevant book chunks as context."
    ),
    response_class=StreamingResponse,
)
def conversation(
    payload: Annotated[ChatConversationCreate, Body(description="Conversation input.")],
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_conversation(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
