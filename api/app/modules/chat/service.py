from collections.abc import Iterator
from uuid import UUID

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    SystemMessage
)

from sqlalchemy import (
    func,
    select
)

from sqlalchemy.orm import (
    Session,
    selectinload
)

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.utils import format_sse
from app.modules.chat.model import Chat

from app.modules.chat.schemas import (
    ChatConversationCreate,
    ChatUpdate
)

from app.modules.chat.utils import (
    append_chat_messages,
    create_chat_with_messages,
    history_messages,
    semantic_book_context,
)


def list_chats(db: Session, title: str | None = None) -> list[Chat]:
    statement = select(Chat).order_by(Chat.created_at.desc())

    if title:
        statement = statement.where(
            func.unaccent(Chat.title).ilike(func.unaccent(f"%{title}%"))
        )

    return list(db.scalars(statement).all())


def get_chat(db: Session, chat_id: UUID) -> Chat | None:
    statement = (
        select(Chat)
        .options(selectinload(Chat.messages))
        .where(Chat.id == chat_id)
    )

    return db.scalar(statement)


def update_chat(db: Session, chat: Chat, payload: ChatUpdate) -> Chat:
    chat.title = payload.title
    db.commit()
    db.refresh(chat)

    return chat


def delete_chat(db: Session, chat: Chat) -> None:
    db.delete(chat)
    db.commit()


def stream_conversation(payload: ChatConversationCreate) -> Iterator[str]:
    chat_id = payload.chat_id
    title: str | None = None
    history: list[object] = []

    if chat_id is not None:
        with SessionLocal() as db:
            chat = get_chat(db, payload.chat_id)

            if chat is None:
                yield format_sse("error", {"message": "Não foi possível processar a conversa."})

                return

            chat_id = chat.id
            title = chat.title
            history = history_messages(chat)

    try:
        book_context = semantic_book_context(payload.input)

        llm = ChatOpenAI(
            model=get_settings().openai_chat_model,
            temperature=0.2,
            streaming=True
        )

        messages = [
            SystemMessage(
                content=(
                    "Você é um assistente de uma biblioteca inteligente. "
                    "Responda em português, usando o contexto dos livros quando ele for relevante. "
                    "Sempre que usar informações do contexto dos livros, inclua a fonte da informação "
                    "com título, autor e páginas. "
                    "Se o contexto não tiver informação suficiente, diga isso claramente.\n\n"
                    f"Contexto dos livros:\n{book_context}"
                )
            ),
            *history,
            HumanMessage(content=payload.input),
        ]

        response_parts: list[str] = []

        for chunk in llm.stream(messages):
            token = chunk.content or ""
            if not token:
                continue

            response_parts.append(str(token))

            yield format_sse("token", {"content": str(token)})

        assistant_response = "".join(response_parts)

        if chat_id is None:
            chat_id, title = create_chat_with_messages(payload.input, assistant_response)
        else:
            append_chat_messages(chat_id, payload.input, assistant_response)

        yield format_sse("chat", {"chat_id": str(chat_id), "title": title})

        yield format_sse("done", {"chat_id": str(chat_id)})
    except Exception:
        yield format_sse("error", {"message": "Não foi possível processar a conversa."})
