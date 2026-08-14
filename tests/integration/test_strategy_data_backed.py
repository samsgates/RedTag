from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.domain import Incident, InventoryLot, Organization, ProofNode, SupplyNode
from app.services.workflow import RecallWorkflow


def test_simulation_uses_trace_batches_instead_of_demo_constants():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        db.add(Organization(id="tenant_acme", name="Acme", autonomy_level=2))
        incident = Incident(
            tenant_id="tenant_acme",
            created_by="u1",
            title="Custom incident",
            description="custom trace",
            status="SCOPE_PROPOSED",
            affected_units=40,
            affected_customers=9,
        )
        db.add(incident)
        db.flush()
        db.add_all(
            [
                SupplyNode(id="batch_alpha", tenant_id="tenant_acme", node_type="MANUFACTURING_BATCH", label="BATCH-ALPHA", attrs={"affected_customer_count": 9}),
                InventoryLot(id="lot_alpha", tenant_id="tenant_acme", product_id="product_alpha", manufacturing_batch_id="BATCH-ALPHA", warehouse="A", quantity=40, status="AVAILABLE"),
                ProofNode(tenant_id="tenant_acme", incident_id=incident.id, node_type="TRACE", label="custom trace", status="SUPPORTED", data={"batch_ids": ["BATCH-ALPHA"]}),
            ]
        )
        db.commit()

        strategies = RecallWorkflow(db).simulate(incident)
        assert strategies[0].scope["batches"] == ["BATCH-ALPHA"]
        assert strategies[1].scope["batches"] == ["BATCH-ALPHA"]
        assert all("BAT-8831" not in str(strategy.scope) for strategy in strategies)
