from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Action, ActionStatus, Approval
from app.services.actions import execute_action, verify_action
from app.services.audit import audit


def list_approvals(db: Session, tenant_id: str) -> list[Approval]:
    return list(
        db.scalars(
            select(Approval)
            .where(Approval.tenant_id == tenant_id)
            .order_by(Approval.created_at.desc())
        )
    )


def decide_approval(
    db: Session,
    *,
    tenant_id: str,
    approval_id: str,
    user_id: str,
    approve: bool,
) -> Approval:
    row = db.scalar(
        select(Approval).where(Approval.tenant_id == tenant_id, Approval.id == approval_id)
    )
    if not row:
        raise LookupError("Approval not found")
    if row.status != "WAITING":
        return row
    row.status = "APPROVED" if approve else "REJECTED"
    row.decided_by = user_id
    row.decided_at = datetime.now(timezone.utc)
    action_id = row.payload.get("action_id")
    action = db.get(Action, action_id) if action_id else None
    if action and action.tenant_id == tenant_id:
        if approve:
            action.status = ActionStatus.PENDING.value
            action.policy_decision = {**action.policy_decision, "human_approval": row.id}
            execute_action(db, action)
            verify_action(db, action)
        else:
            action.status = ActionStatus.BLOCKED.value
            action.error = "Human approval rejected"
    audit(
        db,
        tenant_id=tenant_id,
        incident_id=row.incident_id,
        actor_type="user",
        actor_id=user_id,
        event_type="approval.decided",
        payload={"approval_id": row.id, "decision": row.status, "action_id": action_id},
    )
    db.commit()
    db.refresh(row)
    return row
