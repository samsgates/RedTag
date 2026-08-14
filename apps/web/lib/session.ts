import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function ensureAuth() {
  const mode = process.env.REDTAG_AUTH_MODE || process.env.NEXT_PUBLIC_AUTH_MODE || "dev";
  if (mode === "dev") return;
  const store = await cookies();
  if (!store.get("redtag_id_token")?.value) redirect("/login");
}
