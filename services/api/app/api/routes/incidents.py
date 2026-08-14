from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import Principal, get_principal, require_roles
from app.db.locks import incident_advisory_lock
from app.db.session import get_db
from app.models.domain import (
    Action,
    AuditEvent,
    EvidenceArtifact,
    Incident,
    ProofEdge,
    ProofNode,
    RecallStrategy,
)
from app.schemas.common import TimelineItem
from app.schemas.incidents import (
    ActionRead,
    EvidenceRead,
    IncidentCommandResponse,
    IncidentCreate,
    IncidentRead,
    ProofGraph,
    StrategyRead,
)
from app.services.audit import audit
from app.services.autopilot import AutopilotRunner, queue_autopilot
from app.services.customer_recall import CustomerRecallService
from app.services.incidents import create_incident, get_incident, list_incidents
from app.services.security_service import inspect_binary_and_record, inspect_pdf_and_record, inspect_text_and_record
from app.services.storage import EvidenceStorage
from app.services.upload_security import validate_evidence_upload
from app.services.workflow import RecallWorkflow

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _incident_or_404(db: Session, tenant_id: str, incident_id: str) -> Incident:
    incident = get_incident(db, tenant_id, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> Incident:
    return create_incident(db, principal.tenant_id, principal.user_id, payload)


@router.get("", response_model=list[IncidentRead])
def list_all(
    db: Session = Depends(get_db), principal: Principal = Depends(get_principal)
) -> list[Incident]:
    return list_incidents(db, principal.tenant_id)


@router.get("/{incident_id}", response_model=IncidentRead)
def get_one(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> Incident:
    return _incident_or_404(db, principal.tenant_id, incident_id)


@router.post("/{incident_id}/evidence", response_model=EvidenceRead, status_code=201)
async def upload_evidence(
    incident_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> EvidenceArtifact:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    content = await file.read()
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds upload limit")
    content_type = (file.content_type or "application/octet-stream").lower()
    try:
        validate_evidence_upload(file.filename or "evidence.bin", content_type, content)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    uri, digest = EvidenceStorage().save(
        tenant_id=principal.tenant_id,
        incident_id=incident.id,
        file_name=file.filename or "evidence.bin",
        content=content,
    )
    row = EvidenceArtifact(
        tenant_id=principal.tenant_id,
        incident_id=incident.id,
        file_name=file.filename or "evidence.bin",
        content_type=content_type,
        storage_uri=uri,
        checksum_sha256=digest,
        size_bytes=len(content),
    )
    db.add(row)
    security_events = []
    if content_type.startswith("text/") or content_type in {"text/csv", "application/csv"}:
        text = content.decode("utf-8", errors="replace")
        security_events = inspect_text_and_record(
            db,
            tenant_id=principal.tenant_id,
            incident_id=incident.id,
            source=file.filename or "uploaded-text",
            text=text,
        )
    elif content_type == "application/pdf":
        security_events = inspect_pdf_and_record(
            db,
            tenant_id=principal.tenant_id,
            incident_id=incident.id,
            source=file.filename or "uploaded-pdf",
            content=content,
        )
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        security_events = inspect_binary_and_record(
            db,
            tenant_id=principal.tenant_id,
            incident_id=incident.id,
            source=file.filename or "uploaded-docx",
            content=content,
            byte_type="WORD_DOCUMENT",
        )
    elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        security_events = inspect_binary_and_record(
            db,
            tenant_id=principal.tenant_id,
            incident_id=incident.id,
            source=file.filename or "uploaded-xlsx",
            content=content,
            byte_type="EXCEL_DOCUMENT",
        )
    if security_events:
        row.trust_level = "BLOCKED"
    audit(
        db,
        tenant_id=principal.tenant_id,
        incident_id=incident.id,
        actor_type="user",
        actor_id=principal.user_id,
        event_type="incident.evidence.received",
        payload={"evidence_id": row.id, "file_name": row.file_name, "sha256": digest},
    )
    db.commit()
    db.refresh(row)
    return row




@router.post("/{incident_id}/autopilot", response_model=IncidentCommandResponse, status_code=202)
def autopilot(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> IncidentCommandResponse:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    settings = get_settings()
    if settings.pubsub_enabled:
        event_id = queue_autopilot(
            db, incident=incident, requested_by=principal.user_id, event_type="incident.autopilot.requested"
        )
        return IncidentCommandResponse(
            incident_id=incident.id, event_id=event_id, message="Autopilot queued for durable execution"
        )
    with incident_advisory_lock(db, principal.tenant_id, incident.id) as acquired:
        if not acquired:
            raise HTTPException(status_code=409, detail="Incident workflow is already running")
        result = AutopilotRunner(db).run(incident)
        return IncidentCommandResponse(
            incident_id=incident.id,
            message=(
                f"Autopilot advanced through {', '.join(result.phases) or 'no executable phases'}; "
                f"waiting for {result.waiting_for or 'next event'}"
            ),
        )


@router.post("/{incident_id}/triage", response_model=IncidentCommandResponse, status_code=202)
def triage(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> IncidentCommandResponse:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    RecallWorkflow(db).triage(incident)
    return IncidentCommandResponse(incident_id=incident.id, message="Triage completed")


@router.post("/{incident_id}/trace", response_model=IncidentCommandResponse, status_code=202)
def trace(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> IncidentCommandResponse:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    RecallWorkflow(db).trace(incident)
    return IncidentCommandResponse(incident_id=incident.id, message="Trace completed")


@router.post("/{incident_id}/simulate", response_model=list[StrategyRead])
def simulate(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> list[RecallStrategy]:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    return RecallWorkflow(db).simulate(incident)


@router.post("/{incident_id}/approve-and-contain", response_model=list[ActionRead])
def approve_and_contain(
    incident_id: str,
    strategy_id: str | None = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Approver")),
) -> list[Action]:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    try:
        with incident_advisory_lock(db, principal.tenant_id, incident.id) as acquired:
            if not acquired:
                raise HTTPException(status_code=409, detail="Incident workflow is already running")
            actions = RecallWorkflow(db).approve_and_contain(incident, strategy_id=strategy_id)
            settings = get_settings()
            if settings.pubsub_enabled:
                queue_autopilot(
                    db,
                    incident=incident,
                    requested_by=principal.user_id,
                    event_type="incident.autopilot.resume",
                )
            else:
                AutopilotRunner(db).run(incident)
            return actions
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc




@router.post("/{incident_id}/notify", response_model=list[ActionRead])
def notify_customers(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Quality Manager")),
) -> list[Action]:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    return CustomerRecallService(db).notify(incident)


@router.post("/{incident_id}/close", response_model=IncidentRead)
def close(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles("Owner", "Tenant Admin", "Approver")),
) -> Incident:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    try:
        RecallWorkflow(db).close(incident)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return incident


@router.get("/{incident_id}/actions", response_model=list[ActionRead])
def actions(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> list[Action]:
    _incident_or_404(db, principal.tenant_id, incident_id)
    return list(
        db.scalars(
            select(Action)
            .where(Action.tenant_id == principal.tenant_id, Action.incident_id == incident_id)
            .order_by(Action.created_at.asc())
        )
    )


@router.get("/{incident_id}/strategies", response_model=list[StrategyRead])
def strategies(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> list[RecallStrategy]:
    _incident_or_404(db, principal.tenant_id, incident_id)
    return list(
        db.scalars(
            select(RecallStrategy)
            .where(
                RecallStrategy.tenant_id == principal.tenant_id,
                RecallStrategy.incident_id == incident_id,
            )
            .order_by(RecallStrategy.created_at.asc())
        )
    )


@router.get("/{incident_id}/proof", response_model=ProofGraph)
def proof(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> ProofGraph:
    incident = _incident_or_404(db, principal.tenant_id, incident_id)
    nodes = list(
        db.scalars(
            select(ProofNode)
            .where(ProofNode.tenant_id == principal.tenant_id, ProofNode.incident_id == incident_id)
            .order_by(ProofNode.created_at.asc())
        )
    )
    edges = list(
        db.scalars(
            select(ProofEdge).where(
                ProofEdge.tenant_id == principal.tenant_id, ProofEdge.incident_id == incident_id
            )
        )
    )
    return ProofGraph(
        nodes=[
            {
                "id": n.id,
                "type": n.node_type,
                "label": n.label,
                "status": n.status,
                "data": n.data,
            }
            for n in nodes
        ],
        edges=[
            {"id": e.id, "from": e.from_node_id, "to": e.to_node_id, "relation": e.relation}
            for e in edges
        ],
        verification_coverage=incident.verification_coverage,
    )


@router.get("/{incident_id}/timeline", response_model=list[TimelineItem])
def timeline(
    incident_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_principal),
) -> list[TimelineItem]:
    _incident_or_404(db, principal.tenant_id, incident_id)
    rows = list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == principal.tenant_id, AuditEvent.incident_id == incident_id)
            .order_by(AuditEvent.created_at.asc())
        )
    )
    return [
        TimelineItem(
            id=x.id,
            event_type=x.event_type,
            actor_type=x.actor_type,
            actor_id=x.actor_id,
            payload=x.payload,
            created_at=x.created_at,
        )
        for x in rows
    ]
