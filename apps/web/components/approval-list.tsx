"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge, toneForStatus } from "@/components/badge";

const API = "/api/redtag";

export function ApprovalList({ rows }: { rows: any[] }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);

  async function decide(id: string, decision: "approve" | "reject") {
    setBusy(id);
    try {
      const response = await fetch(`${API}/approvals/${id}/${decision}`, { method: "POST" });
      if (!response.ok) throw new Error(await response.text());
      router.refresh();
    } finally { setBusy(null); }
  }

  if (!rows.length) return <p className="mutedText">No approval requests are waiting.</p>;
  return <div className="tableWrap"><table><thead><tr><th>Action</th><th>Risk</th><th>Status</th><th>Requested</th><th></th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td><strong>{row.action_type}</strong><small>{row.payload?.target_id || row.payload?.action_id || row.incident_id}</small></td><td>{row.risk_class}</td><td><Badge tone={toneForStatus(row.status)}>{row.status}</Badge></td><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.status === "WAITING" && <div className="inlineButtons"><button className="tinyButton" disabled={busy===row.id} onClick={()=>decide(row.id,"approve")}>Approve</button><button className="tinyButton dangerButton" disabled={busy===row.id} onClick={()=>decide(row.id,"reject")}>Reject</button></div>}</td></tr>)}</tbody></table></div>;
}
