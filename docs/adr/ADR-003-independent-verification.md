# ADR-003: Verification is independent from execution

**Status:** Accepted

The executor cannot be the sole authority for success. Verification performs an authoritative readback after action execution. Critical actions block closure until verified.
