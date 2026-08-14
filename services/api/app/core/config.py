from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "RedTag API"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    web_origin: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://redtag:redtag@localhost:5432/redtag"

    auth_mode: Literal["dev", "oidc"] = "dev"
    jwt_issuer: str = "redtag-local"
    jwt_audience: str = "redtag-api"
    jwt_algorithm: str = "HS256"
    jwt_secret: str = "change-me-in-production"
    jwks_url: str | None = None
    oidc_email_claim: str = "email"
    default_tenant_id: str = "tenant_demo"

    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    google_genai_use_vertexai: bool = True
    google_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    gcs_evidence_bucket: str | None = None
    pubsub_topic: str = "redtag-domain-events"
    pubsub_subscription: str = "redtag-domain-worker"
    pubsub_enabled: bool = False
    model_armor_enabled: bool = False
    model_armor_location: str = "us-central1"
    model_armor_template: str | None = None
    model_armor_fail_closed: bool = True
    real_ai_enabled: bool = False
    real_notifications_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "safety@redtag.local"
    notification_webhook_url: str | None = None

    cors_allow_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, ge=1)

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_allow_origins.split(",") if x.strip()]

    def validate_production(self) -> None:
        if self.app_env != "production":
            return
        if self.auth_mode == "dev":
            raise RuntimeError("AUTH_MODE=dev is forbidden in production")
        if not self.jwks_url and self.jwt_secret == "change-me-in-production":
            raise RuntimeError("Production OIDC requires JWKS_URL or a non-default JWT secret")
        if self.model_armor_enabled and not self.model_armor_template:
            raise RuntimeError("MODEL_ARMOR_TEMPLATE is required when Model Armor is enabled")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings
