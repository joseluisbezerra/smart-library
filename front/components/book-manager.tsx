"use client";

import { useEffect, useState, useTransition } from "react";
import { booksProcessingProgressUrl, createBook, deleteBook, listBooks, retryBookProcessing, updateBook } from "@/lib/api";
import { ConfirmDialog } from "@/components/confirm-dialog";
import type { Book, BookPayload, BookProcessingProgress, BookType, ProcessingStatus } from "@/lib/types";

const emptyForm = {
  title: "",
  author: "",
  summary: "",
  publication_date: "",
};

const statusLabels: Record<ProcessingStatus, string> = {
  queued: "Na fila",
  processing: "Processando",
  processed: "Processado",
  "processing failed": "Falhou",
};

const statusClasses: Record<ProcessingStatus, string> = {
  queued: "bg-amber-100 text-amber-900 ring-amber-200",
  processing: "bg-indigo-100 text-indigo-900 ring-indigo-200",
  processed: "bg-emerald-100 text-emerald-900 ring-emerald-200",
  "processing failed": "bg-rose-100 text-rose-900 ring-rose-200",
};

const defaultProgress: Record<ProcessingStatus, number> = {
  queued: 8,
  processing: 35,
  processed: 100,
  "processing failed": 100,
};

export function BookManager() {
  const [books, setBooks] = useState<Book[]>([]);
  const [filters, setFilters] = useState({ title: "", author: "" });
  const [form, setForm] = useState<BookPayload>(emptyForm);
  const [type, setType] = useState<BookType>("common");
  const [file, setFile] = useState<File | null>(null);
  const [editing, setEditing] = useState<Book | null>(null);
  const [progressByBook, setProgressByBook] = useState<Record<string, BookProcessingProgress>>({});
  const [bookToDelete, setBookToDelete] = useState<Book | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function loadBooks(nextFilters = filters) {
    startTransition(async () => {
      try {
        setError(null);
        setBooks(await listBooks(nextFilters));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Não foi possível listar os livros.");
      }
    });
  }

  useEffect(() => {
    loadBooks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const source = new EventSource(booksProcessingProgressUrl());

    source.addEventListener("books_processing_progress", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as BookProcessingProgress[];
        setProgressByBook(Object.fromEntries(payload.map((item) => [item.book_id, item])));
        setBooks((current) =>
          current.map((book) => {
            const progress = payload.find((item) => item.book_id === book.id);
            return progress ? { ...book, processing_status: progress.status } : book;
          }),
        );
      } catch {
        setError("Não foi possível acompanhar o processamento em tempo real.");
      }
    });

    source.onerror = () => {
      source.close();
    };

    return () => source.close();
  }, []);

  function resetForm() {
    setForm(emptyForm);
    setType("common");
    setFile(null);
    setEditing(null);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);

    try {
      if (editing) {
        await updateBook(editing.id, form);
        setMessage("Livro atualizado com sucesso.");
      } else {
        if (!file) {
          setError("Selecione um arquivo PDF, JPG ou PNG.");
          return;
        }
        await createBook({ ...form, type, file });
        setMessage("Livro cadastrado e enviado para processamento.");
      }
      resetForm();
      loadBooks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível salvar o livro.");
    }
  }

  function beginEdit(book: Book) {
    setEditing(book);
    setForm({
      title: book.title,
      author: book.author,
      summary: book.summary,
      publication_date: book.publication_date,
    });
    setType(book.type);
    setFile(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function confirmRemoveBook() {
    if (!bookToDelete) return;

    try {
      await deleteBook(bookToDelete.id);
      setMessage("Livro excluído.");
      setBookToDelete(null);
      loadBooks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível excluir o livro.");
    }
  }

  async function retry(book: Book) {
    try {
      await retryBookProcessing(book.id);
      setMessage("Reprocessamento solicitado.");
      loadBooks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível retentar o processamento.");
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[26rem_1fr]">
      <section className="rounded-[1.5rem] bg-white p-5 shadow-sm shadow-stone-900/5">
        <h2 className="text-xl font-black tracking-[-0.03em] text-stone-950">{editing ? "Editar livro" : "Novo livro"}</h2>
        <form onSubmit={handleSubmit} className="mt-5 grid gap-4">
          <Field label="Título">
            <input required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} className="input" />
          </Field>
          <Field label="Autor">
            <input required value={form.author} onChange={(event) => setForm({ ...form, author: event.target.value })} className="input" />
          </Field>
          <Field label="Resumo">
            <textarea required rows={5} value={form.summary} onChange={(event) => setForm({ ...form, summary: event.target.value })} className="input resize-none" />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Publicação">
              <input required type="date" value={form.publication_date} onChange={(event) => setForm({ ...form, publication_date: event.target.value })} className="input" />
            </Field>
            <Field label="Tipo">
              <select disabled={Boolean(editing)} value={type} onChange={(event) => setType(event.target.value as BookType)} className="input">
                <option value="common">Comum</option>
                <option value="technical">Técnico</option>
              </select>
            </Field>
          </div>
          {!editing && (
            <Field label="Arquivo">
              <input required type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="input file:mr-3 file:rounded-xl file:border-0 file:bg-stone-950 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white" />
            </Field>
          )}
          <div className="flex flex-wrap gap-3 pt-2">
            <button disabled={isPending} className="btn btn-primary">
              {editing ? "Salvar alterações" : "Cadastrar livro"}
            </button>
            {editing && (
              <button type="button" onClick={resetForm} className="btn btn-secondary">
                Cancelar
              </button>
            )}
          </div>
        </form>
        {(message || error) && (
          <p className={`mt-4 rounded-2xl px-4 py-3 text-sm font-semibold ${error ? "bg-rose-50 text-rose-800" : "bg-emerald-50 text-emerald-800"}`}>
            {error ?? message}
          </p>
        )}
      </section>

      <section className="min-w-0 rounded-[1.5rem] bg-white p-5 shadow-sm shadow-stone-900/5">
        <div className="rounded-[1.35rem] border border-stone-200 bg-gradient-to-br from-stone-950 to-stone-800 p-5 text-white shadow-xl shadow-stone-900/10">
          <div>
            <h2 className="text-2xl font-black tracking-[-0.04em]">Acervo</h2>
            <p className="mt-1 text-sm text-stone-300">{books.length} livro(s) encontrados. Status atualizado em tempo real quando houver processamento ativo.</p>
          </div>
          <form
            className="mt-5 grid gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              loadBooks(filters);
            }}
          >
            <input placeholder="Filtrar por título" value={filters.title} onChange={(event) => setFilters({ ...filters, title: event.target.value })} className="input border-white/15 bg-white/10 text-white placeholder:text-stone-300 focus:border-white focus:bg-white/15" />
            <input placeholder="Filtrar por autor" value={filters.author} onChange={(event) => setFilters({ ...filters, author: event.target.value })} className="input border-white/15 bg-white/10 text-white placeholder:text-stone-300 focus:border-white focus:bg-white/15" />
            <div className="flex flex-col gap-3 sm:flex-row">
              <button className="btn btn-success sm:min-w-28">Buscar</button>
              <button type="button" onClick={() => { setFilters({ title: "", author: "" }); loadBooks({ title: "", author: "" }); }} className="btn border border-white/15 bg-white/10 text-white hover:bg-white/15 sm:min-w-28">Limpar</button>
            </div>
          </form>
        </div>

        <div className="mt-5 grid gap-5">
          {books.map((book) => {
            const realtimeProgress = progressByBook[book.id];
            const status = realtimeProgress?.status ?? book.processing_status;
            const progress = Math.max(0, Math.min(100, realtimeProgress?.progress ?? defaultProgress[status]));
            const isFailed = status === "processing failed";
            const canRetry = isFailed && book.processing_attempts < 3;

            return (
              <article key={book.id} className="group overflow-hidden rounded-[1.75rem] border border-stone-200 bg-white shadow-sm shadow-stone-900/5 transition hover:-translate-y-0.5 hover:shadow-2xl hover:shadow-stone-900/10">
                <div className="grid gap-0 lg:grid-cols-[0.72rem_1fr]">
                  <div className={`${isFailed ? "bg-rose-500" : status === "processed" ? "bg-emerald-500" : "bg-indigo-500"}`} />
                  <div className="p-5">
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="flex min-w-0 flex-wrap gap-2">
                        <span className={`rounded-full px-3 py-1 text-xs font-black ring-1 ${statusClasses[status]}`}>{statusLabels[status]}</span>
                        <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-bold text-stone-600">{book.type === "technical" ? "Técnico" : "Comum"}</span>
                        <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-bold text-stone-600">{book.file_extension.toUpperCase()}</span>
                        <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-bold text-stone-600">{book.processing_attempts}/3 tentativas</span>
                      </div>
                      <div className="flex shrink-0 flex-wrap gap-2">
                        <button onClick={() => beginEdit(book)} className="btn btn-secondary">Editar</button>
                        {isFailed && (
                          <button onClick={() => retry(book)} disabled={!canRetry} className="btn bg-indigo-600 text-white shadow-lg shadow-indigo-900/15 hover:bg-indigo-700">
                            {canRetry ? "Reprocessar" : "Limite atingido"}
                          </button>
                        )}
                        <button onClick={() => setBookToDelete(book)} className="btn btn-danger">Excluir</button>
                      </div>
                    </div>

                    <div className="mt-4 w-full min-w-0">
                      <h3 className="text-2xl font-black tracking-[-0.04em] text-stone-950 sm:text-3xl">{book.title}</h3>
                      <p className="mt-1 text-sm font-semibold text-stone-600">{book.author} · {new Date(`${book.publication_date}T00:00:00`).toLocaleDateString("pt-BR")}</p>
                      <p className="mt-4 line-clamp-3 w-full leading-7 text-stone-600">{book.summary}</p>
                    </div>

                    <div className="mt-5 rounded-2xl bg-stone-50 p-4">
                      <div className="mb-2 flex items-center justify-between text-xs font-black uppercase tracking-[0.16em] text-stone-500">
                        <span>Processamento</span>
                        <span>{Math.round(progress)}%</span>
                      </div>
                      <div className="h-3 overflow-hidden rounded-full bg-stone-200">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${isFailed ? "bg-rose-500" : status === "processed" ? "bg-emerald-500" : "bg-gradient-to-r from-indigo-500 to-emerald-400"}`}
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      {isFailed && (
                        <p className="mt-3 text-sm font-semibold text-rose-700">
                          Processamento falhou. Tentativas realizadas: {book.processing_attempts} de 3.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
          {!books.length && <p className="rounded-3xl border border-dashed border-stone-300 p-8 text-center text-stone-500">Nenhum livro encontrado.</p>}
        </div>
      </section>

      <ConfirmDialog
        open={Boolean(bookToDelete)}
        title="Excluir livro?"
        description={`Esta ação remove o livro${bookToDelete ? ` "${bookToDelete.title}"` : ""} e seus dados relacionados. Essa operação não pode ser desfeita.`}
        confirmLabel="Excluir livro"
        onConfirm={confirmRemoveBook}
        onCancel={() => setBookToDelete(null)}
      />
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-2 text-sm font-bold text-stone-700">
      {label}
      {children}
    </label>
  );
}
