from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Incident, ReturnCase
from app.services.audit import audit
from app.services.workflow import RecallWorkflow


def list_returns(db: Session, tenant_id: str, incident_id: str | None = None) -> list[ReturnCase]:
    stmt = select(ReturnCase).where(ReturnCase.tenant_id == tenant_id)
    if incident_id:
        stmt = stmt.where(ReturnCase.incident_id == incident_id)
    return list(db.scalars(stmt.order_by(ReturnCase.created_at.desc())))


def recover_return(
    db: Session,
    *,
    tenant_id: str,
    return_id: str,
    actor_id: str,
) -> ReturnCase:
    row = db.scalar(
        select(ReturnCase).where(ReturnCase.tenant_id == tenant_id, ReturnCase.id == return_id)
    )
    if not row:
        raise LookupError("Return case not found")
    if row.status != "RECOVERED":
        row.status = "RECOVERED"
        row.recovered_at = datetime.now(timezone.utc)
        audit(
            db,
            tenant_id=tenant_id,
            incident_id=row.incident_id,
            actor_type="user",
            actor_id=actor_id,
            event_type="return.recovered",
            payload={"return_id": row.id, "order_id": row.order_id},
        )
        db.commit()
    incident = db.get(Incident, row.incident_id)
    if incident:
        RecallWorkflow(db).refresh_verification_coverage(incident)
    return row
