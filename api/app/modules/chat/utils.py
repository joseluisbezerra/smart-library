from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from langchain_openai import (
    ChatOpenAI,
    OpenAIEmbeddings
)

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.modules.books.model import BookChunk
from app.modules.chat.model import (
    Chat,
    ChatMessage,
    ChatMessageRole
)

settings = get_settings()

CHAT_CONTEXT_LIMIT = 12
BOOK_CONTEXT_LIMIT = 5


def clean_title(title: str) -> str:
    title = title.strip().strip('"').strip("'")

    return title[:120] or "Novo chat"


def create_title(user_input: str) -> str:
    try:
        llm = ChatOpenAI(model=settings.openai_chat_model, temperature=0.2)
        response = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "Gere um título curto em português para uma conversa. "
                        "Responda somente com o título, sem aspas e sem pontuação extra."
                    )
                ),
                HumanMessage(content=user_input),
            ]
        )

        return clean_title(str(response.content))
    except Exception:
        return clean_title(user_input[:80])


def semantic_book_context(user_input: str) -> str:
    embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model)
    query_embedding = embeddings.embed_query(user_input)

    with SessionLocal() as db:
        chunks = list(
            db.scalars(
                select(BookChunk)
                .options(selectinload(BookChunk.book))
                .order_by(BookChunk.embedding.cosine_distance(query_embedding))
                .limit(BOOK_CONTEXT_LIMIT)
            ).all()
        )

    if not chunks:
        return "Nenhum trecho relevante de livros foi encontrado."

    return "\n\n".join(
        (
            f"Trecho {index + 1}\n"
            f"Fonte: {chunk.book.title}, de {chunk.book.author}, "
            f"páginas {chunk.page_start}-{chunk.page_end}\n"
            f"Conteúdo:\n{chunk.content}"
        )
        for index, chunk in enumerate(chunks)
    )


def history_messages(chat: Chat) -> list[object]:
    recent_messages = chat.messages[-CHAT_CONTEXT_LIMIT:]
    messages: list[object] = []

    for message in recent_messages:
        if message.role == ChatMessageRole.USER:
            messages.append(HumanMessage(content=message.content))
        elif message.role == ChatMessageRole.ASSISTANT:
            messages.append(AIMessage(content=message.content))

    return messages


def create_chat_with_messages(user_input: str, assistant_response: str) -> tuple[UUID, str]:
    title = create_title(user_input)

    with SessionLocal() as db:
        chat = Chat(title=title)
        db.add(chat)

        db.flush()

        db.add(
            ChatMessage(
                chat_id=chat.id,
                role=ChatMessageRole.USER,
                content=user_input
            )
        )

        db.add(
            ChatMessage(
                chat_id=chat.id,
                role=ChatMessageRole.ASSISTANT,
                content=assistant_response,
            )
        )

        db.commit()

        return chat.id, chat.title


def append_chat_messages(chat_id: UUID, user_input: str, assistant_response: str) -> None:
    with SessionLocal() as db:
        db.add(
            ChatMessage(
                chat_id=chat_id,
                role=ChatMessageRole.USER,
                content=user_input
            )
        )

        db.add(
            ChatMessage(
                chat_id=chat_id,
                role=ChatMessageRole.ASSISTANT,
                content=assistant_response,
            )
        )

        db.commit()
