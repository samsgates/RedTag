# ADR-004: Domain events use a transactional outbox

**Status:** Accepted

A database mutation and event intent are committed together. A worker publishes committed outbox rows to Pub/Sub. Consumers are idempotent. This prevents lost events between database commit and broker publish.
