export function StatCard({ label, value, sub }: { label: string; value: string | number; sub: string }) {
  return <div className="card stat"><span>{label}</span><strong>{value}</strong><small>{sub}</small></div>;
}
