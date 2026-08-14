# Threat Model

## Assets

Customer contact information, recall scope, inventory state, evidence, action receipts, approvals, agent credentials, connector credentials, and audit history.

## Primary threats

- Cross-tenant data access.
- Prompt injection inside supplier content.
- Tool capability escalation.
- Bulk PII exfiltration.
- Duplicate side effects caused by retries.
- Forged approval or agent identity.
- SSRF through generic connectors.
- Malicious uploads.
- Audit tampering.
- Model hallucination becoming operational truth.

## Controls

- Tenant-scoped queries plus enforced PostgreSQL RLS for business tables.
- Registered typed tools only.
- Risk-class policy engine.
- Prohibited capability list.
- Idempotency constraints.
- Append-only audit behavior from normal application paths.
- Hash-based evidence integrity.
- Independent verification readback.
- Secret Manager and service identities.
- Google Cloud Model Armor text/PDF/DOCX/XLSX screening when enabled plus deterministic local indirect prompt-injection rules.
- Minimal model context and PII minimization.

## Residual risk

RedTag assists product safety operations and does not replace legal or regulatory decision makers. Organizations must configure policies, connectors, retention, and approval thresholds to their regulatory environment.
