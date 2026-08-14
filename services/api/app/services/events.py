from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.domain import OutboxEvent


def enqueue_event(
    db: Session,
    *,
    tenant_id: str,
    event_type: str,
    incident_id: str | None,
    payload: dict,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> OutboxEvent:
    event = OutboxEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        incident_id=incident_id,
        payload=payload,
        correlation_id=correlation_id or uuid4().hex,
        causation_id=causation_id,
    )
    db.add(event)
    return event
