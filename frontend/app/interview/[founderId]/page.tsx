"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import {
  ARCHETYPE_LABELS,
  CHANNEL_LABELS,
  FORMAT_LABELS,
} from "@/lib/labels";
import { useAuthGuard } from "@/lib/useAuthGuard";
import type {
  Canal,
  DiagnosticProfile,
  Founder,
  InterviewQuestion,
} from "@/lib/types";

type Message = { role: "ai" | "user"; text: string };
type Status = "loading" | "chat" | "profiling" | "profile" | "error";

const BLOCK_TITLES = ["Tese de Mercado", "Ativos & Comunicação", "Fronteiras & Rotina"];

export default function InterviewPage() {
  const router = useRouter();
  const params = useParams<{ founderId: string }>();
  const founderId = params.founderId;
  const { ready } = useAuthGuard();

  const started = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [founder, setFounder] = useState<Founder | null>(null);
  const [diagnosticId, setDiagnosticId] = useState<string | null>(null);
  const [current, setCurrent] = useState<InterviewQuestion | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<Status>("loading");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<DiagnosticProfile | null>(null);
  const [selectedChannels, setSelectedChannels] = useState<Canal[]>([]);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (started.current) return;
    started.current = true;

    (async () => {
      try {
        const [founderInfo, res] = await Promise.all([
          api.getFounder(founderId),
          api.startInterview(founderId),
        ]);
        setFounder(founderInfo);
        setDiagnosticId(res.diagnostic_id);
        const first = res.questions[0] ?? null;
        setCurrent(first);
        setMessages([
          {
            role: "ai",
            text: "Vamos começar o diagnóstico de posicionamento. Responda com sinceridade — suas respostas definem seu arquétipo e a estratégia de conteúdo.",
          },
          ...(first ? [{ role: "ai" as const, text: first.text }] : []),
        ]);
        setStatus("chat");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao iniciar entrevista.");
        setStatus("error");
      }
    })();
  }, [founderId, ready]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy, profile]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!current || !diagnosticId || !input.trim() || busy) return;

    const question = current;
    const value = input.trim();
    setMessages((m) => [...m, { role: "user", text: value }]);
    setInput("");
    setBusy(true);
    setError(null);

    try {
      const res = await api.answer(diagnosticId, { [question.key]: value });

      if (res.status === "completed") {
        setStatus("profiling");
        const prof = await api.complete(diagnosticId);
        setProfile(prof);
        const eligible = prof.channel_allocation
          .map((a) => a.channel)
          .filter((c) => c === "instagram" || c === "linkedin");
        setSelectedChannels(
          eligible.length > 0 ? eligible : ["instagram", "linkedin"],
        );
        setCurrent(null);
        setStatus("profile");
      } else {
        const next = res.next_questions?.[0] ?? null;
        setCurrent(next);
        if (next) setMessages((m) => [...m, { role: "ai", text: next.text }]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao registrar resposta.");
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerate() {
    if (!founderId || selectedChannels.length === 0) return;
    setGenerating(true);
    setError(null);
    try {
      const { grid_id } = await api.generatePlan(founderId, selectedChannels);
      router.push(`/grid/${grid_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar o plano.");
      setGenerating(false);
    }
  }

  function toggleChannel(channel: Canal) {
    setSelectedChannels((prev) =>
      prev.includes(channel)
        ? prev.filter((c) => c !== channel)
        : [...prev, channel],
    );
  }

  const activeBlock = current?.block ?? 3;

  return (
    <div className="animate-fade-up">
      <div className="mb-6 flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Entrevista diagnóstica
        </h1>
        <p className="text-sm text-slate-400">
          {founder ? `${founder.name} · ${founder.company_name}` : "Carregando fundador..."}
        </p>
      </div>

      {status !== "profile" && (
        <div className="mb-6 flex gap-3">
          {BLOCK_TITLES.map((title, index) => {
            const block = index + 1;
            const isActive = status === "chat" && activeBlock === block;
            const isDone = status === "profiling" || block < activeBlock;
            return (
              <div
                key={title}
                className={`flex-1 rounded-xl border px-3 py-2 text-xs ${
                  isActive
                    ? "border-brand-400/40 bg-brand-400/10 text-brand-200"
                    : isDone
                      ? "border-white/10 bg-white/[0.03] text-slate-300"
                      : "border-white/5 bg-transparent text-slate-600"
                }`}
              >
                <span className="font-semibold">Bloco {block}</span>
                <span className="ml-2 hidden sm:inline">{title}</span>
              </div>
            );
          })}
        </div>
      )}

      {status === "loading" && (
        <div className="glass-card flex items-center gap-3 p-6 text-sm text-slate-400">
          <Spinner /> Iniciando sessão de diagnóstico...
        </div>
      )}

      {status === "error" && (
        <div className="glass-card border-red-400/30 bg-red-400/5 p-6 text-sm text-red-300">
          {error ?? "Ocorreu um erro."}
        </div>
      )}

      {status === "chat" && (
        <div className="glass-card flex h-[62vh] flex-col overflow-hidden">
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-6">
            {messages.map((message, index) => (
              <Bubble key={index} message={message} />
            ))}
            {busy && (
              <div className="flex items-center gap-2 text-slate-500">
                <TypingDots />
                <span className="text-xs">Analisando...</span>
              </div>
            )}
          </div>

          <form
            onSubmit={handleSubmit}
            className="border-t border-white/10 bg-white/[0.02] p-4"
          >
            <div className="flex items-end gap-3">
              <textarea
                className="input-field max-h-32 min-h-[52px] resize-none"
                placeholder="Digite sua resposta..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                disabled={busy}
              />
              <button
                type="submit"
                disabled={busy || !input.trim()}
                className="btn-primary h-[52px] px-6"
              >
                Enviar
              </button>
            </div>
            {error && <p className="mt-2 text-xs text-red-300">{error}</p>}
          </form>
        </div>
      )}

      {status === "profiling" && (
        <div className="glass-card flex items-center gap-3 p-6 text-sm text-slate-300">
          <Spinner /> Compilando arquétipo e matriz de canais...
        </div>
      )}

      {status === "profile" && profile && (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="glass-card p-6">
              <p className="text-xs uppercase tracking-wider text-brand-300">
                Arquétipo dominante
              </p>
              <h2 className="mt-2 text-xl font-bold text-white">
                {ARCHETYPE_LABELS[profile.dominant_archetype]}
              </h2>
              {profile.secondary_archetype && (
                <p className="mt-3 text-sm text-slate-400">
                  Secundário:{" "}
                  <span className="text-slate-200">
                    {ARCHETYPE_LABELS[profile.secondary_archetype]}
                  </span>
                </p>
              )}
            </div>
            <div className="glass-card p-6">
              <p className="text-xs uppercase tracking-wider text-brand-300">
                Tese central de comunicação
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-200">
                {profile.central_thesis}
              </p>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">
                Matriz de canais recomendada
              </h3>
              <span className="text-xs text-slate-500">
                Selecione os canais para o plano
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {profile.channel_allocation.map((alloc) => {
                const active = selectedChannels.includes(alloc.channel);
                return (
                  <button
                    key={alloc.channel}
                    type="button"
                    onClick={() => toggleChannel(alloc.channel)}
                    className={`rounded-xl border p-4 text-left transition ${
                      active
                        ? "border-brand-400/50 bg-brand-400/10"
                        : "border-white/10 bg-white/[0.02] opacity-60 hover:opacity-100"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">
                        {CHANNEL_LABELS[alloc.channel]}
                      </span>
                      <span className="chip border-white/10 bg-white/5 text-slate-300">
                        {alloc.dedication_percent}% ·{" "}
                        {alloc.role === "primario" ? "Primário" : "Secundário"}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">
                      {alloc.native_formats
                        .map((f) => FORMAT_LABELS[f])
                        .join(" · ")}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {error && (
            <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">
              {error}
            </p>
          )}

          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating || selectedChannels.length === 0}
              className="btn-primary"
            >
              {generating
                ? "Gerando plano..."
                : "Gerar plano (49 posts / 30 dias)"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Bubble({ message }: { message: Message }) {
  const isAi = message.role === "ai";
  return (
    <div className={`flex ${isAi ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isAi
            ? "border border-white/10 bg-white/[0.04] text-slate-200"
            : "bg-brand-500 text-slate-950"
        }`}
      >
        {message.text}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <span className="flex gap-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-slate-400"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </span>
  );
}

function Spinner() {
  return (
    <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-400/40 border-t-brand-400" />
  );
}
