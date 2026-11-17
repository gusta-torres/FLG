"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import type { LeaderboardEntry } from "@/lib/types";

const MEDALS = ["🥇", "🥈", "🥉"];

export default function LeaderboardPage() {
  const { ready } = useAuthGuard();
  const [board, setBoard] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api
      .leaderboard()
      .then(setBoard)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Erro ao carregar placar."),
      );
  }, [ready]);

  if (!ready) return null;

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Placar da competição
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Consistência vence: mantenha a ofensiva 🔥 e suba de posição.
        </p>
      </div>

      {error && (
        <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        {board.map((entry, index) => (
          <div
            key={entry.founder_id}
            className={`glass-card p-6 ${
              index === 0 ? "border-brand-400/40 bg-brand-400/5" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-2xl">{MEDALS[index] ?? index + 1}</span>
              <span className="text-amber-300">🔥 {entry.streak}</span>
            </div>
            <h3 className="mt-3 font-semibold text-white">{entry.name}</h3>
            <p className="text-xs text-slate-500">{entry.company_name}</p>

            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-[11px] text-slate-500">Postados</p>
                <p className="font-semibold text-white">
                  {entry.posted_posts}/{entry.total_posts}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500">Conclusão</p>
                <p className="font-semibold text-white">{entry.completion_pct}%</p>
              </div>
            </div>

            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-brand-500"
                style={{ width: `${entry.completion_pct}%` }}
              />
            </div>

            <p className="mt-4 text-right text-sm font-bold text-brand-300">
              {entry.xp} XP
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
