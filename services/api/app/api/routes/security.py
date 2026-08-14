from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import Principal, get_principal
from app.db.session import get_db
from app.models.domain import SecurityEvent

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/events")
def events(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> list[dict]:
    rows = list(
        db.scalars(
            select(SecurityEvent)
            .where(SecurityEvent.tenant_id == principal.tenant_id)
            .order_by(SecurityEvent.created_at.desc())
            .limit(100)
        )
    )
    return [
        {
            "id": r.id,
            "incident_id": r.incident_id,
            "category": r.category,
            "severity": r.severity,
            "source": r.source,
            "attempted_action": r.attempted_action,
            "decision": r.decision,
            "details": r.details,
            "created_at": r.created_at,
        }
        for r in rows
    ]
