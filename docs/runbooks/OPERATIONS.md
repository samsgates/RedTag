# Operations Runbook

## Database outage

1. Stop mutation workflows if Cloud SQL is unavailable.
2. Keep stateless health endpoints reporting degraded state.
3. Confirm Cloud SQL status and regional health.
4. Restore connectivity or fail over according to organization policy.
5. Do not replay external actions until idempotency state is readable.

## Pub/Sub backlog

Inspect oldest unacked message age and subscription delivery errors. Scale worker consumers, fix poison messages, and use a dead-letter topic for permanently failing events. Do not delete a backlog without recording the operational decision.

## Gemini unavailable

Pause model-dependent planning. Deterministic operational reads and existing approved actions can continue if policy permits. Never replace missing model output with fabricated values.

## Connector unavailable

Open circuit breaker after configured threshold, record exception, queue retry with jittered exponential backoff, and surface degraded connector in the command center.

## Verification failure

Do not close the incident. Create an exception, compare expected and actual state, and either retry a safe mutation, compensate, or require human review.

## Agent loop

Terminate execution after configured step, tool-call, time, token, or cost budget. Emit `AGENT_STALLED`, preserve state, and request a re-plan or human intervention.

## Secret rotation

Create new secret version, update service reference, deploy, verify health, then disable the previous version after overlap period.
