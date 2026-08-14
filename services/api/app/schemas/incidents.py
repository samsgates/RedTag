from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    description: str = Field(default="", max_length=5000)
    severity: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    product_hint: str | None = Field(default=None, max_length=200)


class IncidentRead(ORMModel):
    id: str
    tenant_id: str
    title: str
    description: str
    severity: str
    status: str
    product_hint: str | None
    approved_strategy_id: str | None
    affected_customers: int
    affected_units: int
    verification_coverage: float
    created_by: str
    created_at: datetime
    updated_at: datetime


class EvidenceRead(ORMModel):
    id: str
    incident_id: str
    file_name: str
    content_type: str
    storage_uri: str
    checksum_sha256: str
    trust_level: str
    size_bytes: int
    created_at: datetime


class StrategyRead(ORMModel):
    id: str
    incident_id: str
    name: str
    scope: dict[str, Any]
    affected_customers: int
    affected_units: int
    coverage: float
    estimated_cost: float
    residual_risk: str
    recommended: bool
    rationale: str
    created_at: datetime


class ActionRead(ORMModel):
    id: str
    incident_id: str
    agent_id: str
    action_type: str
    target_type: str
    target_id: str
    risk_class: str
    status: str
    payload: dict[str, Any]
    idempotency_key: str
    policy_decision: dict[str, Any]
    error: str | None
    created_at: datetime
    updated_at: datetime


class ApprovalRead(ORMModel):
    id: str
    incident_id: str
    action_type: str
    risk_class: str
    payload: dict[str, Any]
    status: str
    requested_by: str
    decided_by: str | None
    decided_at: datetime | None
    created_at: datetime


class ProofGraph(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    verification_coverage: float


class IncidentCommandResponse(BaseModel):
    accepted: bool = True
    incident_id: str
    event_id: str | None = None
    message: str
