import { AppShell } from "@/components/app-shell";
import { ChatPanel } from "@/components/chat-panel";

export default function ChatPage() {
  return (
    <AppShell
      active="chat"
      eyebrow="Assistente"
      title="Chat com a biblioteca"
      description="Converse com o conteúdo processado dos livros e receba respostas contextualizadas em tempo real."
    >
      <ChatPanel />
    </AppShell>
  );
}
