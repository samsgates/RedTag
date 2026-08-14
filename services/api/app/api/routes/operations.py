from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import Principal, get_principal
from app.db.session import get_db
from app.models.domain import Customer, InventoryLot, Notification, Organization, Shipment

router = APIRouter(tags=["operations"])


@router.get("/inventory")
def inventory(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> list[dict]:
    rows = list(db.scalars(select(InventoryLot).where(InventoryLot.tenant_id == principal.tenant_id)))
    return [
        {
            "id": r.id,
            "product_id": r.product_id,
            "manufacturing_batch_id": r.manufacturing_batch_id,
            "warehouse": r.warehouse,
            "quantity": r.quantity,
            "status": r.status,
            "version": r.version,
        }
        for r in rows
    ]


@router.get("/organization")
def organization(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> dict:
    org = db.get(Organization, principal.tenant_id)
    return {"id": org.id, "name": org.name, "autonomy_level": org.autonomy_level} if org else {}


@router.get("/shipments")
def shipments(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> list[dict]:
    rows = list(db.scalars(select(Shipment).where(Shipment.tenant_id == principal.tenant_id)))
    return [{"id": r.id, "order_id": r.order_id, "carrier": r.carrier, "tracking_ref": r.tracking_ref, "status": r.status, "version": r.version} for r in rows]


@router.get("/customers")
def customers(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> list[dict]:
    rows = list(db.scalars(select(Customer).where(Customer.tenant_id == principal.tenant_id).limit(200)))
    return [{"id": r.id, "external_ref": r.external_ref, "first_name": r.first_name, "region": r.region, "contact_allowed": r.contact_allowed} for r in rows]


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> list[dict]:
    rows = list(db.scalars(select(Notification).where(Notification.tenant_id == principal.tenant_id).order_by(Notification.created_at.desc()).limit(500)))
    return [{"id": r.id, "incident_id": r.incident_id, "customer_id": r.customer_id, "channel": r.channel, "status": r.status, "attempt_count": r.attempt_count, "provider_ref": r.provider_ref, "error": r.error} for r in rows]
