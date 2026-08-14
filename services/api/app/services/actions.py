import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.registry import connector_for_action, expected_state
from app.models.domain import (
    Action,
    ActionReceipt,
    ActionStatus,
    Approval,
    Organization,
    ProofEdge,
    ProofNode,
    Verification,
    VerificationStatus,
)
from app.services.audit import audit
from app.services.policy import PolicyEngine


def stable_hash(data: dict | None) -> str | None:
    if data is None:
        return None
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def build_idempotency_key(
    tenant_id: str,
    incident_id: str,
    action_type: str,
    target_id: str,
    version: str = "1",
) -> str:
    raw = f"{tenant_id}|{incident_id}|{action_type}|{target_id}|{version}"
    return hashlib.sha256(raw.encode()).hexdigest()


def request_action(
    db: Session,
    *,
    tenant_id: str,
    incident_id: str,
    agent_id: str,
    action_type: str,
    target_type: str,
    target_id: str,
    risk_class: str = "R2",
    payload: dict | None = None,
    quantity: int = 0,
    customer_count: int = 0,
) -> Action:
    key = build_idempotency_key(tenant_id, incident_id, action_type, target_id)
    existing = db.scalar(
        select(Action).where(Action.tenant_id == tenant_id, Action.idempotency_key == key)
    )
    if existing:
        return existing

    org = db.get(Organization, tenant_id)
    autonomy = org.autonomy_level if org else 2
    decision = PolicyEngine().evaluate(
        action_type=action_type,
        risk_class=risk_class,
        autonomy_level=autonomy,
        quantity=quantity,
        customer_count=customer_count,
    )
    action = Action(
        tenant_id=tenant_id,
        incident_id=incident_id,
        agent_id=agent_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        risk_class=risk_class,
        status=(
            ActionStatus.APPROVAL_REQUIRED.value
            if decision.approval_required
            else ActionStatus.BLOCKED.value
            if decision.outcome == "DENY"
            else ActionStatus.PENDING.value
        ),
        idempotency_key=key,
        policy_decision=decision.as_dict(),
        payload=payload or {},
    )
    db.add(action)
    db.flush()
    if decision.approval_required:
        db.add(
            Approval(
                tenant_id=tenant_id,
                incident_id=incident_id,
                action_type=action_type,
                risk_class=risk_class,
                payload={"action_id": action.id, "target_id": target_id},
                requested_by=agent_id,
            )
        )
    if decision.outcome == "DENY":
        audit(
            db,
            tenant_id=tenant_id,
            incident_id=incident_id,
            actor_type="system",
            actor_id="policy-engine",
            event_type="action.blocked",
            payload={"action_id": action.id, "action_type": action_type, "reason": decision.reason},
        )
    return action


def request_inventory_action(
    db: Session,
    *,
    tenant_id: str,
    incident_id: str,
    agent_id: str,
    action_type: str,
    lot_id: str,
    risk_class: str = "R2",
) -> Action:
    return request_action(
        db,
        tenant_id=tenant_id,
        incident_id=incident_id,
        agent_id=agent_id,
        action_type=action_type,
        target_type="inventory_lot",
        target_id=lot_id,
        risk_class=risk_class,
    )


def execute_action(db: Session, action: Action) -> Action:
    if action.status == ActionStatus.SUCCEEDED.value:
        return action
    if action.policy_decision.get("outcome") == "DENY":
        action.status = ActionStatus.BLOCKED.value
        return action
    if action.status == ActionStatus.APPROVAL_REQUIRED.value:
        return action

    action.status = ActionStatus.RUNNING.value
    try:
        connector = connector_for_action(db, action.tenant_id, action.action_type)
        result = connector.execute(action.action_type, action.target_id, action.payload)
    except ValueError as exc:
        action.status = ActionStatus.FAILED.value
        action.error = str(exc)
        return action

    if not result.success:
        action.status = ActionStatus.FAILED.value
        action.error = result.error
        audit(
            db,
            tenant_id=action.tenant_id,
            incident_id=action.incident_id,
            actor_type="agent",
            actor_id=action.agent_id,
            event_type="action.failed",
            payload={"action_id": action.id, "error": action.error},
        )
        return action

    action.status = ActionStatus.SUCCEEDED.value
    expected = expected_state(action.action_type)
    if action.action_type.startswith("customer.notify_"):
        expected = {**expected, "incident_id": action.payload.get("incident_id")}
    action.payload = {**action.payload, "expected": expected}
    receipt = ActionReceipt(
        tenant_id=action.tenant_id,
        action_id=action.id,
        incident_id=action.incident_id,
        agent_id=action.agent_id,
        tool=action.action_type,
        status="succeeded",
        before_state_hash=stable_hash(result.before),
        after_state_hash=stable_hash(result.after),
        external_reference=result.external_reference,
    )
    db.add(receipt)
    db.flush()

    action_node = ProofNode(
        tenant_id=action.tenant_id,
        incident_id=action.incident_id,
        node_type="ACTION",
        label=f"{action.action_type} {action.target_id}",
        status="SUCCESS",
        ref_type="action",
        ref_id=action.id,
        data={"receipt_id": receipt.id},
    )
    db.add(action_node)
    audit(
        db,
        tenant_id=action.tenant_id,
        incident_id=action.incident_id,
        actor_type="agent",
        actor_id=action.agent_id,
        event_type="action.executed",
        payload={"action_id": action.id, "tool": action.action_type, "target": action.target_id},
    )
    return action


def execute_inventory_action(db: Session, action: Action) -> Action:
    return execute_action(db, action)


def verify_action(db: Session, action: Action) -> Verification | None:
    receipt = db.scalar(select(ActionReceipt).where(ActionReceipt.action_id == action.id))
    if not receipt:
        return None
    existing = db.scalar(select(Verification).where(Verification.action_id == action.id))
    if existing:
        return existing

    try:
        connector = connector_for_action(db, action.tenant_id, action.action_type)
        result = connector.verify(
            action.action_type,
            action.target_id,
            action.payload.get("expected", {}),
        )
    except ValueError as exc:
        result = {"verified": False, "reason": str(exc)}
    status = (
        VerificationStatus.VERIFIED.value
        if result["verified"]
        else VerificationStatus.FAILED.value
    )
    verification = Verification(
        tenant_id=action.tenant_id,
        incident_id=action.incident_id,
        action_id=action.id,
        receipt_id=receipt.id,
        status=status,
        method="authoritative_readback",
        details=result,
    )
    db.add(verification)
    receipt.verification_status = status
    db.flush()

    verify_node = ProofNode(
        tenant_id=action.tenant_id,
        incident_id=action.incident_id,
        node_type="VERIFICATION",
        label=f"Verified {action.action_type} on {action.target_id}",
        status=status,
        ref_type="verification",
        ref_id=verification.id,
        data=result,
    )
    db.add(verify_node)
    action_node = db.scalar(
        select(ProofNode).where(ProofNode.ref_type == "action", ProofNode.ref_id == action.id)
    )
    if action_node:
        db.flush()
        db.add(
            ProofEdge(
                tenant_id=action.tenant_id,
                incident_id=action.incident_id,
                from_node_id=action_node.id,
                to_node_id=verify_node.id,
                relation="verified_by",
            )
        )
    audit(
        db,
        tenant_id=action.tenant_id,
        incident_id=action.incident_id,
        actor_type="agent",
        actor_id="verification-agent",
        event_type="action.verified",
        payload={"action_id": action.id, "status": status},
    )
    return verification
