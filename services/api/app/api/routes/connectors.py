from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.connectors.inventory import InventoryConnector
from app.connectors.notification import NotificationConnector
from app.connectors.shipment import ShipmentConnector
from app.core.security import Principal, get_principal
from app.db.session import get_db

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("")
def connectors(db: Session = Depends(get_db), principal: Principal = Depends(get_principal)) -> list[dict]:
    instances = [
        InventoryConnector(db, principal.tenant_id),
        ShipmentConnector(db, principal.tenant_id),
        NotificationConnector(db, principal.tenant_id),
    ]
    return [{"name": c.name, **c.health()} for c in instances]
