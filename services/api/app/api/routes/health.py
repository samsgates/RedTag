from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness endpoint. It intentionally does not depend on external services."""

    settings = get_settings()
    return HealthResponse(status="ok", environment=settings.app_env, database="unchecked")


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str | bool]:
    """Readiness endpoint. Traffic should only be routed when the database is usable."""

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from exc
    return {"ready": True, "database": "ok"}
