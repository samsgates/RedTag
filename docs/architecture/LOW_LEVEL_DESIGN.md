# RedTag Low-Level Design

## Request and identity path

1. A request reaches the Next.js same-origin BFF or FastAPI directly.
2. Browser mutations are rejected when cross-site request metadata indicates a foreign origin.
3. FastAPI validates the bearer token using configured issuer, audience, and JWKS.
4. The token subject/email is resolved to a provisioned RedTag user and active tenant membership.
5. The authenticated tenant is bound to the SQLAlchemy Session.
6. PostgreSQL transactions receive `set_config('app.tenant_id', tenant, true)` through a Session `after_begin` hook.
7. RBAC verifies the route capability.
8. Domain services additionally include tenant predicates in every business query.

## Incident lifecycle

`NEW -> TRIAGING -> INVESTIGATING -> SCOPE_PROPOSED -> AWAITING_APPROVAL -> CONTAINING -> NOTIFYING -> RECOVERING/VERIFYING -> READY_TO_CLOSE -> VERIFIED_CLOSED`

Additional states include paused, security-held, failed, reopened, and exception states.

## Recall Director autopilot

`AutopilotRunner` reads only persisted incident state. It does not store progress in model memory.

- `NEW`: triage evidence.
- `INVESTIGATING`: trace authoritative supply genealogy.
- `SCOPE_PROPOSED`: create data-backed strategies.
- `AWAITING_APPROVAL`: stop and wait.
- `NOTIFYING`: send approved notifications and perform configured fallback recovery.
- `RECOVERING`: stop for physical-world return events.
- `VERIFYING`: recalculate independent proof coverage.
- `READY_TO_CLOSE`: stop for authorized closure.

The runner has a hard maximum number of phases per cycle to prevent loops.

## Durable workflow delivery

1. API writes an `OutboxEvent` in the operational transaction.
2. The outbox publisher claims rows using `FOR UPDATE SKIP LOCKED`.
3. Pub/Sub receives the domain event.
4. The worker subscriber acknowledges irrelevant events and handles autopilot command events.
5. The worker binds the event tenant to the database session before reading business data.
6. `AutopilotRunner` resumes from persisted status.
7. On failure the message is nacked and may be redelivered.
8. Redelivery is safe because action requests use deterministic idempotency keys.

`outbox_events` is intentionally not protected by tenant RLS because it is consumed by a cross-tenant internal system worker. It is not exposed through the public API. Business tables remain protected by RLS.

## Action protocol

1. Agent or domain service creates a typed action request.
2. Idempotency key is generated from tenant, incident, action, target, and action version.
3. Deterministic policy returns ALLOW, REQUIRE_APPROVAL, or DENY.
4. Connector executes only an allowed capability.
5. Connector returns before state, after state, and external reference.
6. RedTag writes an `ActionReceipt`.
7. A separate verification path re-reads authoritative target state.
8. `Verification` and proof nodes are persisted.
9. Incident verification coverage is recalculated.

## Counterfactual strategy engine

Simulation consumes the latest provenance-backed TRACE proof node rather than demo constants. It calculates focused, traced-batch, and expanded-product scopes from tenant genealogy and inventory. Cost output is explicitly marked as a model assumption based on configurable deterministic unit/customer coefficients. It is not an accounting or legal determination.

## Evidence path

1. Upload allowlist validates MIME type and blocks active/executable extensions.
2. Basic magic signatures are checked for PDF, PNG, and JPEG.
3. Bytes are SHA-256 hashed.
4. Local mode stores under `.redtag/evidence`; cloud mode writes to Cloud Storage.
5. Text receives deterministic indirect prompt-injection screening.
6. When enabled, text/PDF/DOCX/XLSX is also screened by Google Cloud Model Armor.
7. Gemini receives an evidence manifest plus supported multimodal parts, with explicit instruction that attachments are untrusted data.
8. Extracted claims persist provenance back to evidence IDs.

## AI integration

`GeminiStructuredClient` uses the Google Gen AI SDK and Pydantic response schemas. Raw natural-language model output cannot directly trigger arbitrary mutations.

The deployable ADK application under `services/agent_runtime/app/agent.py` is a `SequentialAgent` consisting of Incident, Trace, and Risk agents. It deliberately exposes no state-changing tools. Operational mutations remain in the policy-controlled control plane.

## Multi-tenancy

Application query scoping and PostgreSQL RLS are both enabled. Identity bootstrap tables are outside tenant RLS because membership must be checked before tenant context can be trusted. The business application session reapplies RLS context after every transaction boundary.

## Failure model

- Duplicate API/action request: idempotency returns the existing action.
- Duplicate Pub/Sub command: state machine resumes from current state and side effects remain idempotent.
- Connector failure: action remains FAILED with audit history.
- Notification email failure: approved alternate SMS route is attempted when available.
- Verification mismatch: receipt remains unverified and closure is blocked.
- Model schema failure: no operational action is produced.
- Model Armor unavailable with fail-closed enabled: blocking security event is recorded.
- Worker restart: outbox and incident state remain persisted.
