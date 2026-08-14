from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import Principal, get_principal, require_roles
from app.db.session import get_db
from app.models.domain import Approval
from app.schemas.incidents import ApprovalRead
from app.services.approvals import decide_approval, list_approvals

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
def all_approvals(
    db: Session = Depends(get_db), principal: Principal = Depends(get_principal)
) -> list[Approval]:
    return list_approvals(db, principal.tenant_id)


@router.post("/{approval_id}/approve", response_model=ApprovalRead)
def approve(
    approval_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Approver")),
) -> Approval:
    try:
        return decide_approval(
            db,
            tenant_id=principal.tenant_id,
            approval_id=approval_id,
            user_id=principal.user_id,
            approve=True,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{approval_id}/reject", response_model=ApprovalRead)
def reject(
    approval_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Approver")),
) -> Approval:
    try:
        return decide_approval(
            db,
            tenant_id=principal.tenant_id,
            approval_id=approval_id,
            user_id=principal.user_id,
            approve=False,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
