"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import {
  ATTRIBUTION_LABELS,
  CHANNEL_LABELS,
  FUNNEL_ACCENTS,
  FUNNEL_LABELS,
  FORMAT_LABELS,
} from "@/lib/labels";
import { useAuthGuard } from "@/lib/useAuthGuard";
import type { Canal, ContentItem, ContentStatus, EditorialGrid } from "@/lib/types";

const STATUS_LABEL: Record<ContentStatus, string> = {
  pendente: "Pendente",
  aprovado: "Aprovado",
  postado: "Postado",
};

const STATUS_STYLE: Record<ContentStatus, string> = {
  pendente: "border-white/10 bg-white/5 text-slate-300",
  aprovado: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  postado: "border-brand-400/40 bg-brand-400/10 text-brand-200",
};

type StatusFilter = "todos" | ContentStatus;
type ChannelFilter = "todos" | "instagram" | "linkedin";

export default function GridPage() {
  const params = useParams<{ gridId: string }>();
  const gridId = params.gridId;
  const { ready } = useAuthGuard();

  const [grid, setGrid] = useState<EditorialGrid | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("todos");
  const [channelFilter, setChannelFilter] = useState<ChannelFilter>("todos");
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.getGrid(gridId);
      setGrid(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar o plano.");
    } finally {
      setLoading(false);
    }
  }, [gridId]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  const replaceItem = (updated: ContentItem) => {
    setGrid((current) =>
      current
        ? {
            ...current,
            items: current.items.map((i) => (i.id === updated.id ? updated : i)),
          }
        : current,
    );
  };

  async function setStatus(item: ContentItem, status: ContentStatus) {
    setBusyId(item.id);
    setError(null);
    try {
      replaceItem(await api.updateItemStatus(item.id, status));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar status.");
    } finally {
      setBusyId(null);
    }
  }

  async function genText(item: ContentItem) {
    setBusyId(item.id);
    setError(null);
    try {
      const updated = await api.generateItemText(item.id);
      replaceItem(updated);
      setExpanded(updated.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar texto.");
    } finally {
      setBusyId(null);
    }
  }

  const items = useMemo(() => {
    if (!grid) return [];
    return grid.items.filter(
      (i) =>
        (statusFilter === "todos" || i.status === statusFilter) &&
        (channelFilter === "todos" || i.channel === channelFilter),
    );
  }, [grid, statusFilter, channelFilter]);

  const byDay = useMemo(() => {
    const map = new Map<number, ContentItem[]>();
    for (const item of items) {
      const list = map.get(item.day) ?? [];
      list.push(item);
      map.set(item.day, list);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [items]);

  if (!ready) return null;

  if (loading) {
    return (
      <div className="glass-card flex items-center gap-3 p-6 text-sm text-slate-400">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-400/40 border-t-brand-400" />
        Carregando plano...
      </div>
    );
  }

  if (!grid) {
    return (
      <div className="glass-card border-red-400/30 bg-red-400/5 p-6 text-sm text-red-300">
        {error ?? "Plano não encontrado."}
      </div>
    );
  }

  const posted = grid.items.filter((i) => i.status === "postado").length;
  const pct = grid.items.length ? Math.round((posted / grid.items.length) * 100) : 0;

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Plano de Conteúdo
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {grid.goal_posts} posts em {grid.period_days} dias · Instagram e LinkedIn
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-white">
            {posted}/{grid.items.length} postados · {pct}%
          </p>
          <div className="mt-1 h-1.5 w-40 overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full bg-brand-500" style={{ width: `${pct}%` }} />
          </div>
        </div>
      </div>

      {error && (
        <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <FilterGroup
          options={[
            ["todos", "Todos"],
            ["pendente", "Pendentes"],
            ["aprovado", "Aprovados"],
            ["postado", "Postados"],
          ]}
          value={statusFilter}
          onChange={(v) => setStatusFilter(v as StatusFilter)}
        />
        <FilterGroup
          options={[
            ["todos", "Todos os canais"],
            ["instagram", "Instagram"],
            ["linkedin", "LinkedIn"],
          ]}
          value={channelFilter}
          onChange={(v) => setChannelFilter(v as ChannelFilter)}
        />
      </div>

      <div className="space-y-5">
        {byDay.map(([day, dayItems]) => (
          <section key={day}>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Dia {day}
            </h2>
            <div className="space-y-3">
              {dayItems.map((item) => (
                <article key={item.id} className="glass-card p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="chip border-white/10 bg-white/5 text-slate-300">
                      {CHANNEL_LABELS[item.channel as Canal]}
                    </span>
                    <span className={`chip ${FUNNEL_ACCENTS[item.funnel_level]}`}>
                      {FUNNEL_LABELS[item.funnel_level]}
                    </span>
                    <span className="chip border-white/10 bg-white/5 text-slate-400">
                      {FORMAT_LABELS[item.format]}
                    </span>
                    <span className={`chip ml-auto ${STATUS_STYLE[item.status]}`}>
                      {STATUS_LABEL[item.status]}
                    </span>
                  </div>

                  <h3 className="mt-3 text-sm font-semibold leading-snug text-white">
                    “{item.hook}”
                  </h3>
                  <p className="mt-1 text-sm text-slate-400">{item.central_idea}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    CTA: <span className="text-slate-300">{item.cta}</span>
                  </p>

                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <select
                      className="rounded-lg border border-white/10 bg-white/[0.03] px-2 py-1 text-xs text-slate-200"
                      value={item.status}
                      disabled={busyId === item.id}
                      onChange={(e) =>
                        setStatus(item, e.target.value as ContentStatus)
                      }
                    >
                      <option value="pendente">Pendente</option>
                      <option value="aprovado">Aprovado</option>
                      <option value="postado">Postado</option>
                    </select>

                    <button
                      className="btn-ghost"
                      disabled={busyId === item.id}
                      onClick={() => genText(item)}
                    >
                      {busyId === item.id
                        ? "Gerando..."
                        : item.full_text
                          ? "Regerar texto"
                          : "Gerar texto"}
                    </button>

                    {item.full_text && (
                      <button
                        className="btn-ghost"
                        onClick={() =>
                          setExpanded(expanded === item.id ? null : item.id)
                        }
                      >
                        {expanded === item.id ? "Ocultar texto" : "Ver texto"}
                      </button>
                    )}

                    <span className="ml-auto text-[11px] text-slate-500">
                      {ATTRIBUTION_LABELS[item.attribution]}
                    </span>
                  </div>

                  {item.full_text && expanded === item.id && (
                    <pre className="mt-3 whitespace-pre-wrap rounded-xl border border-white/10 bg-white/[0.02] p-3 text-xs leading-relaxed text-slate-200">
                      {item.full_text}
                    </pre>
                  )}
                </article>
              ))}
            </div>
          </section>
        ))}
        {byDay.length === 0 && (
          <p className="text-sm text-slate-500">Nenhum post para os filtros atuais.</p>
        )}
      </div>
    </div>
  );
}

function FilterGroup({
  options,
  value,
  onChange,
}: {
  options: [string, string][];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1 rounded-xl border border-white/10 bg-white/[0.02] p-1">
      {options.map(([key, label]) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={`rounded-lg px-3 py-1.5 text-xs transition ${
            value === key
              ? "bg-brand-500 text-slate-950"
              : "text-slate-400 hover:text-white"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
