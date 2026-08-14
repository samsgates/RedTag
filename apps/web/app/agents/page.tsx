import { Badge, toneForStatus } from "@/components/badge";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function AgentsPage() {
  await ensureAuth();
  const agents = await api.agents().catch(() => []);
  return <><header className="topbar"><div><p className="eyebrow">SPECIALIZED AUTONOMY</p><h1>Agent Fleet</h1><p>Narrow agents with scoped responsibilities and tool boundaries.</p></div></header><section className="agentGrid">{agents.map((agent:any)=><article className="card panel agentCard" key={agent.id}><div className="panelHead"><div><span className="eyebrow">{agent.id}</span><h2>{agent.name}</h2></div><Badge tone={toneForStatus(agent.status)}>{agent.status}</Badge></div><p className="mutedText">Model: {agent.model} · Version {agent.version}</p><h3>Capabilities</h3><div className="chipRow">{agent.capabilities.map((c:string)=><span className="chip" key={c}>{c}</span>)}</div><h3>Tools</h3><div className="chipRow">{agent.tools.length ? agent.tools.map((t:string)=><span className="chip" key={t}>{t}</span>) : <span className="mutedText">Reasoning only</span>}</div></article>)}</section></>;
}
