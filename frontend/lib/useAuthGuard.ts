"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getStoredUser, getToken } from "./api";
import type { User } from "./types";

export function useAuthGuard(requiredRole?: User["role"]) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = getToken();
    const current = getStoredUser();
    if (!token || !current) {
      router.replace("/login");
      return;
    }
    if (requiredRole && current.role !== requiredRole) {
      router.replace("/dashboard");
      return;
    }
    setUser(current);
    setReady(true);
  }, [router, requiredRole]);

  return { ready, user };
}
