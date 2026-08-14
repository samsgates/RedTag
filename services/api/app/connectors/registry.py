from sqlalchemy.orm import Session

from app.connectors.base import Connector
from app.connectors.inventory import InventoryConnector
from app.connectors.notification import NotificationConnector
from app.connectors.shipment import ShipmentConnector


def connector_for_action(db: Session, tenant_id: str, action_type: str) -> Connector:
    if action_type.startswith("inventory."):
        return InventoryConnector(db, tenant_id)
    if action_type.startswith("shipment."):
        return ShipmentConnector(db, tenant_id)
    if action_type.startswith("customer.notify_"):
        return NotificationConnector(db, tenant_id)
    raise ValueError(f"No registered connector for action: {action_type}")


def expected_state(action_type: str) -> dict:
    mapping = {
        "inventory.quarantine": {"status": "QUARANTINED"},
        "inventory.release": {"status": "AVAILABLE"},
        "shipment.hold": {"status": "HOLD_RECALL"},
        "shipment.release": {"status": "READY_TO_SHIP"},
        "customer.notify_email": {"status": "DELIVERED"},
        "customer.notify_sms": {"status": "DELIVERED"},
    }
    if action_type not in mapping:
        raise ValueError(f"No verification expectation for action: {action_type}")
    return mapping[action_type]
