"""Provision or update a RedTag tenant user after external OIDC/Firebase identity creation."""

import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import Membership, Organization, User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision a RedTag user and tenant membership")
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--tenant-name", required=True)
    parser.add_argument("--user-id", required=True, help="OIDC subject, for Firebase this is the UID")
    parser.add_argument("--email", required=True)
    parser.add_argument("--roles", default="Quality Manager,Approver", help="Comma separated RedTag roles")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    roles = [role.strip() for role in args.roles.split(",") if role.strip()]
    with SessionLocal() as db:
        org = db.get(Organization, args.tenant_id)
        if not org:
            org = Organization(id=args.tenant_id, name=args.tenant_name, autonomy_level=2)
            db.add(org)
        user = db.get(User, args.user_id) or db.scalar(select(User).where(User.email == args.email))
        if not user:
            user = User(id=args.user_id, email=args.email, display_name=args.email.split("@", 1)[0])
            db.add(user)
            db.flush()
        membership = db.scalar(
            select(Membership).where(Membership.user_id == user.id, Membership.tenant_id == args.tenant_id)
        )
        if membership:
            membership.roles = roles
            membership.active = True
        else:
            db.add(Membership(user_id=user.id, tenant_id=args.tenant_id, roles=roles, active=True))
        db.commit()
    print(f"Provisioned {args.email} in {args.tenant_id} with roles: {', '.join(roles)}")


if __name__ == "__main__":
    main()
