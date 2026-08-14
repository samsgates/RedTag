"""Durable RedTag autopilot orchestration.

The runner intentionally advances only through states that are safe to execute without additional
human authority. High-impact scope approval and final verified closure remain explicit gates.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Incident, IncidentStatus
from app.services.audit import audit
from app.services.customer_recall import CustomerRecallService
from app.services.events import enqueue_event
from app.services.workflow import RecallWorkflow


@dataclass(frozen=True)
class AutopilotResult:
    incident_id: str
    status: str
    phases: tuple[str, ...]
    waiting_for: str | None


class AutopilotRunner:
    """Advance an incident until the next safety or external-world gate."""

    MAX_PHASES = 8

    def __init__(self, db: Session):
        self.db = db

    def run(self, incident: Incident) -> AutopilotResult:
        phases: list[str] = []
        waiting_for: str | None = None

        for _ in range(self.MAX_PHASES):
            status = incident.status
            workflow = RecallWorkflow(self.db)

            if status == IncidentStatus.NEW.value:
                workflow.triage(incident)
                phases.append("triage")
                continue
            if status == IncidentStatus.INVESTIGATING.value:
                workflow.trace(incident)
                phases.append("trace")
                continue
            if status == IncidentStatus.SCOPE_PROPOSED.value:
                workflow.simulate(incident)
                phases.append("simulate")
                continue
            if status == IncidentStatus.AWAITING_APPROVAL.value:
                waiting_for = "recall_scope_approval"
                break
            if status == IncidentStatus.NOTIFYING.value:
                CustomerRecallService(self.db).notify(incident)
                phases.append("notify_and_recover_delivery_failures")
                self.db.refresh(incident)
                # Contact failures require additional enterprise data or human resolution. Product
                # return cases require physical-world events. Do not spin on either state.
                if incident.status == IncidentStatus.NOTIFYING.value:
                    waiting_for = "customer_contact_exception_resolution"
                elif incident.status == IncidentStatus.RECOVERING.value:
                    waiting_for = "physical_product_recovery"
                continue
            if status == IncidentStatus.VERIFYING.value:
                workflow.refresh_verification_coverage(incident)
                phases.append("verification_refresh")
                self.db.refresh(incident)
                continue
            if status == IncidentStatus.RECOVERING.value:
                waiting_for = "physical_product_recovery"
                break
            if status == IncidentStatus.READY_TO_CLOSE.value:
                waiting_for = "authorized_closure"
                break
            if status in {
                IncidentStatus.VERIFIED_CLOSED.value,
                IncidentStatus.PAUSED.value,
                IncidentStatus.SECURITY_HOLD.value,
                IncidentStatus.EXCEPTIONS_OPEN.value,
                IncidentStatus.FAILED.value,
                IncidentStatus.REOPENED.value,
            }:
                waiting_for = status.lower()
                break
            # CONTAINING is normally completed in one guarded transaction by approve_and_contain.
            # Any other state indicates a recoverable workflow interruption that should be inspected.
            waiting_for = f"state:{status.lower()}"
            break
        else:
            waiting_for = "loop_guard"

        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="agent",
            actor_id="recall-director",
            event_type="autopilot.cycle.completed",
            payload={"phases": phases, "status": incident.status, "waiting_for": waiting_for},
        )
        self.db.commit()
        return AutopilotResult(
            incident_id=incident.id,
            status=incident.status,
            phases=tuple(phases),
            waiting_for=waiting_for,
        )


def queue_autopilot(
    db: Session,
    *,
    incident: Incident,
    requested_by: str,
    event_type: str = "incident.autopilot.requested",
) -> str:
    """Queue a durable autopilot cycle through the transactional outbox."""

    event = enqueue_event(
        db,
        tenant_id=incident.tenant_id,
        event_type=event_type,
        incident_id=incident.id,
        payload={"incident_id": incident.id, "requested_by": requested_by},
    )
    audit(
        db,
        tenant_id=incident.tenant_id,
        incident_id=incident.id,
        actor_type="user" if requested_by != "system" else "system",
        actor_id=requested_by,
        event_type=event_type,
        payload={"event_id": event.id},
    )
    db.commit()
    return event.id


def get_incident_for_worker(db: Session, tenant_id: str, incident_id: str) -> Incident | None:
    return db.scalar(
        select(Incident).where(Incident.tenant_id == tenant_id, Incident.id == incident_id)
    )
