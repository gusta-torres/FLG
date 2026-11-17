"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearSession, getStoredUser } from "@/lib/api";
import type { User } from "@/lib/types";

const ROLE_LABEL: Record<User["role"], string> = {
  marketing: "Marketing",
  founder: "Founder",
};

export default function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]);

  function logout() {
    clearSession();
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-20 border-b border-white/5 bg-[#070b10]/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href={user ? "/dashboard" : "/login"} className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 font-bold text-slate-950">
            F
          </span>
          <span className="text-sm font-semibold tracking-tight text-white">
            FLG Content System
          </span>
        </Link>

        {user ? (
          <div className="flex items-center gap-3">
            <Link
              href="/leaderboard"
              className="hidden text-sm text-slate-300 hover:text-white sm:block"
            >
              Placar
            </Link>
            <div className="text-right">
              <p className="text-sm font-medium text-white">{user.name}</p>
              <p className="text-[11px] text-slate-500">{ROLE_LABEL[user.role]}</p>
            </div>
            <button onClick={logout} className="btn-ghost">
              Sair
            </button>
          </div>
        ) : (
          <span className="hidden text-xs text-slate-500 sm:block">
            Founder-Led Growth · Estratégia de Conteúdo
          </span>
        )}
      </div>
    </header>
  );
}
