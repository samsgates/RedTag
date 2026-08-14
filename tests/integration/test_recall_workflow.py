from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.domain import InventoryLot, Organization, SupplyNode
from app.schemas.incidents import IncidentCreate
from app.services.incidents import create_incident
from app.services.workflow import RecallWorkflow


def test_recall_closes_only_after_verified_containment():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        db.add(Organization(id="tenant_demo", name="Demo", autonomy_level=2))
        db.add_all(
            [
                SupplyNode(id="component_x91", tenant_id="tenant_demo", node_type="COMPONENT", label="X91 Connector", attrs={}),
                SupplyNode(id="b1", tenant_id="tenant_demo", node_type="MANUFACTURING_BATCH", label="BAT-8831", attrs={"affected": True}),
                SupplyNode(id="b2", tenant_id="tenant_demo", node_type="MANUFACTURING_BATCH", label="BAT-8832", attrs={"affected": True}),
                InventoryLot(id="lot1", tenant_id="tenant_demo", product_id="p1", manufacturing_batch_id="BAT-8831", warehouse="A", quantity=412, status="AVAILABLE"),
                InventoryLot(id="lot2", tenant_id="tenant_demo", product_id="p2", manufacturing_batch_id="BAT-8832", warehouse="B", quantity=188, status="AVAILABLE"),
            ]
        )
        db.commit()
        incident = create_incident(
            db,
            "tenant_demo",
            "user1",
            IncidentCreate(title="X91 thermal event", description="field report", severity="HIGH"),
        )
        workflow = RecallWorkflow(db)
        workflow.triage(incident)
        workflow.trace(incident)
        workflow.simulate(incident)
        workflow.approve_and_contain(incident)
        db.refresh(incident)
        assert incident.verification_coverage == 100.0
        workflow.close(incident)
        db.refresh(incident)
        assert incident.status == "VERIFIED_CLOSED"
        assert db.get(InventoryLot, "lot1").status == "QUARANTINED"
