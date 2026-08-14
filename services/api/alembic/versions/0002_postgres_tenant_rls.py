"""enable tenant row-level security on business tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-14
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Membership is deliberately excluded because it is required to authorize the tenant before the
# tenant RLS context is established. Organization and User are identity bootstrap tables as well.
TENANT_TABLES = [
    "incidents",
    "evidence_artifacts",
    "evidence_claims",
    "supply_nodes",
    "supply_edges",
    "inventory_lots",
    "customers",
    "orders",
    "shipments",
    "notifications",
    "return_cases",
    "recall_strategies",
    "approvals",
    "actions",
    "action_receipts",
    "verifications",
    "proof_nodes",
    "proof_edges",
    "audit_events",
    "security_events",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in TENANT_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f'''CREATE POLICY redtag_tenant_isolation ON "{table}"
                USING (tenant_id = current_setting('app.tenant_id', true))
                WITH CHECK (tenant_id = current_setting('app.tenant_id', true))'''
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in reversed(TENANT_TABLES):
        op.execute(f'DROP POLICY IF EXISTS redtag_tenant_isolation ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
