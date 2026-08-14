import { cookies } from "next/headers";
import { NextRequest } from "next/server";

function mutationOriginAllowed(request: NextRequest) {
  if (["GET", "HEAD", "OPTIONS"].includes(request.method)) return true;
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite === "cross-site") return false;
  const origin = request.headers.get("origin");
  return !origin || origin === request.nextUrl.origin;
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (!mutationOriginAllowed(request)) {
    return Response.json({ error: "Cross-site mutation rejected" }, { status: 403 });
  }
  const { path } = await context.params;
  const upstream = (process.env.REDTAG_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1").replace(/\/$/, "");
  const source = new URL(request.url);
  const target = `${upstream}/${path.map(encodeURIComponent).join("/")}${source.search}`;
  const store = await cookies();
  const tenant = store.get("redtag_tenant")?.value || process.env.REDTAG_DEFAULT_TENANT_ID || "tenant_demo";
  const token = store.get("redtag_id_token")?.value;

  const headers = new Headers();
  for (const name of ["accept", "content-type", "idempotency-key", "x-request-id"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set("X-Tenant-ID", tenant);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const body = hasBody ? await request.arrayBuffer() : undefined;
  const response = await fetch(target, { method: request.method, headers, body, cache: "no-store", redirect: "manual" });
  const outHeaders = new Headers();
  for (const name of ["content-type", "x-request-id", "location"]) {
    const value = response.headers.get(name);
    if (value) outHeaders.set(name, value);
  }
  return new Response(await response.arrayBuffer(), { status: response.status, headers: outHeaders });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
