import Link from "next/link";

type AppShellProps = {
  children: React.ReactNode;
  active: "books" | "chat";
  eyebrow: string;
  title: string;
  description: string;
};

const navItems = [
  { href: "/books", label: "Livros", key: "books" },
  { href: "/chat", label: "Chat", key: "chat" },
] as const;

export function AppShell({ children, active, eyebrow, title, description }: AppShellProps) {
  return (
    <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-[17rem_1fr]">
        <aside className="rounded-[1.75rem] border border-stone-200/80 bg-stone-950 p-5 text-white shadow-2xl shadow-stone-900/15 lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)]">
          <Link href="/" className="block rounded-2xl border border-white/10 bg-white/5 p-4">
            <span className="text-sm font-medium text-emerald-200">Smart Library</span>
            <strong className="mt-2 block text-2xl tracking-[-0.04em]">Painel</strong>
          </Link>
          <nav className="mt-6 grid gap-2">
            {navItems.map((item) => (
              <Link
                key={item.key}
                href={item.href}
                className={`rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                  active === item.key
                    ? "bg-white text-stone-950"
                    : "text-stone-300 hover:bg-white/10 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-8 rounded-2xl bg-emerald-300/10 p-4 text-sm leading-6 text-emerald-50">
            API direta em <span className="font-mono text-emerald-200">{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</span>
          </div>
        </aside>
        <section className="min-w-0 rounded-[1.75rem] border border-stone-200/80 bg-white/75 p-4 shadow-2xl shadow-stone-900/10 backdrop-blur sm:p-6">
          <header className="mb-6 rounded-[1.5rem] bg-white p-5 shadow-sm shadow-stone-900/5 sm:p-6">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-emerald-700">{eyebrow}</p>
            <h1 className="mt-2 text-3xl font-black tracking-[-0.04em] text-stone-950 sm:text-5xl">{title}</h1>
            <p className="mt-3 max-w-3xl leading-7 text-stone-600">{description}</p>
          </header>
          {children}
        </section>
      </div>
    </main>
  );
}
