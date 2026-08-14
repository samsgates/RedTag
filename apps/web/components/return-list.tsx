"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge, toneForStatus } from "@/components/badge";

const API = "/api/redtag";

export function ReturnList({ rows }: { rows: any[] }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  async function recover(id: string) {
    setBusy(id);
    try {
      const response = await fetch(`${API}/returns/${id}/recover`, { method: "POST" });
      if (!response.ok) throw new Error(await response.text());
      router.refresh();
    } finally { setBusy(null); }
  }
  if (!rows.length) return <p className="mutedText">Return cases appear after customer notification succeeds.</p>;
  return <div>{rows.map(row => <div className="actionRow" key={row.id}><div><strong>{row.order_id}</strong><small>{row.customer_id}</small></div><Badge tone={toneForStatus(row.status)}>{row.status}</Badge>{row.status !== "RECOVERED" ? <button className="tinyButton" disabled={busy===row.id} onClick={()=>recover(row.id)}>Recover</button> : <span>✓</span>}</div>)}</div>;
}
