import { NextRequest } from "next/server";

function resolveApiBase(): string {
  const raw = process.env.API_INTERNAL_URL ?? "";
  if (!raw) return "http://localhost:8000";
  if (/^https?:\/\//i.test(raw)) return raw;
  return `http://${raw}`;
}

const API_BASE = resolveApiBase();

type Ctx = { params: Promise<{ path: string[] }> };

async function proxy(req: NextRequest, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  const target = `${API_BASE}/api/${path.join("/")}${req.nextUrl.search}`;

  const headers: Record<string, string> = {
    "content-type": req.headers.get("content-type") ?? "application/json",
  };
  const auth = req.headers.get("authorization");
  if (auth) headers["authorization"] = auth;

  const hasBody = !["GET", "HEAD"].includes(req.method);

  let res: Response;
  try {
    res = await fetch(target, {
      method: req.method,
      headers,
      body: hasBody ? await req.text() : undefined,
      cache: "no-store",
    });
  } catch {
    return Response.json(
      { detail: "Não foi possível conectar à API." },
      { status: 502 },
    );
  }

  const text = await res.text();
  return new Response(text, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/json",
    },
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
