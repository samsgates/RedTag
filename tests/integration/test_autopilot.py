from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.domain import InventoryLot, Organization, SupplyNode
from app.schemas.incidents import IncidentCreate
from app.services.autopilot import AutopilotRunner
from app.services.incidents import create_incident
from app.services.workflow import RecallWorkflow


def test_autopilot_advances_to_human_scope_gate_and_resumes_after_approval():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        db.add(Organization(id="tenant_demo", name="Demo", autonomy_level=2))
        db.add_all(
            [
                SupplyNode(id="component_x91", tenant_id="tenant_demo", node_type="COMPONENT", label="X91 Connector", attrs={}),
                SupplyNode(id="b1", tenant_id="tenant_demo", node_type="MANUFACTURING_BATCH", label="BAT-8831", attrs={"affected": True}),
                SupplyNode(id="b2", tenant_id="tenant_demo", node_type="MANUFACTURING_BATCH", label="BAT-8832", attrs={"affected": True}),
                InventoryLot(id="lot1", tenant_id="tenant_demo", product_id="p1", manufacturing_batch_id="BAT-8831", warehouse="A", quantity=20, status="AVAILABLE"),
                InventoryLot(id="lot2", tenant_id="tenant_demo", product_id="p2", manufacturing_batch_id="BAT-8832", warehouse="B", quantity=10, status="AVAILABLE"),
            ]
        )
        db.commit()
        incident = create_incident(
            db,
            "tenant_demo",
            "user1",
            IncidentCreate(title="X91 thermal event", description="field report", severity="HIGH"),
        )

        result = AutopilotRunner(db).run(incident)
        assert result.phases == ("triage", "trace", "simulate")
        assert result.waiting_for == "recall_scope_approval"
        assert incident.status == "AWAITING_APPROVAL"

        RecallWorkflow(db).approve_and_contain(incident)
        resumed = AutopilotRunner(db).run(incident)
        assert resumed.waiting_for == "authorized_closure"
        assert incident.status == "READY_TO_CLOSE"
