from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@event.listens_for(Session, "after_begin")
def _apply_postgres_tenant_context(session: Session, transaction, connection) -> None:  # noqa: ANN001
    """Re-apply the RLS tenant variable for every PostgreSQL transaction."""

    tenant_id = session.info.get("tenant_id")
    if tenant_id and connection.dialect.name == "postgresql":
        connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.info.pop("tenant_id", None)
        db.close()
