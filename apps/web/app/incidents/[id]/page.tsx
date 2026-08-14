import { Badge, toneForStatus } from "@/components/badge";
import { IncidentControls } from "@/components/incident-controls";
import { ReturnList } from "@/components/return-list";
import { StrategyList } from "@/components/strategy-list";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function IncidentPage({ params }: { params: Promise<{ id: string }> }) {
  await ensureAuth();
  const { id } = await params;
  const [incident, actions, strategies, timeline, proof, returns] = await Promise.all([
    api.incident(id),
    api.actions(id),
    api.strategies(id),
    api.timeline(id),
    api.proof(id),
    api.returns(id),
  ]);

  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">INCIDENT {incident.id}</p>
          <h1>{incident.title}</h1>
          <p>{incident.description}</p>
        </div>
        <Badge tone={toneForStatus(incident.status)}>{incident.status.replaceAll("_", " ")}</Badge>
      </header>

      <IncidentControls incidentId={incident.id} />

      <section className="statsGrid">
        <div className="card stat"><span>Severity</span><strong>{incident.severity}</strong><small>Current classification</small></div>
        <div className="card stat"><span>Affected units</span><strong>{incident.affected_units}</strong><small>Traced inventory</small></div>
        <div className="card stat"><span>Customers</span><strong>{incident.affected_customers.toLocaleString()}</strong><small>Potential exposure</small></div>
        <div className="card stat"><span>Proof coverage</span><strong>{incident.verification_coverage}%</strong><small>Independent readback</small></div>
      </section>

      <section className="gridTwo">
        <div className="card panel">
          <span className="eyebrow">COUNTERFACTUAL RECALL</span>
          <h2>Strategies</h2>
          <StrategyList incidentId={incident.id} strategies={strategies} />
        </div>

        <div className="card panel">
          <span className="eyebrow">RECALL PROOF GRAPH</span>
          <h2>Verified operational chain</h2>
          {!proof.nodes.length && <p className="mutedText">Proof nodes appear as agents create evidence-backed findings and verified actions.</p>}
          <div className="proofList">
            {proof.nodes.map((node: any, idx: number) => (
              <div className="proofNode" key={node.id}>
                <span>{idx + 1}</span>
                <div><strong>{node.type}</strong><p>{node.label}</p></div>
                <Badge tone={toneForStatus(node.status)}>{node.status}</Badge>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="gridTwo">
        <div className="card panel">
          <span className="eyebrow">PRODUCT RECOVERY</span>
          <h2>Return cases</h2>
          <ReturnList rows={returns} />
        </div>
        <div className="card panel">
          <span className="eyebrow">ACTION RECEIPTS</span>
          <h2>Agent actions</h2>
          {!actions.length && <p className="mutedText">State-changing actions will appear here after containment begins.</p>}
          {actions.map((action: any) => (
            <div className="actionRow" key={action.id}>
              <div><strong>{action.action_type}</strong><small>{action.target_id}</small></div>
              <Badge tone={toneForStatus(action.status)}>{action.status}</Badge>
              <span>{action.risk_class}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="card panel">
        <span className="eyebrow">AUDIT TIMELINE</span>
        <h2>Observable execution</h2>
        {!timeline.length && <p className="mutedText">Audit events will appear as the workflow progresses.</p>}
        {timeline.map((item: any) => (
          <div className="timelineItem" key={item.id}>
            <span className="timelineDot" />
            <div>
              <strong>{item.event_type}</strong>
              <p>{item.actor_id}</p>
              <small>{new Date(item.created_at).toLocaleString()}</small>
            </div>
          </div>
        ))}
      </section>
    </>
  );
}
