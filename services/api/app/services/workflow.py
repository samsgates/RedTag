from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.contracts import IncidentFinding
from app.core.config import get_settings
from app.models.domain import (
    Action,
    ActionReceipt,
    EvidenceArtifact,
    EvidenceClaim,
    Incident,
    IncidentStatus,
    InventoryLot,
    Notification,
    Order,
    ReturnCase,
    Shipment,
    ProofEdge,
    ProofNode,
    RecallStrategy,
    SupplyEdge,
    SupplyNode,
    VerificationStatus,
)
from app.services.actions import execute_action, request_action, request_inventory_action, verify_action
from app.services.audit import audit


class RecallWorkflow:
    """Durable domain workflow.

    In cloud deployments Pub/Sub or Agent Runtime can trigger each phase. This service keeps the
    transitions deterministic and independently testable.
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def triage(self, incident: Incident) -> IncidentFinding:
        incident.status = IncidentStatus.TRIAGING.value
        artifacts = list(
            self.db.scalars(
                select(EvidenceArtifact)
                .where(
                    EvidenceArtifact.tenant_id == incident.tenant_id,
                    EvidenceArtifact.incident_id == incident.id,
                )
                .order_by(EvidenceArtifact.created_at.asc())
                .limit(10)
            )
        )
        evidence_manifest = [
            {
                "id": item.id,
                "file_name": item.file_name,
                "content_type": item.content_type,
                "storage_uri": item.storage_uri,
                "checksum_sha256": item.checksum_sha256,
                "trust_level": item.trust_level,
            }
            for item in artifacts
        ]
        if self.settings.real_ai_enabled:
            from app.agents.gemini import GeminiStructuredClient

            finding = GeminiStructuredClient().triage(
                f"{incident.title}\n{incident.description}",
                evidence_manifest=evidence_manifest,
            )
        else:
            finding = IncidentFinding(
                defect_type="thermal connector failure",
                component="X91 Connector",
                supplier_batch="C-771",
                manufacturing_batches=["BAT-8831", "BAT-8832"],
                severity="HIGH",
                confidence=0.96,
                evidence_ids=[item.id for item in artifacts if item.trust_level != "BLOCKED"],
                summary="Connector X91 from supplier batch C-771 may overheat under load.",
            )
        incident.severity = finding.severity
        incident.status = IncidentStatus.INVESTIGATING.value

        valid_evidence_ids = {item.id for item in artifacts}
        provenance_ids = [item for item in finding.evidence_ids if item in valid_evidence_ids]
        if not provenance_ids and artifacts:
            provenance_ids = [item.id for item in artifacts]
        claim_values = [
            ("defect_type", finding.defect_type),
            ("component", finding.component),
            ("supplier_batch", finding.supplier_batch),
        ] + [("manufacturing_batch", value) for value in finding.manufacturing_batches]
        for claim_type, value in claim_values:
            if value is None:
                continue
            for evidence_id in provenance_ids[:3]:
                self.db.add(
                    EvidenceClaim(
                        tenant_id=incident.tenant_id,
                        incident_id=incident.id,
                        evidence_id=evidence_id,
                        claim_type=claim_type,
                        value=str(value),
                        confidence=finding.confidence,
                        provenance={"source": "incident-agent", "evidence_id": evidence_id},
                    )
                )

        node = ProofNode(
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            node_type="FINDING",
            label=finding.summary,
            status="SUPPORTED",
            data=finding.model_dump(),
        )
        self.db.add(node)
        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="agent",
            actor_id="incident-agent",
            event_type="incident.triage.completed",
            payload=finding.model_dump(),
        )
        self.db.commit()
        return finding

    def trace(self, incident: Incident) -> dict:
        nodes = list(
            self.db.scalars(select(SupplyNode).where(SupplyNode.tenant_id == incident.tenant_id))
        )
        edges = list(
            self.db.scalars(select(SupplyEdge).where(SupplyEdge.tenant_id == incident.tenant_id))
        )
        if not nodes:
            raise RuntimeError("No supply genealogy is available for this tenant")

        latest_finding = self.db.scalar(
            select(ProofNode)
            .where(
                ProofNode.tenant_id == incident.tenant_id,
                ProofNode.incident_id == incident.id,
                ProofNode.node_type == "FINDING",
            )
            .order_by(ProofNode.created_at.desc())
        )
        if not latest_finding:
            raise RuntimeError("Run incident triage before supply tracing")
        finding = latest_finding.data or {}
        requested_labels = {
            str(value).strip().lower()
            for value in [finding.get("component"), finding.get("supplier_batch"), *(finding.get("manufacturing_batches") or [])]
            if value
        }
        by_id = {node.id: node for node in nodes}
        seed_ids = {node.id for node in nodes if node.label.strip().lower() in requested_labels}
        if not seed_ids:
            raise RuntimeError("Triage findings do not resolve to authoritative supply genealogy")

        adjacency: dict[str, list[str]] = {}
        for edge in edges:
            adjacency.setdefault(edge.from_id, []).append(edge.to_id)
        visited = set(seed_ids)
        queue = list(seed_ids)
        while queue:
            current = queue.pop(0)
            for child in adjacency.get(current, []):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)

        explicit_batches = {str(x).strip().lower() for x in finding.get("manufacturing_batches", [])}
        batch_nodes = [
            node
            for node in nodes
            if node.node_type == "MANUFACTURING_BATCH"
            and (node.id in visited or node.label.strip().lower() in explicit_batches)
        ]
        batch_ids = sorted({node.label for node in batch_nodes})
        if not batch_ids:
            raise RuntimeError("No authoritative manufacturing batches could be traced")

        lots = list(
            self.db.scalars(
                select(InventoryLot).where(
                    InventoryLot.tenant_id == incident.tenant_id,
                    InventoryLot.manufacturing_batch_id.in_(batch_ids),
                )
            )
        )
        affected_units = sum(lot.quantity for lot in lots)
        actual_customers = int(
            self.db.scalar(
                select(func.count(func.distinct(Order.customer_id))).where(
                    Order.tenant_id == incident.tenant_id,
                    Order.manufacturing_batch_id.in_(batch_ids),
                )
            )
            or 0
        )
        aggregate_customers = sum(int(node.attrs.get("affected_customer_count", 0) or 0) for node in batch_nodes)
        affected_customers = max(actual_customers, aggregate_customers)
        incident.affected_units = affected_units
        incident.affected_customers = affected_customers
        incident.status = IncidentStatus.SCOPE_PROPOSED.value

        trace_node = ProofNode(
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            node_type="TRACE",
            label=f"Trace found {len(batch_ids)} affected manufacturing batches",
            status="SUPPORTED",
            data={
                "batch_ids": batch_ids,
                "inventory_lots": [item.id for item in lots],
                "graph_nodes": sorted(visited),
                "customer_records_loaded": actual_customers,
                "customer_exposure_count": affected_customers,
            },
        )
        self.db.add(trace_node)
        self.db.flush()
        self.db.add(
            ProofEdge(
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                from_node_id=latest_finding.id,
                to_node_id=trace_node.id,
                relation="supports_trace",
            )
        )
        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="agent",
            actor_id="trace-agent",
            event_type="trace.completed",
            payload={
                "affected_units": affected_units,
                "affected_customers": affected_customers,
                "batch_ids": batch_ids,
            },
        )
        self.db.commit()
        return {
            "batch_ids": batch_ids,
            "affected_units": affected_units,
            "affected_customers": affected_customers,
            "customer_records_loaded": actual_customers,
            "nodes": len(visited),
            "edges": len([e for e in edges if e.from_id in visited and e.to_id in visited]),
        }

    def simulate(self, incident: Incident) -> list[RecallStrategy]:
        """Build deterministic, data-backed containment strategies.

        Gemini may explain or rank these candidates in higher-level agent flows, but the numerical
        scope is derived from authoritative genealogy, inventory, and order data. This keeps the
        simulation useful for arbitrary tenant datasets instead of being tied to the demo scenario.
        """
        existing = list(
            self.db.scalars(
                select(RecallStrategy).where(
                    RecallStrategy.tenant_id == incident.tenant_id,
                    RecallStrategy.incident_id == incident.id,
                )
            )
        )
        if existing:
            return existing

        trace_node = self.db.scalar(
            select(ProofNode)
            .where(
                ProofNode.tenant_id == incident.tenant_id,
                ProofNode.incident_id == incident.id,
                ProofNode.node_type == "TRACE",
            )
            .order_by(ProofNode.created_at.desc())
        )
        if not trace_node:
            raise ValueError("Run supply tracing before simulation")
        batch_ids = list(dict.fromkeys((trace_node.data or {}).get("batch_ids", [])))
        if not batch_ids:
            raise ValueError("Trace contains no manufacturing batches")

        batch_nodes = list(
            self.db.scalars(
                select(SupplyNode).where(
                    SupplyNode.tenant_id == incident.tenant_id,
                    SupplyNode.node_type == "MANUFACTURING_BATCH",
                    SupplyNode.label.in_(batch_ids),
                )
            )
        )
        node_by_label = {node.label: node for node in batch_nodes}
        lots = list(
            self.db.scalars(
                select(InventoryLot).where(
                    InventoryLot.tenant_id == incident.tenant_id,
                    InventoryLot.manufacturing_batch_id.in_(batch_ids),
                )
            )
        )
        units_by_batch = {batch_id: 0 for batch_id in batch_ids}
        for lot in lots:
            units_by_batch[lot.manufacturing_batch_id] = units_by_batch.get(lot.manufacturing_batch_id, 0) + lot.quantity

        def customer_count_for(batches: list[str]) -> int:
            actual = int(
                self.db.scalar(
                    select(func.count(func.distinct(Order.customer_id))).where(
                        Order.tenant_id == incident.tenant_id,
                        Order.manufacturing_batch_id.in_(batches),
                    )
                )
                or 0
            )
            aggregate = sum(
                int((node_by_label.get(batch).attrs if node_by_label.get(batch) else {}).get("affected_customer_count", 0) or 0)
                for batch in batches
            )
            return max(actual, aggregate)

        total_units = max(1, sum(units_by_batch.values()))
        focused_batch = max(batch_ids, key=lambda item: units_by_batch.get(item, 0))
        focused_units = max(1, units_by_batch.get(focused_batch, 0))
        focused_customers = customer_count_for([focused_batch])
        focused_coverage = round(min(0.98, max(0.05, focused_units / total_units)), 3)

        affected_product_ids = sorted({lot.product_id for lot in lots})
        all_product_lots = (
            list(
                self.db.scalars(
                    select(InventoryLot).where(
                        InventoryLot.tenant_id == incident.tenant_id,
                        InventoryLot.product_id.in_(affected_product_ids),
                    )
                )
            )
            if affected_product_ids
            else []
        )
        expanded_batches = sorted({lot.manufacturing_batch_id for lot in all_product_lots}) or batch_ids
        expanded_units = sum(lot.quantity for lot in all_product_lots) or total_units
        expanded_customers = customer_count_for(expanded_batches)
        if expanded_customers == 0:
            expanded_customers = incident.affected_customers

        # Costs are explicitly modeled estimates. They are not legal or accounting conclusions.
        containment_unit_cost = 500.0
        outreach_customer_cost = 25.0
        fixed_incident_cost = 50_000.0

        def estimate_cost(units: int, customers: int) -> float:
            return round(fixed_incident_cost + units * containment_unit_cost + customers * outreach_customer_cost, 2)

        strategies = [
            RecallStrategy(
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                name=f"Focused batch: {focused_batch}",
                scope={"batches": [focused_batch]},
                affected_customers=focused_customers,
                affected_units=focused_units,
                coverage=focused_coverage,
                estimated_cost=estimate_cost(focused_units, focused_customers),
                residual_risk="HIGH" if len(batch_ids) > 1 else "MEDIUM",
                recommended=False,
                rationale="Smallest data-backed scope. Lower disruption, but it may leave other traced batches exposed.",
            ),
            RecallStrategy(
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                name="All traced affected batches",
                scope={"batches": batch_ids},
                affected_customers=incident.affected_customers,
                affected_units=incident.affected_units,
                coverage=0.992,
                estimated_cost=estimate_cost(incident.affected_units, incident.affected_customers),
                residual_risk="LOW",
                recommended=True,
                rationale="Recommended containment boundary because it covers every manufacturing batch supported by the current trace evidence.",
            ),
            RecallStrategy(
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                name="Expanded product-family precaution",
                scope={"products": affected_product_ids, "batches": expanded_batches},
                affected_customers=max(expanded_customers, incident.affected_customers),
                affected_units=max(expanded_units, incident.affected_units),
                coverage=0.999,
                estimated_cost=estimate_cost(max(expanded_units, incident.affected_units), max(expanded_customers, incident.affected_customers)),
                residual_risk="LOW",
                recommended=False,
                rationale="Broadest precautionary scope derived from all inventory lots belonging to products reached by the trace.",
            ),
        ]
        self.db.add_all(strategies)
        incident.status = IncidentStatus.AWAITING_APPROVAL.value
        decision_node = ProofNode(
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            node_type="DECISION",
            label="Risk Agent recommends all traced affected batches",
            status="RECOMMENDED",
            data={
                "recommended": "All traced affected batches",
                "source_trace_node": trace_node.id,
                "assumptions": {
                    "containment_unit_cost": containment_unit_cost,
                    "outreach_customer_cost": outreach_customer_cost,
                    "fixed_incident_cost": fixed_incident_cost,
                },
            },
        )
        self.db.add(decision_node)
        self.db.flush()
        self.db.add(
            ProofEdge(
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                from_node_id=trace_node.id,
                to_node_id=decision_node.id,
                relation="supports_decision",
            )
        )
        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="agent",
            actor_id="risk-agent",
            event_type="scope.generated",
            payload={"strategies": [s.name for s in strategies], "recommended": "All traced affected batches"},
        )
        self.db.commit()
        return strategies

    def _strategy_batches(self, incident: Incident, strategy: RecallStrategy | None) -> list[str]:
        if not strategy:
            return []
        batches = list(dict.fromkeys(strategy.scope.get("batches", [])))
        if batches:
            return batches
        products = list(dict.fromkeys(strategy.scope.get("products", [])))
        if not products:
            return []
        # Product scope may contain canonical product node IDs. Resolve the matching inventory lots.
        return sorted(
            set(
                self.db.scalars(
                    select(InventoryLot.manufacturing_batch_id).where(
                        InventoryLot.tenant_id == incident.tenant_id,
                        InventoryLot.product_id.in_(products),
                    )
                )
            )
        )

    def _approved_batches(self, incident: Incident) -> list[str]:
        strategy = None
        if incident.approved_strategy_id:
            strategy = self.db.scalar(
                select(RecallStrategy).where(
                    RecallStrategy.id == incident.approved_strategy_id,
                    RecallStrategy.tenant_id == incident.tenant_id,
                    RecallStrategy.incident_id == incident.id,
                )
            )
        if not strategy:
            strategy = self.db.scalar(
                select(RecallStrategy).where(
                    RecallStrategy.tenant_id == incident.tenant_id,
                    RecallStrategy.incident_id == incident.id,
                    RecallStrategy.recommended.is_(True),
                )
            )
        return self._strategy_batches(incident, strategy)

    def approve_and_contain(self, incident: Incident, strategy_id: str | None = None) -> list[Action]:
        if strategy_id:
            strategy = self.db.scalar(
                select(RecallStrategy).where(
                    RecallStrategy.id == strategy_id,
                    RecallStrategy.tenant_id == incident.tenant_id,
                    RecallStrategy.incident_id == incident.id,
                )
            )
        else:
            strategy = self.db.scalar(
                select(RecallStrategy).where(
                    RecallStrategy.tenant_id == incident.tenant_id,
                    RecallStrategy.incident_id == incident.id,
                    RecallStrategy.recommended.is_(True),
                )
            )
        if not strategy:
            raise ValueError("No valid recall strategy exists. Run simulation first or select a valid strategy.")
        incident.approved_strategy_id = strategy.id
        batches = self._strategy_batches(incident, strategy)
        if not batches:
            raise ValueError("Approved strategy does not resolve to manufacturing batches")
        incident.status = IncidentStatus.CONTAINING.value
        lots = list(
            self.db.scalars(
                select(InventoryLot).where(
                    InventoryLot.tenant_id == incident.tenant_id,
                    InventoryLot.manufacturing_batch_id.in_(batches),
                )
            )
        )
        actions: list[Action] = []
        for lot in lots:
            action = request_inventory_action(
                self.db,
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                agent_id="containment-agent",
                action_type="inventory.quarantine",
                lot_id=lot.id,
                risk_class="R2",
            )
            if action.status not in {"APPROVAL_REQUIRED", "BLOCKED"}:
                execute_action(self.db, action)
                verify_action(self.db, action)
            actions.append(action)

        affected_orders = list(
            self.db.scalars(
                select(Order).where(
                    Order.tenant_id == incident.tenant_id,
                    Order.manufacturing_batch_id.in_(batches),
                    Order.status == "READY_TO_SHIP",
                )
            )
        )
        order_ids = [o.id for o in affected_orders]
        shipments = (
            list(
                self.db.scalars(
                    select(Shipment).where(
                        Shipment.tenant_id == incident.tenant_id,
                        Shipment.order_id.in_(order_ids),
                    )
                )
            )
            if order_ids
            else []
        )
        for shipment in shipments:
            action = request_action(
                self.db,
                tenant_id=incident.tenant_id,
                incident_id=incident.id,
                agent_id="containment-agent",
                action_type="shipment.hold",
                target_type="shipment",
                target_id=shipment.id,
                risk_class="R2",
            )
            if action.status not in {"APPROVAL_REQUIRED", "BLOCKED"}:
                execute_action(self.db, action)
                verify_action(self.db, action)
            actions.append(action)
        incident.status = IncidentStatus.NOTIFYING.value
        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="user",
            actor_id="approver",
            event_type="scope.approved",
            payload={"strategy_id": strategy.id, "strategy_name": strategy.name, "batches": batches},
        )
        self.db.commit()
        self.refresh_verification_coverage(incident)
        return actions

    def unresolved_customer_count(self, incident: Incident) -> int:
        batches = self._approved_batches(incident)
        if not batches:
            return 0
        customer_ids = set(
            self.db.scalars(
                select(Order.customer_id).where(
                    Order.tenant_id == incident.tenant_id,
                    Order.manufacturing_batch_id.in_(batches),
                )
            )
        )
        if not customer_ids:
            return 0
        delivered = set(
            self.db.scalars(
                select(Notification.customer_id).where(
                    Notification.tenant_id == incident.tenant_id,
                    Notification.incident_id == incident.id,
                    Notification.status == "DELIVERED",
                )
            )
        )
        return len(customer_ids - delivered)

    def open_return_count(self, incident: Incident) -> int:
        return int(
            self.db.scalar(
                select(func.count(ReturnCase.id)).where(
                    ReturnCase.tenant_id == incident.tenant_id,
                    ReturnCase.incident_id == incident.id,
                    ReturnCase.status != "RECOVERED",
                )
            )
            or 0
        )

    def refresh_verification_coverage(self, incident: Incident) -> float:
        total = self.db.scalar(
            select(func.count(ActionReceipt.id)).where(
                ActionReceipt.tenant_id == incident.tenant_id,
                ActionReceipt.incident_id == incident.id,
            )
        ) or 0
        verified = self.db.scalar(
            select(func.count(ActionReceipt.id)).where(
                ActionReceipt.tenant_id == incident.tenant_id,
                ActionReceipt.incident_id == incident.id,
                ActionReceipt.verification_status == VerificationStatus.VERIFIED.value,
            )
        ) or 0
        incident.verification_coverage = 0.0 if total == 0 else round((verified / total) * 100, 2)
        unresolved = self.unresolved_customer_count(incident)
        open_returns = self.open_return_count(incident)
        if total > 0 and verified == total and unresolved == 0 and open_returns == 0:
            incident.status = IncidentStatus.READY_TO_CLOSE.value
        elif unresolved > 0:
            incident.status = IncidentStatus.NOTIFYING.value
        elif open_returns > 0:
            incident.status = IncidentStatus.RECOVERING.value
        elif total > 0 and verified < total:
            incident.status = IncidentStatus.VERIFYING.value
        self.db.commit()
        return incident.verification_coverage

    def close(self, incident: Incident) -> None:
        self.refresh_verification_coverage(incident)
        if incident.status != IncidentStatus.READY_TO_CLOSE.value or incident.verification_coverage < 100:
            raise ValueError(
                "Incident cannot close until critical actions are verified, customers are reached, "
                "and return cases are recovered or explicitly resolved"
            )
        incident.status = IncidentStatus.VERIFIED_CLOSED.value
        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="user",
            actor_id="authorized-closer",
            event_type="incident.closed",
            payload={"verification_coverage": incident.verification_coverage},
        )
        self.db.commit()
