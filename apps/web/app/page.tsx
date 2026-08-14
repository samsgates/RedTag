import Link from "next/link";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Plus, ShieldAlert } from "lucide-react";
import { Badge, toneForStatus } from "@/components/badge";
import { StatCard } from "@/components/stat-card";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function Home() {
  await ensureAuth();
  const [incidents, inventory, security] = await Promise.all([
    api.incidents().catch(() => []),
    api.inventory().catch(() => []),
    api.security().catch(() => [])
  ]);
  const active = incidents.filter(i => i.status !== "VERIFIED_CLOSED");
  const quarantined = inventory.filter(i => i.status === "QUARANTINED").reduce((a, b) => a + b.quantity, 0);
  const verification = incidents.length ? Math.round(incidents.reduce((a, b) => a + b.verification_coverage, 0) / incidents.length) : 0;

  return (
    <>
      <header className="topbar"><div><p className="eyebrow">AUTONOMOUS PRODUCT SAFETY</p><h1>Command Center</h1><p>Operational truth, policy-controlled action, independent verification.</p></div><div className="headerActions"><Link className="primaryButton" href="/incidents/new"><Plus size={15}/> New incident</Link><div className="topStatus"><span className="liveDot"/> Production controls active</div></div></header>
      <section className="statsGrid">
        <StatCard label="Active incidents" value={active.length} sub="Across current tenant"/>
        <StatCard label="Affected customers" value={incidents.reduce((a,b)=>a+b.affected_customers,0).toLocaleString()} sub="Current exposure"/>
        <StatCard label="Units quarantined" value={quarantined.toLocaleString()} sub="Authoritative inventory"/>
        <StatCard label="Verification" value={`${verification}%`} sub="Critical actions"/>
      </section>

      <section className="gridTwo">
        <div className="card panel">
          <div className="panelHead"><div><span className="eyebrow">INCIDENT OPERATIONS</span><h2>Active recalls</h2></div><AlertTriangle size={20}/></div>
          <div className="tableWrap"><table><thead><tr><th>Incident</th><th>Severity</th><th>Status</th><th>Exposure</th><th></th></tr></thead><tbody>
            {incidents.map(i => <tr key={i.id}><td><strong>{i.title}</strong><small>{i.id}</small></td><td><Badge tone={toneForStatus(i.severity)}>{i.severity}</Badge></td><td><Badge tone={toneForStatus(i.status)}>{i.status.replaceAll("_"," ")}</Badge></td><td>{i.affected_units.toLocaleString()} units</td><td><Link href={`/incidents/${i.id}`}><ArrowUpRight size={18}/></Link></td></tr>)}
            {!incidents.length && <tr><td colSpan={5}>Start the API and seed the demo dataset to populate this command center.</td></tr>}
          </tbody></table></div>
        </div>
        <div className="card panel securityPanel">
          <div className="panelHead"><div><span className="eyebrow">ZERO TRUST AGENTS</span><h2>Security controls</h2></div><ShieldAlert size={20}/></div>
          {security.slice(0,3).map(s => <div className="securityEvent" key={s.id}><div><Badge tone="danger">{s.decision}</Badge><strong>{s.category.replaceAll("_"," ")}</strong></div><p>Source: {s.source}</p><small>Untrusted instruction was denied before tool execution.</small></div>)}
          {!security.length && <div className="emptyState"><CheckCircle2/><p>No recent policy violations.</p></div>}
        </div>
      </section>

      <section className="card panel"><div className="panelHead"><div><span className="eyebrow">AUTHORITATIVE STATE</span><h2>Inventory control</h2></div></div>
        <div className="inventoryGrid">{inventory.map(row => <div className="inventoryItem" key={row.id}><div><strong>{row.product_id.replace("product_","").toUpperCase()}</strong><small>{row.warehouse}</small></div><div className="qty">{row.quantity}<small> units</small></div><Badge tone={toneForStatus(row.status)}>{row.status}</Badge></div>)}</div>
      </section>
    </>
  );
}
