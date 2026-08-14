"""Pub/Sub consumer for durable RedTag workflow commands."""

import json

import structlog
from google.cloud import pubsub_v1

from app.core.config import get_settings
from app.db.locks import incident_advisory_lock
from app.db.session import SessionLocal
from app.db.tenant import bind_tenant
from app.services.autopilot import AutopilotRunner, get_incident_for_worker

log = structlog.get_logger()
AUTOPILOT_EVENTS = {"incident.autopilot.requested", "incident.autopilot.resume"}


class DomainSubscriber:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client: pubsub_v1.SubscriberClient | None = None
        self.future = None

    def _callback(self, message) -> None:  # noqa: ANN001
        try:
            event = json.loads(message.data.decode("utf-8"))
            event_type = str(event.get("event_type", ""))
            if event_type not in AUTOPILOT_EVENTS:
                message.ack()
                return
            tenant_id = str(event.get("tenant_id", ""))
            incident_id = str(event.get("incident_id", ""))
            if not tenant_id or not incident_id:
                raise ValueError("autopilot event missing tenant_id or incident_id")

            with SessionLocal() as db:
                bind_tenant(db, tenant_id)
                incident = get_incident_for_worker(db, tenant_id, incident_id)
                if not incident:
                    log.warning("autopilot.incident.not_found", tenant_id=tenant_id, incident_id=incident_id)
                    message.ack()
                    return
                with incident_advisory_lock(db, tenant_id, incident_id) as acquired:
                    if not acquired:
                        log.info("autopilot.incident.busy", tenant_id=tenant_id, incident_id=incident_id)
                        message.nack()
                        return
                    result = AutopilotRunner(db).run(incident)
                    log.info(
                        "autopilot.event.processed",
                        incident_id=incident_id,
                        status=result.status,
                        phases=list(result.phases),
                        waiting_for=result.waiting_for,
                    )
            message.ack()
        except Exception:
            log.exception("autopilot.event.failed")
            message.nack()

    def start(self) -> None:
        if not self.settings.pubsub_enabled:
            return
        if not self.settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required when Pub/Sub is enabled")
        self.client = pubsub_v1.SubscriberClient()
        subscription_path = self.client.subscription_path(
            self.settings.google_cloud_project,
            self.settings.pubsub_subscription,
        )
        flow = pubsub_v1.types.FlowControl(max_messages=20, max_lease_duration=300)
        self.future = self.client.subscribe(subscription_path, callback=self._callback, flow_control=flow)
        log.info("pubsub.subscriber.started", subscription=subscription_path)

    def stop(self) -> None:
        if self.future:
            self.future.cancel()
            try:
                self.future.result(timeout=10)
            except Exception:
                pass
        if self.client:
            self.client.close()
