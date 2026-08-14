import { NextRequest, NextResponse } from "next/server";

const secure = process.env.NODE_ENV === "production";

function sameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite === "cross-site") return false;
  return !origin || origin === request.nextUrl.origin;
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ error: "Cross-site request rejected" }, { status: 403 });
  const body = await request.json().catch(() => ({}));
  const token = typeof body.token === "string" ? body.token.trim() : "";
  const tenantId = typeof body.tenant_id === "string" ? body.tenant_id.trim() : "";
  if (!token || token.length > 10000) return NextResponse.json({ error: "Invalid identity token" }, { status: 400 });
  if (!tenantId || tenantId.length > 128) return NextResponse.json({ error: "Invalid tenant" }, { status: 400 });

  const response = NextResponse.json({ ok: true });
  response.cookies.set("redtag_id_token", token, { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 55 * 60 });
  response.cookies.set("redtag_tenant", tenantId, { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 55 * 60 });
  return response;
}

export async function DELETE(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ error: "Cross-site request rejected" }, { status: 403 });
  const response = NextResponse.json({ ok: true });
  response.cookies.set("redtag_id_token", "", { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 0 });
  response.cookies.set("redtag_tenant", "", { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 0 });
  return response;
}
