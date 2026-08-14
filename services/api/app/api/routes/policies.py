from fastapi import APIRouter, Depends

from app.core.security import Principal, get_principal

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("")
def policies(principal: Principal = Depends(get_principal)) -> dict:
    return {
        "tenant_id": principal.tenant_id,
        "version": "builtin-1.0",
        "risk_classes": {
            "R0": "read-only",
            "R1": "low-risk reversible",
            "R2": "operational mutation",
            "R3": "high impact",
            "R4": "legal or financial sensitivity",
        },
        "prohibited": ["customer.bulk_export", "system.shell", "system.sql"],
    }
