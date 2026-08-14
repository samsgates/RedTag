from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.db.tenant import bind_tenant
from app.models.domain import Membership, User


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    roles: tuple[str, ...]
    email: str | None = None

    def has_role(self, *allowed: str) -> bool:
        return bool(set(self.roles).intersection(allowed))


def _dev_principal(settings: Settings, x_tenant_id: str | None) -> Principal:
    return Principal(
        user_id="user_demo",
        tenant_id=x_tenant_id or settings.default_tenant_id,
        roles=("Owner", "Tenant Admin", "Quality Manager", "Approver"),
        email="demo@redtag.local",
    )


def _decode_token(token: str, settings: Settings) -> dict:
    try:
        if settings.jwks_url:
            signing_key = PyJWKClient(settings.jwks_url).get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
            )
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def get_principal(
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> Principal:
    if settings.auth_mode == "dev":
        principal = _dev_principal(settings, x_tenant_id)
        bind_tenant(db, principal.tenant_id)
        return principal

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    token = authorization.removeprefix("Bearer ").strip()
    payload = _decode_token(token, settings)
    user_id = str(payload.get("sub", ""))
    email = str(payload.get(settings.oidc_email_claim, "") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    # Bind tenant context before any tenant-scoped business query. Identity bootstrap tables are
    # intentionally outside RLS so membership can be validated first.
    bind_tenant(db, x_tenant_id)

    user = db.scalar(
        select(User).where(or_(User.id == user_id, User.email == email if email else False))
    )
    if not user:
        raise HTTPException(status_code=403, detail="User is not provisioned in RedTag")
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.tenant_id == x_tenant_id,
            Membership.active.is_(True),
        )
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No active membership for tenant")
    return Principal(
        user_id=user.id,
        tenant_id=x_tenant_id,
        roles=tuple(str(x) for x in membership.roles),
        email=user.email,
    )


def require_roles(*roles: str):
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_role(*roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal

    return dependency
