"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2 } from "lucide-react";
import { Badge } from "@/components/badge";

export function StrategyList({ incidentId, strategies }: { incidentId: string; strategies: any[] }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function approve(strategyId: string) {
    setBusy(strategyId);
    setError("");
    try {
      const response = await fetch(
        `/api/redtag/incidents/${incidentId}/approve-and-contain?strategy_id=${encodeURIComponent(strategyId)}`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error(await response.text());
      router.refresh();
    } catch (value) {
      setError(value instanceof Error ? value.message : "Approval failed");
    } finally {
      setBusy(null);
    }
  }

  if (!strategies.length) return <p className="mutedText">Run simulation to compare recall scopes.</p>;

  return (
    <>
      {strategies.map((strategy: any) => (
        <div className={strategy.recommended ? "strategy recommended" : "strategy"} key={strategy.id}>
          <div>
            <strong>{strategy.name}</strong>
            {strategy.recommended && <Badge tone="good">RECOMMENDED</Badge>}
          </div>
          <p>{strategy.rationale}</p>
          <div className="strategyMeta">
            <span>{Math.round(strategy.coverage * 1000) / 10}% coverage</span>
            <span>{strategy.affected_customers.toLocaleString()} customers</span>
            <span>${strategy.estimated_cost.toLocaleString()} est.</span>
          </div>
          <button className="strategyApprove" disabled={busy !== null} onClick={() => approve(strategy.id)}>
            {busy === strategy.id ? <Loader2 size={13} className="spin"/> : <CheckCircle2 size={13}/>} Approve this scope
          </button>
        </div>
      ))}
      {error && <p className="formError">{error}</p>}
    </>
  );
}
