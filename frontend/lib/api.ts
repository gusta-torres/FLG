import type {
  AnswerResponse,
  Canal,
  ContentItem,
  ContentStatus,
  CreateFounderPayload,
  DiagnosticProfile,
  EditorialGrid,
  Founder,
  LeaderboardEntry,
  StartInterviewResponse,
  TokenResponse,
  User,
} from "./types";

// Em produção (Netlify) aponta direto para a API via NEXT_PUBLIC_API_URL.
// Em desenvolvimento, usa o proxy same-origin (/api/v1).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

const TOKEN_KEY = "flg.token";
const USER_KEY = "flg.user";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

function saveSession(token: string, user: User): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (res.status === 401) {
    clearSession();
  }

  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // noop
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  async login(email: string, password: string): Promise<User> {
    const data = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    saveSession(data.access_token, data.user);
    return data.user;
  },

  me(): Promise<User> {
    return request<User>("/auth/me");
  },

  listFounders(): Promise<Founder[]> {
    return request<Founder[]>("/founders");
  },

  getFounder(founderId: string): Promise<Founder> {
    return request<Founder>(`/founders/${founderId}`);
  },

  getFounderPlan(founderId: string): Promise<{ grid_id: string | null }> {
    return request<{ grid_id: string | null }>(`/founders/${founderId}/plan`);
  },

  createFounder(payload: CreateFounderPayload): Promise<Founder> {
    return request<Founder>("/founders", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  startInterview(founderId: string): Promise<StartInterviewResponse> {
    return request<StartInterviewResponse>("/diagnostics/session", {
      method: "POST",
      body: JSON.stringify({ founder_id: founderId }),
    });
  },

  answer(diagnosticId: string, answers: Record<string, string>): Promise<AnswerResponse> {
    return request<AnswerResponse>(`/diagnostics/${diagnosticId}/answer`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    });
  },

  complete(diagnosticId: string): Promise<DiagnosticProfile> {
    return request<DiagnosticProfile>(`/diagnostics/${diagnosticId}/complete`, {
      method: "POST",
    });
  },

  generatePlan(
    founderId: string,
    channels: Canal[] = ["instagram", "linkedin"],
    periodDays = 30,
    goalPosts = 49,
  ): Promise<{ grid_id: string }> {
    return request<{ grid_id: string }>("/editorial-grids", {
      method: "POST",
      body: JSON.stringify({
        founder_id: founderId,
        channels,
        period_days: periodDays,
        goal_posts: goalPosts,
      }),
    });
  },

  getGrid(gridId: string): Promise<EditorialGrid> {
    return request<EditorialGrid>(`/editorial-grids/${gridId}`);
  },

  updateItemStatus(itemId: string, status: ContentStatus): Promise<ContentItem> {
    return request<ContentItem>(`/content-items/${itemId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  generateItemText(itemId: string): Promise<ContentItem> {
    return request<ContentItem>(`/content-items/${itemId}/generate-text`, {
      method: "POST",
    });
  },

  leaderboard(): Promise<LeaderboardEntry[]> {
    return request<LeaderboardEntry[]>("/leaderboard");
  },
};
