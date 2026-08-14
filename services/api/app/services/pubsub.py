import json

from google.cloud import pubsub_v1

from app.core.config import get_settings


class DomainPublisher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.publisher = pubsub_v1.PublisherClient() if self.settings.pubsub_enabled else None

    def publish(self, event: dict) -> str | None:
        if not self.publisher:
            return None
        if not self.settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required when Pub/Sub is enabled")
        topic_path = self.publisher.topic_path(
            self.settings.google_cloud_project,
            self.settings.pubsub_topic,
        )
        future = self.publisher.publish(topic_path, json.dumps(event).encode(), event_type=event["event_type"])
        return future.result(timeout=30)
