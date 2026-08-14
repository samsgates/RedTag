"""Database tenant-context propagation for PostgreSQL Row-Level Security."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def bind_tenant(db: Session, tenant_id: str) -> None:
    """Bind a tenant to the SQLAlchemy session.

    PostgreSQL RLS policies read ``app.tenant_id``. The Session event in ``session.py`` reapplies
    this value at the beginning of every transaction, so commits inside a long-running request do
    not silently drop tenant enforcement.
    """

    if not tenant_id:
        raise ValueError("tenant_id is required")
    db.info["tenant_id"] = tenant_id
    if db.in_transaction() and db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": tenant_id})
