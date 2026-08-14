from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:20]}"


class IncidentStatus(StrEnum):
    NEW = "NEW"
    TRIAGING = "TRIAGING"
    INVESTIGATING = "INVESTIGATING"
    SCOPE_PROPOSED = "SCOPE_PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    CONTAINING = "CONTAINING"
    NOTIFYING = "NOTIFYING"
    RECOVERING = "RECOVERING"
    VERIFYING = "VERIFYING"
    EXCEPTIONS_OPEN = "EXCEPTIONS_OPEN"
    READY_TO_CLOSE = "READY_TO_CLOSE"
    VERIFIED_CLOSED = "VERIFIED_CLOSED"
    PAUSED = "PAUSED"
    SECURITY_HOLD = "SECURITY_HOLD"
    FAILED = "FAILED"
    REOPENED = "REOPENED"


class ActionStatus(StrEnum):
    PENDING = "PENDING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class TenantScoped:
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    autonomy_level: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)




class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Membership(Base, TenantScoped):
    __tablename__ = "memberships"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("membership"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    roles: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),)


class Incident(Base, TenantScoped):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("inc"))
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(40), default=IncidentStatus.NEW.value, index=True)
    product_hint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approved_strategy_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    affected_customers: Mapped[int] = mapped_column(Integer, default=0)
    affected_units: Mapped[int] = mapped_column(Integer, default=0)
    verification_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EvidenceArtifact(Base, TenantScoped):
    __tablename__ = "evidence_artifacts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("ev"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128))
    storage_uri: Mapped[str] = mapped_column(Text)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    trust_level: Mapped[str] = mapped_column(String(32), default="UNTRUSTED")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceClaim(Base, TenantScoped):
    __tablename__ = "evidence_claims"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("claim"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_artifacts.id", ondelete="CASCADE"), index=True)
    claim_type: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SupplyNode(Base, TenantScoped):
    __tablename__ = "supply_nodes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_type: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(255))
    attrs: Mapped[dict] = mapped_column(JSON, default=dict)


class SupplyEdge(Base, TenantScoped):
    __tablename__ = "supply_edges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("edge"))
    from_id: Mapped[str] = mapped_column(String(64), index=True)
    to_id: Mapped[str] = mapped_column(String(64), index=True)
    relation: Mapped[str] = mapped_column(String(64))
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("tenant_id", "from_id", "to_id", "relation", name="uq_supply_edge"),)


class InventoryLot(Base, TenantScoped):
    __tablename__ = "inventory_lots"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    manufacturing_batch_id: Mapped[str] = mapped_column(String(64), index=True)
    warehouse: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="AVAILABLE")
    version: Mapped[int] = mapped_column(Integer, default=1)




class Customer(Base, TenantScoped):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    external_ref: Mapped[str] = mapped_column(String(128), index=True)
    first_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str] = mapped_column(String(64), default="US")
    contact_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "external_ref", name="uq_customer_external"),)


class Order(Base, TenantScoped):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    manufacturing_batch_id: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="FULFILLED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Shipment(Base, TenantScoped):
    __tablename__ = "shipments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    carrier: Mapped[str] = mapped_column(String(80), default="DemoCarrier")
    tracking_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="READY_TO_SHIP")
    version: Mapped[int] = mapped_column(Integer, default=1)


class Notification(Base, TenantScoped):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("notification"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(24))
    template_id: Mapped[str] = mapped_column(String(80), default="recall-safety-v1")
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "incident_id", "customer_id", "channel", name="uq_notification_once"),)


class ReturnCase(Base, TenantScoped):
    __tablename__ = "return_cases"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("return"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    recovery_method: Mapped[str] = mapped_column(String(32), default="RETURN_LABEL")
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "incident_id", "order_id", name="uq_return_order_incident"),)


class RecallStrategy(Base, TenantScoped):
    __tablename__ = "recall_strategies"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("strategy"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    scope: Mapped[dict] = mapped_column(JSON)
    affected_customers: Mapped[int] = mapped_column(Integer)
    affected_units: Mapped[int] = mapped_column(Integer)
    coverage: Mapped[float] = mapped_column(Float)
    estimated_cost: Mapped[float] = mapped_column(Float)
    residual_risk: Mapped[str] = mapped_column(String(32))
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Approval(Base, TenantScoped):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("approval"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    risk_class: Mapped[str] = mapped_column(String(8))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="WAITING")
    requested_by: Mapped[str] = mapped_column(String(128))
    decided_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Action(Base, TenantScoped):
    __tablename__ = "actions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("act"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    agent_id: Mapped[str] = mapped_column(String(100))
    action_type: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(128))
    risk_class: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default=ActionStatus.PENDING.value)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(180))
    policy_decision: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_action_idempotency"),)


class ActionReceipt(Base, TenantScoped):
    __tablename__ = "action_receipts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("receipt"))
    action_id: Mapped[str] = mapped_column(ForeignKey("actions.id", ondelete="CASCADE"), unique=True)
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_id: Mapped[str] = mapped_column(String(100))
    agent_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    tool: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(32))
    before_state_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    after_state_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default=VerificationStatus.PENDING.value)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Verification(Base, TenantScoped):
    __tablename__ = "verifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("verify"))
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    action_id: Mapped[str] = mapped_column(ForeignKey("actions.id", ondelete="CASCADE"), index=True)
    receipt_id: Mapped[str] = mapped_column(ForeignKey("action_receipts.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32))
    method: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProofNode(Base, TenantScoped):
    __tablename__ = "proof_nodes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("proof"))
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    node_type: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="INFO")
    ref_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ref_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProofEdge(Base, TenantScoped):
    __tablename__ = "proof_edges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("pedge"))
    incident_id: Mapped[str] = mapped_column(String(64), index=True)
    from_node_id: Mapped[str] = mapped_column(String(64), index=True)
    to_node_id: Mapped[str] = mapped_column(String(64), index=True)
    relation: Mapped[str] = mapped_column(String(64))


class AuditEvent(Base, TenantScoped):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("audit"))
    incident_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SecurityEvent(Base, TenantScoped):
    __tablename__ = "security_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("sec"))
    incident_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="HIGH")
    source: Mapped[str] = mapped_column(String(255))
    attempted_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decision: Mapped[str] = mapped_column(String(32), default="BLOCKED")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OutboxEvent(Base, TenantScoped):
    __tablename__ = "outbox_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("evt"))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    incident_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    causation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


Index("ix_audit_tenant_incident_created", AuditEvent.tenant_id, AuditEvent.incident_id, AuditEvent.created_at)
Index("ix_actions_tenant_incident_created", Action.tenant_id, Action.incident_id, Action.created_at)
