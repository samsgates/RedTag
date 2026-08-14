export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

export function toneForStatus(value: string) {
  if (["VERIFIED", "VERIFIED_CLOSED", "READY_TO_CLOSE", "SUCCEEDED", "QUARANTINED"].includes(value)) return "good";
  if (["HIGH", "CRITICAL", "FAILED", "BLOCKED", "SECURITY_HOLD"].includes(value)) return "danger";
  if (["AWAITING_APPROVAL", "VERIFYING", "CONTAINING", "MEDIUM"].includes(value)) return "warn";
  return "neutral";
}
