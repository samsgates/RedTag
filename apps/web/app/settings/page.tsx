import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function SettingsPage() {
  await ensureAuth();
  const [policies, connectors] = await Promise.all([api.policies().catch(()=>null), api.connectors().catch(()=>[])]);
  return <><header className="topbar"><div><p className="eyebrow">GOVERNANCE</p><h1>Settings</h1><p>Review policy boundaries and the health of registered operational connectors.</p></div></header><section className="gridTwo"><div className="card panel"><span className="eyebrow">POLICY</span><h2>{policies?.version || "Unavailable"}</h2><p className="mutedText">Prohibited capabilities</p><div className="chipRow">{policies?.prohibited?.map((p:string)=><span className="chip dangerChip" key={p}>{p}</span>)}</div></div><div className="card panel"><span className="eyebrow">CONNECTORS</span><h2>Runtime health</h2>{connectors.map((c:any)=><div className="actionRow" key={c.name}><div><strong>{c.name}</strong><small>Typed enterprise connector</small></div><span>{c.status || "UNKNOWN"}</span><span>{c.ok === false ? "!" : "✓"}</span></div>)}</div></section></>;
}
