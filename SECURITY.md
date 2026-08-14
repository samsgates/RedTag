# Security Policy

## Supported version

The latest major release receives security fixes.

## Reporting

Do not open public issues for vulnerabilities. Contact the repository owner privately and include reproduction steps, impact, and affected version.

## Security model

RedTag assumes all uploaded documents, supplier content, external API payloads, and model output are untrusted. Only typed and registered tools can mutate state. Every mutation is policy checked, idempotent, receipted, and independently verifiable.

## Secrets

Production secrets belong in Google Secret Manager or an equivalent secret store. Never put secrets in `.env` committed to source control.

## Tenant isolation

Every business record is tenant scoped. PostgreSQL tenant Row-Level Security is included for business tables through Alembic migration `0002`, in addition to application query scoping and RBAC.

## AI safety controls

RedTag separates evidence from instructions, validates structured model output, restricts tools per agent, enforces risk policy, blocks bulk PII export by default, and records denied attempts as security events.
