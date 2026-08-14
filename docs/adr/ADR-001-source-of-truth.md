# ADR-001: PostgreSQL is operational source of truth

**Status:** Accepted

LLM memory and agent sessions are not authoritative for inventory, customer, shipment, approval, action, or verification state. PostgreSQL provides transactions, constraints, durable history, and deterministic readback.
