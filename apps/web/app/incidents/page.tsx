import Link from "next/link";
import { ArrowUpRight, Plus } from "lucide-react";
import { Badge, toneForStatus } from "@/components/badge";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function IncidentsPage() {
  await ensureAuth();
  const incidents = await api.incidents().catch(() => []);
  return <>
    <header className="topbar"><div><p className="eyebrow">SAFETY OPERATIONS</p><h1>Incidents</h1><p>Investigate, contain, recover, and verify every product-safety event.</p></div><Link className="primaryButton" href="/incidents/new"><Plus size={15}/> New incident</Link></header>
    <section className="card panel"><div className="tableWrap"><table><thead><tr><th>Incident</th><th>Severity</th><th>Status</th><th>Affected units</th><th>Customers</th><th>Proof</th><th></th></tr></thead><tbody>
      {incidents.map(i => <tr key={i.id}><td><strong>{i.title}</strong><small>{i.id}</small></td><td><Badge tone={toneForStatus(i.severity)}>{i.severity}</Badge></td><td><Badge tone={toneForStatus(i.status)}>{i.status.replaceAll("_", " ")}</Badge></td><td>{i.affected_units.toLocaleString()}</td><td>{i.affected_customers.toLocaleString()}</td><td>{i.verification_coverage}%</td><td><Link href={`/incidents/${i.id}`}><ArrowUpRight size={18}/></Link></td></tr>)}
      {!incidents.length && <tr><td colSpan={7}>No incidents yet. Create the first incident or seed the demo dataset.</td></tr>}
    </tbody></table></div></section>
  </>;
}
