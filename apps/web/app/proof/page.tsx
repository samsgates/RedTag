import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Badge, toneForStatus } from "@/components/badge";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function ProofIndexPage() {
  await ensureAuth();
  const incidents = await api.incidents().catch(()=>[]);
  return <><header className="topbar"><div><p className="eyebrow">AUDITABLE AUTONOMY</p><h1>Recall Proof</h1><p>Open an incident to inspect the evidence, action, receipt, and verification chain.</p></div></header><section className="card panel">{incidents.map(i=><div className="proofIndexRow" key={i.id}><div><strong>{i.title}</strong><small>{i.id}</small></div><div className="coverageTrack"><span style={{width:`${Math.min(100,i.verification_coverage)}%`}}/></div><strong>{i.verification_coverage}%</strong><Badge tone={toneForStatus(i.status)}>{i.status.replaceAll("_"," ")}</Badge><Link href={`/incidents/${i.id}`}><ArrowUpRight size={18}/></Link></div>)}</section></>;
}
