from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Incident, IncidentStatus
from app.schemas.incidents import IncidentCreate
from app.services.audit import audit
from app.services.events import enqueue_event


def create_incident(db: Session, tenant_id: str, user_id: str, data: IncidentCreate) -> Incident:
    incident = Incident(
        tenant_id=tenant_id,
        created_by=user_id,
        title=data.title,
        description=data.description,
        severity=data.severity,
        product_hint=data.product_hint,
    )
    db.add(incident)
    db.flush()
    audit(
        db,
        tenant_id=tenant_id,
        incident_id=incident.id,
        actor_type="user",
        actor_id=user_id,
        event_type="incident.created",
        payload={"title": incident.title, "severity": incident.severity},
    )
    enqueue_event(
        db,
        tenant_id=tenant_id,
        event_type="incident.created",
        incident_id=incident.id,
        payload={"incident_id": incident.id},
    )
    db.commit()
    db.refresh(incident)
    return incident


def get_incident(db: Session, tenant_id: str, incident_id: str) -> Incident | None:
    return db.scalar(select(Incident).where(Incident.tenant_id == tenant_id, Incident.id == incident_id))


def list_incidents(db: Session, tenant_id: str) -> list[Incident]:
    return list(
        db.scalars(
            select(Incident).where(Incident.tenant_id == tenant_id).order_by(Incident.created_at.desc())
        )
    )


def transition(incident: Incident, new_status: IncidentStatus) -> None:
    allowed: dict[str, set[str]] = {
        IncidentStatus.NEW.value: {IncidentStatus.TRIAGING.value, IncidentStatus.PAUSED.value},
        IncidentStatus.TRIAGING.value: {IncidentStatus.INVESTIGATING.value, IncidentStatus.FAILED.value},
        IncidentStatus.INVESTIGATING.value: {IncidentStatus.SCOPE_PROPOSED.value, IncidentStatus.FAILED.value},
        IncidentStatus.SCOPE_PROPOSED.value: {IncidentStatus.AWAITING_APPROVAL.value, IncidentStatus.CONTAINING.value},
        IncidentStatus.AWAITING_APPROVAL.value: {IncidentStatus.CONTAINING.value, IncidentStatus.PAUSED.value},
        IncidentStatus.CONTAINING.value: {IncidentStatus.NOTIFYING.value, IncidentStatus.VERIFYING.value},
        IncidentStatus.NOTIFYING.value: {IncidentStatus.RECOVERING.value, IncidentStatus.VERIFYING.value},
        IncidentStatus.RECOVERING.value: {IncidentStatus.VERIFYING.value},
        IncidentStatus.VERIFYING.value: {IncidentStatus.READY_TO_CLOSE.value, IncidentStatus.EXCEPTIONS_OPEN.value},
        IncidentStatus.READY_TO_CLOSE.value: {IncidentStatus.VERIFIED_CLOSED.value},
        IncidentStatus.EXCEPTIONS_OPEN.value: {IncidentStatus.VERIFYING.value, IncidentStatus.PAUSED.value},
    }
    if new_status.value not in allowed.get(incident.status, set()):
        raise ValueError(f"Invalid incident transition: {incident.status} -> {new_status.value}")
    incident.status = new_status.value
