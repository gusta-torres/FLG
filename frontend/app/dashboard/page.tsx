"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { BUSINESS_MODEL_LABELS } from "@/lib/labels";
import { useAuthGuard } from "@/lib/useAuthGuard";
import type {
  CreateFounderPayload,
  Founder,
  LeaderboardEntry,
  ModeloNegocio,
} from "@/lib/types";

const BUSINESS_MODELS = Object.entries(BUSINESS_MODEL_LABELS) as [
  ModeloNegocio,
  string,
][];

const EMPTY_FORM: CreateFounderPayload = {
  name: "",
  company_name: "",
  business_model: "b2b_servicos_executivos",
  email: "",
  password: "",
};

export default function DashboardPage() {
  const router = useRouter();
  const { ready, user } = useAuthGuard();

  const [founders, setFounders] = useState<Founder[]>([]);
  const [board, setBoard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CreateFounderPayload>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [f, b] = await Promise.all([api.listFounders(), api.leaderboard()]);
      setFounders(f);
      setBoard(b);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  const boardById = new Map(board.map((entry) => [entry.founder_id, entry]));

  async function openPlan(founderId: string) {
    setBusyId(founderId);
    setError(null);
    try {
      const existing = await api.getFounderPlan(founderId);
      if (existing.grid_id) {
        router.push(`/grid/${existing.grid_id}`);
        return;
      }
      const { grid_id } = await api.generatePlan(founderId);
      router.push(`/grid/${grid_id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message} (o founder já concluiu o diagnóstico?)`
          : "Erro ao abrir o plano.",
      );
      setBusyId(null);
    }
  }

  async function createFounder(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const founder = await api.createFounder(form);
      setForm(EMPTY_FORM);
      setShowForm(false);
      await load();
      router.push(`/interview/${founder.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar founder.");
    } finally {
      setSaving(false);
    }
  }

  if (!ready) return null;

  return (
    <div className="animate-fade-up space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Painel</h1>
          <p className="mt-1 text-sm text-slate-400">
            {user?.role === "marketing"
              ? "Gerencie os founders e acompanhe a competição de conteúdo."
              : "Acompanhe seu plano e suba no placar."}
          </p>
        </div>
        {user?.role === "marketing" && (
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Fechar" : "+ Novo founder"}
          </button>
        )}
      </div>

      {error && (
        <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      {showForm && user?.role === "marketing" && (
        <form onSubmit={createFounder} className="glass-card space-y-4 p-6">
          <h2 className="text-sm font-semibold text-white">Cadastrar founder</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs text-slate-400">Nome</label>
              <input
                className="input-field"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-slate-400">Empresa</label>
              <input
                className="input-field"
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-slate-400">Email de acesso</label>
              <input
                type="email"
                className="input-field"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs text-slate-400">
                Senha (mín. 6 caracteres)
              </label>
              <input
                type="text"
                className="input-field"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                minLength={6}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1.5 block text-xs text-slate-400">
                Modelo de negócio
              </label>
              <select
                className="input-field"
                value={form.business_model}
                onChange={(e) =>
                  setForm({ ...form, business_model: e.target.value as ModeloNegocio })
                }
              >
                {BUSINESS_MODELS.map(([value, label]) => (
                  <option key={value} value={value} className="bg-slate-900">
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Criando..." : "Cadastrar e iniciar diagnóstico"}
            </button>
          </div>
        </form>
      )}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-300">Founders</h2>
        {loading ? (
          <p className="text-sm text-slate-500">Carregando...</p>
        ) : founders.length === 0 ? (
          <div className="glass-card p-6 text-sm text-slate-400">
            Nenhum founder cadastrado ainda.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {founders.map((founder) => {
              const entry = boardById.get(founder.id);
              return (
                <div key={founder.id} className="glass-card flex flex-col p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="font-semibold text-white">{founder.name}</h3>
                      <p className="text-xs text-slate-500">{founder.company_name}</p>
                    </div>
                    {entry && (
                      <span className="chip border-brand-400/30 bg-brand-400/10 text-brand-300">
                        🔥 {entry.streak}
                      </span>
                    )}
                  </div>

                  <p className="mt-2 text-[11px] text-slate-500">
                    {BUSINESS_MODEL_LABELS[founder.business_model]}
                  </p>

                  <div className="mt-4">
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>
                        {entry ? entry.posted_posts : 0}/
                        {entry ? entry.total_posts : 0} postados
                      </span>
                      <span>{entry ? entry.completion_pct : 0}%</span>
                    </div>
                    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-brand-500"
                        style={{ width: `${entry ? entry.completion_pct : 0}%` }}
                      />
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <button
                      className="btn-ghost flex-1"
                      onClick={() => router.push(`/interview/${founder.id}`)}
                    >
                      Diagnóstico
                    </button>
                    <button
                      className="btn-primary flex-1"
                      disabled={busyId === founder.id}
                      onClick={() => openPlan(founder.id)}
                    >
                      {busyId === founder.id ? "Gerando..." : "Plano"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300">
            Placar da competição
          </h2>
          <button className="btn-ghost" onClick={() => router.push("/leaderboard")}>
            Ver placar completo
          </button>
        </div>
        <div className="glass-card divide-y divide-white/5">
          {board.length === 0 ? (
            <p className="p-5 text-sm text-slate-400">Sem dados ainda.</p>
          ) : (
            board.map((entry, index) => (
              <div
                key={entry.founder_id}
                className="flex items-center justify-between gap-4 p-4"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/5 text-xs font-bold text-slate-300">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-white">{entry.name}</p>
                    <p className="text-[11px] text-slate-500">
                      {entry.posted_posts} postados · {entry.completion_pct}%
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-amber-300">🔥 {entry.streak}</span>
                  <span className="font-semibold text-brand-300">{entry.xp} XP</span>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
