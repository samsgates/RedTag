from sqlalchemy.orm import Session

from app.models.domain import AuditEvent


def audit(
    db: Session,
    *,
    tenant_id: str,
    actor_type: str,
    actor_id: str,
    event_type: str,
    payload: dict,
    incident_id: str | None = None,
) -> AuditEvent:
    row = AuditEvent(
        tenant_id=tenant_id,
        incident_id=incident_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(row)
    return row
