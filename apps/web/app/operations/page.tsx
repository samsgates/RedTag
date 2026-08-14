import { Badge, toneForStatus } from "@/components/badge";
import { api } from "@/lib/api";
import { ensureAuth } from "@/lib/session";

export default async function OperationsPage() {
  await ensureAuth();
  const [inventory, shipments, notifications] = await Promise.all([api.inventory().catch(()=>[]), api.shipments().catch(()=>[]), api.notifications().catch(()=>[])]);
  return <><header className="topbar"><div><p className="eyebrow">AUTHORITATIVE READBACK</p><h1>Operations</h1><p>Inventory, shipment, and customer-notification state used for independent verification.</p></div></header>
    <section className="card panel"><span className="eyebrow">INVENTORY</span><h2>Lots</h2><div className="tableWrap"><table><thead><tr><th>Lot</th><th>Product</th><th>Batch</th><th>Warehouse</th><th>Qty</th><th>Status</th></tr></thead><tbody>{inventory.map((row:any)=><tr key={row.id}><td>{row.id}</td><td>{row.product_id}</td><td>{row.manufacturing_batch_id}</td><td>{row.warehouse}</td><td>{row.quantity}</td><td><Badge tone={toneForStatus(row.status)}>{row.status}</Badge></td></tr>)}</tbody></table></div></section>
    <section className="gridTwo"><div className="card panel"><span className="eyebrow">SHIPMENTS</span><h2>Outbound state</h2>{shipments.map((row:any)=><div className="actionRow" key={row.id}><div><strong>{row.id}</strong><small>{row.carrier} · {row.tracking_ref}</small></div><Badge tone={toneForStatus(row.status)}>{row.status}</Badge><span>{row.version}</span></div>)}</div><div className="card panel"><span className="eyebrow">NOTIFICATIONS</span><h2>Delivery state</h2>{notifications.map((row:any)=><div className="actionRow" key={row.id}><div><strong>{row.customer_id}</strong><small>{row.channel} · attempt {row.attempt_count}</small></div><Badge tone={toneForStatus(row.status)}>{row.status}</Badge><span>{row.error ? "!" : "✓"}</span></div>)}</div></section>
  </>;
}
