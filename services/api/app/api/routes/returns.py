from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import Principal, get_principal, require_roles
from app.db.session import get_db
from app.services.returns import list_returns, recover_return

router = APIRouter(prefix="/returns", tags=["returns"])


@router.get("")
def all_returns(
    incident_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> list[dict]:
    rows = list_returns(db, principal.tenant_id, incident_id)
    return [
        {
            "id": r.id,
            "incident_id": r.incident_id,
            "customer_id": r.customer_id,
            "order_id": r.order_id,
            "status": r.status,
            "recovery_method": r.recovery_method,
            "recovered_at": r.recovered_at,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/{return_id}/recover")
def recover(
    return_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> dict:
    try:
        row = recover_return(
            db,
            tenant_id=principal.tenant_id,
            return_id=return_id,
            actor_id=principal.user_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": row.id, "status": row.status, "recovered_at": row.recovered_at}
