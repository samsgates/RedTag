"""Cloud Run compatible outbox publisher and Pub/Sub workflow consumer.

The service exposes a health endpoint while running the transactional-outbox publisher and durable
workflow subscriber. Multiple publisher replicas are safe because rows are claimed with
``SELECT FOR UPDATE SKIP LOCKED``. Pub/Sub redelivery is safe because RedTag mutations are idempotent.
"""

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.subscriber import DomainSubscriber
from app.worker import publish_batch

settings = get_settings()
configure_logging(settings.log_level)
log = structlog.get_logger()


async def _outbox_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            count = await asyncio.to_thread(publish_batch)
            if count:
                log.info("outbox.batch.published", count=count)
        except Exception:
            log.exception("outbox.batch.failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=2.0)
        except TimeoutError:
            pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop = asyncio.Event()
    subscriber = DomainSubscriber()
    publisher_task = asyncio.create_task(_outbox_loop(stop))
    try:
        await asyncio.to_thread(subscriber.start)
        log.info("workflow.worker.started", pubsub_enabled=settings.pubsub_enabled)
        yield
    finally:
        stop.set()
        await asyncio.to_thread(subscriber.stop)
        await publisher_task


app = FastAPI(title="RedTag Workflow Worker", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "pubsub_enabled": settings.pubsub_enabled}
