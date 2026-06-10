import type { Book, BookPayload, BookType, Chat, ChatDetail } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    let message = `Erro ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: string };
      message = data.detail ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function listBooks(filters: { title?: string; author?: string } = {}) {
  const params = new URLSearchParams();

  if (filters.title) params.set("title", filters.title);
  if (filters.author) params.set("author", filters.author);

  const query = params.toString();

  return request<Book[]>(`/books${query ? `?${query}` : ""}`);
}

export function createBook(payload: BookPayload & { type: BookType; file: File }) {
  const form = new FormData();

  form.append("title", payload.title);
  form.append("author", payload.author);
  form.append("summary", payload.summary);
  form.append("publication_date", payload.publication_date);
  form.append("type", payload.type);
  form.append("file", payload.file);

  return request<Book>("/books", { method: "POST", body: form });
}

export function updateBook(id: string, payload: BookPayload) {
  return request<Book>(`/books/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteBook(id: string) {
  return request<void>(`/books/${id}`, { method: "DELETE" });
}

export function retryBookProcessing(id: string) {
  return request<Book>(`/books/${id}/retry-processing`, { method: "POST" });
}

export function booksProcessingProgressUrl() {
  return `${API_URL}/books/processing-progress/stream?interval=1`;
}

export function listChats(title?: string) {
  const query = title ? `?${new URLSearchParams({ title })}` : "";

  return request<Chat[]>(`/chats${query}`);
}

export function getChat(id: string) {
  return request<ChatDetail>(`/chats/${id}`);
}

export function updateChatTitle(id: string, title: string) {
  return request<Chat>(`/chats/${id}`, { method: "PUT", body: JSON.stringify({ title }) });
}

export function deleteChat(id: string) {
  return request<void>(`/chats/${id}`, { method: "DELETE" });
}

export function conversationUrl() {
  return `${API_URL}/chats/conversation`;
}
