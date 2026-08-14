from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import Connector, ConnectorResult
from app.models.domain import InventoryLot


class InventoryConnector(Connector):
    name = "inventory"

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _lot(self, target_id: str) -> InventoryLot | None:
        return self.db.scalar(
            select(InventoryLot).where(
                InventoryLot.tenant_id == self.tenant_id,
                InventoryLot.id == target_id,
            )
        )

    def health(self) -> dict:
        return {"status": "ok", "connector": self.name}

    def execute(self, action: str, target_id: str, payload: dict) -> ConnectorResult:
        lot = self._lot(target_id)
        if not lot:
            return ConnectorResult(False, None, None, None, "Inventory lot not found")
        before = {"status": lot.status, "quantity": lot.quantity, "version": lot.version}
        if action == "inventory.quarantine":
            lot.status = "QUARANTINED"
        elif action == "inventory.release":
            lot.status = "AVAILABLE"
        else:
            return ConnectorResult(False, None, before, None, f"Unsupported action: {action}")
        lot.version += 1
        self.db.flush()
        after = {"status": lot.status, "quantity": lot.quantity, "version": lot.version}
        return ConnectorResult(True, f"inventory:{lot.id}:v{lot.version}", before, after)

    def verify(self, action: str, target_id: str, expected: dict) -> dict:
        lot = self._lot(target_id)
        if not lot:
            return {"verified": False, "reason": "Inventory lot not found"}
        actual = {"status": lot.status, "quantity": lot.quantity, "version": lot.version}
        expected_status = expected.get("status")
        return {
            "verified": expected_status is None or lot.status == expected_status,
            "actual": actual,
            "expected": expected,
        }
