import type { Founder } from "./types";

const KEY = "flg.currentFounder";

export function saveFounder(founder: Founder): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, JSON.stringify(founder));
}

export function loadFounder(): Founder | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Founder;
  } catch {
    return null;
  }
}

export function clearFounder(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(KEY);
}
