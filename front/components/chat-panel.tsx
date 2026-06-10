"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { conversationUrl, deleteChat, getChat, listChats, updateChatTitle } from "@/lib/api";
import { ConfirmDialog } from "@/components/confirm-dialog";
import type { Chat, ChatMessage } from "@/lib/types";

type StreamEvent = {
  event: string;
  data: Record<string, string>;
};

export function ChatPanel() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [chatToDelete, setChatToDelete] = useState<Chat | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isPending, startTransition] = useTransition();
  const bottomRef = useRef<HTMLDivElement>(null);

  function loadChats() {
    startTransition(async () => {
      try {
        setChats(await listChats());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Não foi possível listar conversas.");
      }
    });
  }

  useEffect(() => {
    loadChats();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function openChat(chatId: string) {
    try {
      setError(null);
      const chat = await getChat(chatId);
      setActiveChatId(chat.id);
      setMessages(chat.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível abrir a conversa.");
    }
  }

  function startEditing(chat: Chat) {
    setEditingChatId(chat.id);
    setEditingTitle(chat.title);
  }

  async function saveChatTitle(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingChatId || !editingTitle.trim()) return;

    try {
      await updateChatTitle(editingChatId, editingTitle.trim());
      setEditingChatId(null);
      setEditingTitle("");
      loadChats();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível editar o título.");
    }
  }

  async function confirmRemoveChat() {
    if (!chatToDelete) return;

    try {
      await deleteChat(chatToDelete.id);
      if (activeChatId === chatToDelete.id) {
        setActiveChatId(null);
        setMessages([]);
      }
      setChatToDelete(null);
      loadChats();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível excluir a conversa.");
    }
  }

  async function submitMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = input.trim();
    if (!content || isStreaming) return;

    setInput("");
    setError(null);
    setIsStreaming(true);

    const optimisticUser: ChatMessage = {
      id: crypto.randomUUID(),
      chat_id: activeChatId ?? "draft",
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    const optimisticAssistant: ChatMessage = {
      id: crypto.randomUUID(),
      chat_id: activeChatId ?? "draft",
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };

    setMessages((current) => [...current, optimisticUser, optimisticAssistant]);

    try {
      const response = await fetch(conversationUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: content, chat_id: activeChatId }),
      });

      if (!response.ok || !response.body) {
        throw new Error(response.statusText || "Não foi possível iniciar a conversa.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const parsed = parseSse(part);
          if (!parsed) continue;
          handleStreamEvent(parsed, optimisticAssistant.id);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível enviar a mensagem.");
    } finally {
      setIsStreaming(false);
    }
  }

  function handleStreamEvent(parsed: StreamEvent, assistantId: string) {
    if (parsed.event === "token") {
      const token = parsed.data.content ?? "";
      setMessages((current) => current.map((message) => (message.id === assistantId ? { ...message, content: message.content + token } : message)));
      return;
    }

    if (parsed.event === "chat" || parsed.event === "done") {
      const nextChatId = parsed.data.chat_id;
      if (nextChatId) setActiveChatId(nextChatId);
      loadChats();
      return;
    }

    if (parsed.event === "error") {
      setError(parsed.data.message ?? "Não foi possível processar a conversa.");
    }
  }

  return (
    <div className="grid min-h-[calc(100vh-15rem)] gap-5 xl:grid-cols-[20rem_1fr]">
      <aside className="rounded-[1.5rem] bg-white p-4 shadow-sm shadow-stone-900/5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-black tracking-[-0.03em] text-stone-950">Conversas</h2>
          <button onClick={() => { setActiveChatId(null); setMessages([]); }} className="btn btn-primary px-3 py-2 text-xs">Nova</button>
        </div>
        <div className="mt-4 grid gap-2">
          {chats.map((chat) => (
            <div key={chat.id} className={`rounded-2xl border p-2 transition ${activeChatId === chat.id ? "border-stone-950 bg-stone-100 shadow-sm" : "border-stone-200 bg-white hover:border-stone-300"}`}>
              {editingChatId === chat.id ? (
                <form onSubmit={saveChatTitle} className="grid gap-2">
                  <input value={editingTitle} onChange={(event) => setEditingTitle(event.target.value)} className="input bg-white text-sm" autoFocus />
                  <div className="flex gap-2">
                    <button className="btn btn-success flex-1 px-3 py-2 text-xs">Salvar</button>
                    <button type="button" onClick={() => setEditingChatId(null)} className="btn btn-secondary flex-1 px-3 py-2 text-xs">Cancelar</button>
                  </div>
                </form>
              ) : (
                <>
                  <button onClick={() => openChat(chat.id)} className="w-full rounded-xl px-3 py-2 text-left text-sm font-bold text-stone-800 hover:bg-stone-50">
                    <span className="line-clamp-2">{chat.title}</span>
                    <span className="mt-1 block text-xs font-medium text-stone-500">{new Date(chat.updated_at).toLocaleString("pt-BR")}</span>
                  </button>
                  <div className="mt-1 flex gap-2">
                    <button onClick={() => startEditing(chat)} className="btn btn-secondary flex-1 px-3 py-2 text-xs">Editar</button>
                    <button onClick={() => setChatToDelete(chat)} className="btn flex-1 bg-rose-50 px-3 py-2 text-xs text-rose-700 hover:bg-rose-100">Excluir</button>
                  </div>
                </>
              )}
            </div>
          ))}
          {!chats.length && <p className="rounded-2xl border border-dashed border-stone-300 p-5 text-sm text-stone-500">Nenhuma conversa ainda.</p>}
        </div>
      </aside>

      <section className="flex min-w-0 flex-col rounded-[1.5rem] bg-white shadow-sm shadow-stone-900/5">
        <div className="border-b border-stone-100 p-5">
          <h2 className="text-xl font-black tracking-[-0.03em] text-stone-950">{activeChatId ? "Conversa ativa" : "Nova conversa"}</h2>
          <p className="mt-1 text-sm text-stone-500">Pergunte em português sobre os livros processados.</p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-3xl px-5 py-4 leading-7 ${message.role === "user" ? "bg-stone-950 text-white" : "bg-stone-100 text-stone-800"}`}>
                {message.role === "assistant" ? (
                  message.content ? (
                    <div className="markdown">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                    </div>
                  ) : isStreaming ? (
                    "Pensando..."
                  ) : null
                ) : (
                  message.content
                )}
              </div>
            </div>
          ))}
          {!messages.length && (
            <div className="rounded-[1.5rem] border border-dashed border-stone-300 p-8 text-center text-stone-500">
              Comece uma conversa para consultar sua biblioteca.
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && <p className="mx-5 mb-3 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-800">{error}</p>}

        <form onSubmit={submitMessage} className="border-t border-stone-100 p-4">
          <div className="flex flex-col gap-3 sm:flex-row">
            <textarea
              rows={2}
              value={input}
              disabled={isStreaming || isPending}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Digite sua pergunta..."
              className="min-h-14 flex-1 resize-none rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-stone-950 focus:bg-white"
            />
            <button disabled={isStreaming || !input.trim()} className="btn btn-success px-6">
              {isStreaming ? "Enviando" : "Enviar"}
            </button>
          </div>
        </form>
      </section>

      <ConfirmDialog
        open={Boolean(chatToDelete)}
        title="Excluir conversa?"
        description={`A conversa${chatToDelete ? ` "${chatToDelete.title}"` : ""} será removida do histórico. Essa ação não pode ser desfeita.`}
        confirmLabel="Excluir conversa"
        onConfirm={confirmRemoveChat}
        onCancel={() => setChatToDelete(null)}
      />
    </div>
  );
}

function parseSse(chunk: string): StreamEvent | null {
  const event = chunk.split("\n").find((line) => line.startsWith("event: "))?.slice(7);
  const dataLine = chunk.split("\n").find((line) => line.startsWith("data: "))?.slice(6);
  if (!event || !dataLine) return null;

  try {
    return { event, data: JSON.parse(dataLine) as Record<string, string> };
  } catch {
    return null;
  }
}
