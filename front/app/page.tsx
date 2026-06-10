import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-10">
      <section className="overflow-hidden rounded-[2rem] border border-stone-200/80 bg-white/75 p-8 shadow-2xl shadow-stone-900/10 backdrop-blur md:p-12">
        <p className="mb-5 inline-flex rounded-full bg-emerald-100 px-4 py-2 text-sm font-semibold text-emerald-900">
          Biblioteca inteligente
        </p>
        <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <h1 className="max-w-3xl text-5xl font-black tracking-[-0.05em] text-stone-950 md:text-7xl">
              Conhecimento organizado, pronto para conversar.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-650">
              Cadastre livros, acompanhe o processamento e use o chat para consultar sua base com uma interface direta e limpa.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <Link
              href="/books"
              className="group rounded-3xl bg-stone-950 p-6 text-white transition hover:-translate-y-1 hover:shadow-xl hover:shadow-stone-900/20"
            >
              <span className="text-sm font-semibold text-emerald-200">Gerenciamento</span>
              <strong className="mt-3 block text-2xl">Livros</strong>
              <span className="mt-8 block text-sm text-stone-300 group-hover:text-white">Cadastrar, editar e processar arquivos.</span>
            </Link>
            <Link
              href="/chat"
              className="group rounded-3xl border border-stone-200 bg-white p-6 transition hover:-translate-y-1 hover:shadow-xl hover:shadow-stone-900/10"
            >
              <span className="text-sm font-semibold text-indigo-700">Consulta semântica</span>
              <strong className="mt-3 block text-2xl text-stone-950">Chat</strong>
              <span className="mt-8 block text-sm text-stone-600 group-hover:text-stone-950">Pergunte e receba respostas contextualizadas.</span>
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
