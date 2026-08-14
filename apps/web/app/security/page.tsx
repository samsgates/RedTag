import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/badge";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function SecurityPage() {
  await ensureAuth();
  const events = await api.security().catch(() => []);
  return <><header className="topbar"><div><p className="eyebrow">ZERO TRUST CONTROLS</p><h1>Security</h1><p>Denied instructions, policy blocks, and unsafe capability attempts remain auditable.</p></div><ShieldCheck size={24}/></header><section className="card panel"><div className="tableWrap"><table><thead><tr><th>Decision</th><th>Category</th><th>Severity</th><th>Source</th><th>Attempted action</th><th>Time</th></tr></thead><tbody>{events.map((event:any)=><tr key={event.id}><td><Badge tone="danger">{event.decision}</Badge></td><td>{event.category}</td><td>{event.severity}</td><td>{event.source}</td><td>{event.attempted_action || "Policy instruction"}</td><td>{new Date(event.created_at).toLocaleString()}</td></tr>)}{!events.length && <tr><td colSpan={6}>No recorded security events.</td></tr>}</tbody></table></div></section></>;
}
