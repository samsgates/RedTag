from typing import Literal

from pydantic import BaseModel, Field


class IncidentFinding(BaseModel):
    defect_type: str
    component: str | None = None
    supplier_batch: str | None = None
    manufacturing_batches: list[str] = Field(default_factory=list)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    summary: str


class TracePlan(BaseModel):
    seed_entities: list[str]
    relationships_to_resolve: list[str]
    stop_conditions: list[str]


class StrategyCandidate(BaseModel):
    name: str
    batches: list[str]
    affected_customers: int
    affected_units: int
    coverage: float = Field(ge=0, le=1)
    estimated_cost: float = Field(ge=0)
    residual_risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    rationale: str


class StrategySet(BaseModel):
    strategies: list[StrategyCandidate]
    recommended_name: str
