from datetime import (
    datetime,
    timezone
)

from types import SimpleNamespace
from uuid import uuid4

from unittest.mock import (
    ANY,
    Mock
)

from fastapi import status

from app.core.utils import format_sse
from app.modules.chat.controller import service


def make_chat() -> SimpleNamespace:
    now = datetime.now(timezone.utc)

    return SimpleNamespace(
        id=uuid4(),
        title="Chat sobre livros",
        created_at=now,
        updated_at=now,
    )


def test_list_chats_calls_service(client, monkeypatch):
    list_chats = Mock(return_value=[])
    monkeypatch.setattr(service, "list_chats", list_chats)

    response = client.get("/chats", params={"title": "livros"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
    list_chats.assert_called_once_with(ANY, title="livros")


def test_get_chat_returns_404_when_chat_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(service, "get_chat", Mock(return_value=None))

    response = client.get(f"/chats/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Chat not found"


def test_update_chat_returns_404_when_chat_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(service, "get_chat", Mock(return_value=None))

    response = client.put(f"/chats/{uuid4()}", json={"title": "Novo título"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Chat not found"


def test_delete_chat_returns_204_when_chat_exists(client, monkeypatch):
    chat = make_chat()
    delete_chat = Mock()
    monkeypatch.setattr(service, "get_chat", Mock(return_value=chat))
    monkeypatch.setattr(service, "delete_chat", delete_chat)

    response = client.delete(f"/chats/{chat.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    delete_chat.assert_called_once_with(ANY, chat)


def test_conversation_returns_event_stream(client, monkeypatch):
    monkeypatch.setattr(
        service,
        "stream_conversation",
        Mock(return_value=iter([format_sse("token", {"content": "Olá"})])),
    )

    response = client.post("/chats/conversation", json={"input": "Olá"})

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: token" in response.text
    assert 'data: {"content": "Ol\\u00e1"}' in response.text
