"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (getToken()) router.replace("/dashboard");
  }, [router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.login(email.trim(), password);
      router.replace("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível entrar. Verifique email e senha.",
      );
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl items-center gap-12 lg:grid-cols-2">
      <section className="hidden lg:block">
        <span className="chip border-brand-400/30 bg-brand-400/10 text-brand-300">
          Founder-Led Growth
        </span>
        <h1 className="mt-6 text-4xl font-bold leading-tight tracking-tight text-white">
          O centro de comando do conteúdo dos founders.
        </h1>
        <p className="mt-5 text-sm leading-relaxed text-slate-400">
          Planos de 49 posts em 30 dias, calendário editorial e uma competição
          interna de consistência — tudo em um só lugar.
        </p>
      </section>

      <section className="glass-card animate-fade-up p-7">
        <h2 className="text-lg font-semibold text-white">Entrar</h2>
        <p className="mt-1 text-sm text-slate-400">
          Acesse com seu email e senha.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">
              Email
            </label>
            <input
              type="email"
              className="input-field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="voce@empresa.com"
              required
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">
              Senha
            </label>
            <input
              type="password"
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="mt-4 text-center text-[11px] text-slate-500">
          Acesso inicial do marketing: admin@flg.local / flg-admin-123
        </p>
      </section>
    </div>
  );
}
