import { ApprovalList } from "@/components/approval-list";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function ApprovalsPage() {
  await ensureAuth();
  const approvals = await api.approvals().catch(() => []);
  return <><header className="topbar"><div><p className="eyebrow">HUMAN AUTHORIZATION</p><h1>Approvals</h1><p>High-impact actions wait here when policy requires explicit human authorization.</p></div></header><section className="card panel"><ApprovalList rows={approvals}/></section></>;
}
