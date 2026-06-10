import { AppShell } from "@/components/app-shell";
import { BookManager } from "@/components/book-manager";

export default function BooksPage() {
  return (
    <AppShell
      active="books"
      eyebrow="Acervo"
      title="Gerenciamento de livros"
      description="Cadastre arquivos, edite metadados e acompanhe o processamento para alimentar a biblioteca inteligente."
    >
      <BookManager />
    </AppShell>
  );
}
