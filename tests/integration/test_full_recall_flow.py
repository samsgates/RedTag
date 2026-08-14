from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.domain import (
    Customer,
    InventoryLot,
    Notification,
    Order,
    Organization,
    ReturnCase,
    Shipment,
    SupplyNode,
)
from app.schemas.incidents import IncidentCreate
from app.services.customer_recall import CustomerRecallService
from app.services.incidents import create_incident
from app.services.returns import recover_return
from app.services.workflow import RecallWorkflow


def test_end_to_end_recall_with_delivery_recovery_and_returns():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        db.add(Organization(id="tenant_demo", name="Demo", autonomy_level=2))
        db.add_all(
            [
                SupplyNode(id="component_x91", tenant_id="tenant_demo", node_type="COMPONENT", label="X91 Connector", attrs={}),
                SupplyNode(id="b1", tenant_id="tenant_demo", node_type="MANUFACTURING_BATCH", label="BAT-8831", attrs={"affected": True}),
                SupplyNode(id="b2", tenant_id="tenant_demo", node_type="MANUFACTURING_BATCH", label="BAT-8832", attrs={"affected": True}),
                InventoryLot(id="lot1", tenant_id="tenant_demo", product_id="p1", manufacturing_batch_id="BAT-8831", warehouse="A", quantity=12, status="AVAILABLE"),
                Customer(id="c1", tenant_id="tenant_demo", external_ref="X1", first_name="One", email="one@example.test", phone="+15550000001"),
                Customer(id="c2", tenant_id="tenant_demo", external_ref="X2", first_name="Two", email="fail@example.test", phone="+15550000002"),
                Order(id="o1", tenant_id="tenant_demo", customer_id="c1", product_id="p1", manufacturing_batch_id="BAT-8831", status="READY_TO_SHIP"),
                Order(id="o2", tenant_id="tenant_demo", customer_id="c2", product_id="p1", manufacturing_batch_id="BAT-8831", status="FULFILLED"),
                Shipment(id="s1", tenant_id="tenant_demo", order_id="o1", status="READY_TO_SHIP"),
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
        assert incident.status == "NOTIFYING"
        assert db.get(Shipment, "s1").status == "HOLD_RECALL"

        CustomerRecallService(db).notify(incident)
        db.refresh(incident)
        assert incident.status == "RECOVERING"
        delivered_c2 = db.scalar(
            select(Notification).where(
                Notification.customer_id == "c2",
                Notification.channel == "sms",
                Notification.status == "DELIVERED",
            )
        )
        assert delivered_c2 is not None

        returns = list(db.scalars(select(ReturnCase)))
        assert len(returns) == 2
        for row in returns:
            recover_return(
                db,
                tenant_id="tenant_demo",
                return_id=row.id,
                actor_id="user1",
            )
        db.refresh(incident)
        assert incident.status == "READY_TO_CLOSE"
        workflow.close(incident)
        assert incident.status == "VERIFIED_CLOSED"
