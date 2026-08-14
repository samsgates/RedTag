import hashlib
from pathlib import Path

from app.core.config import get_settings


class EvidenceStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_root = Path(".redtag/evidence")

    def save(self, *, tenant_id: str, incident_id: str, file_name: str, content: bytes) -> tuple[str, str]:
        digest = hashlib.sha256(content).hexdigest()
        safe_name = Path(file_name).name
        key = f"{tenant_id}/{incident_id}/{digest}-{safe_name}"
        if self.settings.gcs_evidence_bucket:
            from google.cloud import storage

            client = storage.Client(project=self.settings.google_cloud_project)
            bucket = client.bucket(self.settings.gcs_evidence_bucket)
            blob = bucket.blob(key)
            blob.upload_from_string(content)
            return f"gs://{self.settings.gcs_evidence_bucket}/{key}", digest

        path = self.local_root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path), digest

    def read(self, storage_uri: str) -> bytes:
        if storage_uri.startswith("gs://"):
            from google.cloud import storage

            bucket_name, key = storage_uri.removeprefix("gs://").split("/", 1)
            client = storage.Client(project=self.settings.google_cloud_project)
            return client.bucket(bucket_name).blob(key).download_as_bytes()
        return Path(storage_uri).read_bytes()
