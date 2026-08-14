"""Cross-process advisory locks for incident workflow serialization."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


def _lock_key(tenant_id: str, incident_id: str) -> int:
    """Return a stable signed 64-bit PostgreSQL advisory-lock key."""

    digest = hashlib.sha256(f"{tenant_id}|{incident_id}".encode()).digest()[:8]
    unsigned = int.from_bytes(digest, byteorder="big", signed=False)
    return unsigned - (1 << 64) if unsigned >= (1 << 63) else unsigned


@contextmanager
def incident_advisory_lock(
    db: Session,
    tenant_id: str,
    incident_id: str,
) -> Iterator[bool]:
    """Serialize long-running workflow changes for one incident.

    A dedicated PostgreSQL connection holds the session-level advisory lock. RedTag workflows commit
    between phases, so keeping the lock on a separate open connection is required. Holding it on the
    ORM Session connection would be unsafe because that connection may return to the pool on commit.

    Non-PostgreSQL test/local databases use a no-op lock.
    """

    bind = db.get_bind()
    if bind.dialect.name != "postgresql":
        yield True
        return

    key = _lock_key(tenant_id, incident_id)
    with bind.connect() as lock_connection:
        acquired = bool(
            lock_connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
            ).scalar_one()
        )
        try:
            yield acquired
        finally:
            if acquired:
                lock_connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
