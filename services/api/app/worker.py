import time
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.domain import OutboxEvent
from app.services.pubsub import DomainPublisher

settings = get_settings()
configure_logging(settings.log_level)
log = structlog.get_logger()


def publish_batch() -> int:
    publisher = DomainPublisher()
    count = 0
    with SessionLocal() as db:
        rows = list(
            db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published.is_(False))
                .order_by(OutboxEvent.created_at.asc())
                .limit(100)
                .with_for_update(skip_locked=True)
            )
        )
        for row in rows:
            payload = {
                "event_id": row.id,
                "event_type": row.event_type,
                "tenant_id": row.tenant_id,
                "incident_id": row.incident_id,
                "correlation_id": row.correlation_id,
                "causation_id": row.causation_id,
                "timestamp": row.created_at.isoformat(),
                "payload": row.payload,
            }
            if settings.pubsub_enabled:
                publisher.publish(payload)
            row.published = True
            row.published_at = datetime.now(timezone.utc)
            count += 1
        db.commit()
    return count


def main() -> None:
    log.info("outbox.worker.started", pubsub_enabled=settings.pubsub_enabled)
    while True:
        try:
            count = publish_batch()
            if count:
                log.info("outbox.batch.published", count=count)
        except Exception:
            log.exception("outbox.batch.failed")
        time.sleep(2)


if __name__ == "__main__":
    main()
