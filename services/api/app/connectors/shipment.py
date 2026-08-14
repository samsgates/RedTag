from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import Connector, ConnectorResult
from app.models.domain import Shipment


class ShipmentConnector(Connector):
    name = "shipment"

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _shipment(self, target_id: str) -> Shipment | None:
        return self.db.scalar(
            select(Shipment).where(
                Shipment.tenant_id == self.tenant_id,
                Shipment.id == target_id,
            )
        )

    def health(self) -> dict:
        return {"status": "ok", "connector": self.name}

    def execute(self, action: str, target_id: str, payload: dict) -> ConnectorResult:
        shipment = self._shipment(target_id)
        if not shipment:
            return ConnectorResult(False, None, None, None, "Shipment not found")
        before = {"status": shipment.status, "version": shipment.version}
        if action == "shipment.hold":
            if shipment.status in {"DELIVERED", "CANCELLED"}:
                return ConnectorResult(False, None, before, None, f"Shipment is already {shipment.status}")
            shipment.status = "HOLD_RECALL"
        elif action == "shipment.release":
            if shipment.status == "HOLD_RECALL":
                shipment.status = "READY_TO_SHIP"
        else:
            return ConnectorResult(False, None, before, None, f"Unsupported action: {action}")
        shipment.version += 1
        self.db.flush()
        after = {"status": shipment.status, "version": shipment.version}
        return ConnectorResult(True, f"shipment:{shipment.id}:v{shipment.version}", before, after)

    def verify(self, action: str, target_id: str, expected: dict) -> dict:
        shipment = self._shipment(target_id)
        if not shipment:
            return {"verified": False, "reason": "Shipment not found"}
        actual = {"status": shipment.status, "version": shipment.version}
        expected_status = expected.get("status")
        return {
            "verified": expected_status is None or shipment.status == expected_status,
            "actual": actual,
            "expected": expected,
        }
