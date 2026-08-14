"""frozen initial PostgreSQL schema

Revision ID: 0001
Revises:
Create Date: 2026-08-14

This migration is intentionally independent of runtime SQLAlchemy metadata. Future model changes
must be introduced in new Alembic revisions rather than changing historical schema behavior.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

UPGRADE_SQL = [
    'CREATE TABLE audit_events (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64), \n\tactor_type VARCHAR(32) NOT NULL, \n\tactor_id VARCHAR(128) NOT NULL, \n\tevent_type VARCHAR(100) NOT NULL, \n\tpayload JSON NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_audit_events_event_type ON audit_events (event_type)',
    'CREATE INDEX ix_audit_events_incident_id ON audit_events (incident_id)',
    'CREATE INDEX ix_audit_events_tenant_id ON audit_events (tenant_id)',
    'CREATE INDEX ix_audit_tenant_incident_created ON audit_events (tenant_id, incident_id, created_at)',
    'CREATE TABLE customers (\n\tid VARCHAR(64) NOT NULL, \n\texternal_ref VARCHAR(128) NOT NULL, \n\tfirst_name VARCHAR(120) NOT NULL, \n\temail VARCHAR(320), \n\tphone VARCHAR(64), \n\tregion VARCHAR(64) NOT NULL, \n\tcontact_allowed BOOLEAN NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_customer_external UNIQUE (tenant_id, external_ref)\n)',
    'CREATE INDEX ix_customers_external_ref ON customers (external_ref)',
    'CREATE INDEX ix_customers_tenant_id ON customers (tenant_id)',
    'CREATE TABLE incidents (\n\tid VARCHAR(64) NOT NULL, \n\ttitle VARCHAR(240) NOT NULL, \n\tdescription TEXT NOT NULL, \n\tseverity VARCHAR(32) NOT NULL, \n\tstatus VARCHAR(40) NOT NULL, \n\tproduct_hint VARCHAR(200), \n\tapproved_strategy_id VARCHAR(64), \n\taffected_customers INTEGER NOT NULL, \n\taffected_units INTEGER NOT NULL, \n\tverification_coverage FLOAT NOT NULL, \n\tcreated_by VARCHAR(128) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_incidents_approved_strategy_id ON incidents (approved_strategy_id)',
    'CREATE INDEX ix_incidents_status ON incidents (status)',
    'CREATE INDEX ix_incidents_tenant_id ON incidents (tenant_id)',
    'CREATE TABLE inventory_lots (\n\tid VARCHAR(64) NOT NULL, \n\tproduct_id VARCHAR(64) NOT NULL, \n\tmanufacturing_batch_id VARCHAR(64) NOT NULL, \n\twarehouse VARCHAR(128) NOT NULL, \n\tquantity INTEGER NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tversion INTEGER NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_inventory_lots_manufacturing_batch_id ON inventory_lots (manufacturing_batch_id)',
    'CREATE INDEX ix_inventory_lots_product_id ON inventory_lots (product_id)',
    'CREATE INDEX ix_inventory_lots_tenant_id ON inventory_lots (tenant_id)',
    'CREATE TABLE organizations (\n\tid VARCHAR(64) NOT NULL, \n\tname VARCHAR(200) NOT NULL, \n\tautonomy_level INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE TABLE outbox_events (\n\tid VARCHAR(64) NOT NULL, \n\tevent_type VARCHAR(100) NOT NULL, \n\tincident_id VARCHAR(64), \n\tcorrelation_id VARCHAR(64) NOT NULL, \n\tcausation_id VARCHAR(64), \n\tpayload JSON NOT NULL, \n\tpublished BOOLEAN NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tpublished_at TIMESTAMP WITH TIME ZONE, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_outbox_events_correlation_id ON outbox_events (correlation_id)',
    'CREATE INDEX ix_outbox_events_event_type ON outbox_events (event_type)',
    'CREATE INDEX ix_outbox_events_incident_id ON outbox_events (incident_id)',
    'CREATE INDEX ix_outbox_events_published ON outbox_events (published)',
    'CREATE INDEX ix_outbox_events_tenant_id ON outbox_events (tenant_id)',
    'CREATE TABLE proof_edges (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tfrom_node_id VARCHAR(64) NOT NULL, \n\tto_node_id VARCHAR(64) NOT NULL, \n\trelation VARCHAR(64) NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_proof_edges_from_node_id ON proof_edges (from_node_id)',
    'CREATE INDEX ix_proof_edges_incident_id ON proof_edges (incident_id)',
    'CREATE INDEX ix_proof_edges_tenant_id ON proof_edges (tenant_id)',
    'CREATE INDEX ix_proof_edges_to_node_id ON proof_edges (to_node_id)',
    'CREATE TABLE proof_nodes (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tnode_type VARCHAR(40) NOT NULL, \n\tlabel VARCHAR(255) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tref_type VARCHAR(40), \n\tref_id VARCHAR(64), \n\tdata JSON NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_proof_nodes_incident_id ON proof_nodes (incident_id)',
    'CREATE INDEX ix_proof_nodes_tenant_id ON proof_nodes (tenant_id)',
    'CREATE TABLE security_events (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64), \n\tcategory VARCHAR(64) NOT NULL, \n\tseverity VARCHAR(16) NOT NULL, \n\tsource VARCHAR(255) NOT NULL, \n\tattempted_action VARCHAR(100), \n\tdecision VARCHAR(32) NOT NULL, \n\tdetails JSON NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_security_events_category ON security_events (category)',
    'CREATE INDEX ix_security_events_incident_id ON security_events (incident_id)',
    'CREATE INDEX ix_security_events_tenant_id ON security_events (tenant_id)',
    'CREATE TABLE supply_edges (\n\tid VARCHAR(64) NOT NULL, \n\tfrom_id VARCHAR(64) NOT NULL, \n\tto_id VARCHAR(64) NOT NULL, \n\trelation VARCHAR(64) NOT NULL, \n\tprovenance JSON NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_supply_edge UNIQUE (tenant_id, from_id, to_id, relation)\n)',
    'CREATE INDEX ix_supply_edges_from_id ON supply_edges (from_id)',
    'CREATE INDEX ix_supply_edges_tenant_id ON supply_edges (tenant_id)',
    'CREATE INDEX ix_supply_edges_to_id ON supply_edges (to_id)',
    'CREATE TABLE supply_nodes (\n\tid VARCHAR(64) NOT NULL, \n\tnode_type VARCHAR(64) NOT NULL, \n\tlabel VARCHAR(255) NOT NULL, \n\tattrs JSON NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE INDEX ix_supply_nodes_node_type ON supply_nodes (node_type)',
    'CREATE INDEX ix_supply_nodes_tenant_id ON supply_nodes (tenant_id)',
    'CREATE TABLE users (\n\tid VARCHAR(128) NOT NULL, \n\temail VARCHAR(320) NOT NULL, \n\tdisplay_name VARCHAR(200), \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id)\n)',
    'CREATE UNIQUE INDEX ix_users_email ON users (email)',
    'CREATE TABLE actions (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tagent_id VARCHAR(100) NOT NULL, \n\taction_type VARCHAR(80) NOT NULL, \n\ttarget_type VARCHAR(64) NOT NULL, \n\ttarget_id VARCHAR(128) NOT NULL, \n\trisk_class VARCHAR(8) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tpayload JSON NOT NULL, \n\tidempotency_key VARCHAR(180) NOT NULL, \n\tpolicy_decision JSON NOT NULL, \n\terror TEXT, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_action_idempotency UNIQUE (tenant_id, idempotency_key), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_actions_action_type ON actions (action_type)',
    'CREATE INDEX ix_actions_incident_id ON actions (incident_id)',
    'CREATE INDEX ix_actions_tenant_id ON actions (tenant_id)',
    'CREATE INDEX ix_actions_tenant_incident_created ON actions (tenant_id, incident_id, created_at)',
    'CREATE TABLE approvals (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\taction_type VARCHAR(64) NOT NULL, \n\trisk_class VARCHAR(8) NOT NULL, \n\tpayload JSON NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\trequested_by VARCHAR(128) NOT NULL, \n\tdecided_by VARCHAR(128), \n\tdecided_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_approvals_incident_id ON approvals (incident_id)',
    'CREATE INDEX ix_approvals_tenant_id ON approvals (tenant_id)',
    'CREATE TABLE evidence_artifacts (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tfile_name VARCHAR(255) NOT NULL, \n\tcontent_type VARCHAR(128) NOT NULL, \n\tstorage_uri TEXT NOT NULL, \n\tchecksum_sha256 VARCHAR(64) NOT NULL, \n\ttrust_level VARCHAR(32) NOT NULL, \n\tsize_bytes INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_evidence_artifacts_incident_id ON evidence_artifacts (incident_id)',
    'CREATE INDEX ix_evidence_artifacts_tenant_id ON evidence_artifacts (tenant_id)',
    'CREATE TABLE memberships (\n\tid VARCHAR(64) NOT NULL, \n\tuser_id VARCHAR(128) NOT NULL, \n\troles JSON NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_membership_tenant_user UNIQUE (tenant_id, user_id), \n\tFOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_memberships_tenant_id ON memberships (tenant_id)',
    'CREATE INDEX ix_memberships_user_id ON memberships (user_id)',
    'CREATE TABLE notifications (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tcustomer_id VARCHAR(64) NOT NULL, \n\tchannel VARCHAR(24) NOT NULL, \n\ttemplate_id VARCHAR(80) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tattempt_count INTEGER NOT NULL, \n\tprovider_ref VARCHAR(128), \n\terror TEXT, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_notification_once UNIQUE (tenant_id, incident_id, customer_id, channel), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE, \n\tFOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_notifications_customer_id ON notifications (customer_id)',
    'CREATE INDEX ix_notifications_incident_id ON notifications (incident_id)',
    'CREATE INDEX ix_notifications_tenant_id ON notifications (tenant_id)',
    'CREATE TABLE orders (\n\tid VARCHAR(64) NOT NULL, \n\tcustomer_id VARCHAR(64) NOT NULL, \n\tproduct_id VARCHAR(64) NOT NULL, \n\tmanufacturing_batch_id VARCHAR(64) NOT NULL, \n\tquantity INTEGER NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_orders_customer_id ON orders (customer_id)',
    'CREATE INDEX ix_orders_manufacturing_batch_id ON orders (manufacturing_batch_id)',
    'CREATE INDEX ix_orders_product_id ON orders (product_id)',
    'CREATE INDEX ix_orders_tenant_id ON orders (tenant_id)',
    'CREATE TABLE recall_strategies (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tscope JSON NOT NULL, \n\taffected_customers INTEGER NOT NULL, \n\taffected_units INTEGER NOT NULL, \n\tcoverage FLOAT NOT NULL, \n\testimated_cost FLOAT NOT NULL, \n\tresidual_risk VARCHAR(32) NOT NULL, \n\trecommended BOOLEAN NOT NULL, \n\trationale TEXT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_recall_strategies_incident_id ON recall_strategies (incident_id)',
    'CREATE INDEX ix_recall_strategies_tenant_id ON recall_strategies (tenant_id)',
    'CREATE TABLE action_receipts (\n\tid VARCHAR(64) NOT NULL, \n\taction_id VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tagent_id VARCHAR(100) NOT NULL, \n\tagent_version VARCHAR(32) NOT NULL, \n\ttool VARCHAR(100) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tbefore_state_hash VARCHAR(64), \n\tafter_state_hash VARCHAR(64), \n\texternal_reference VARCHAR(200), \n\tverification_status VARCHAR(32) NOT NULL, \n\texecuted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (action_id), \n\tFOREIGN KEY(action_id) REFERENCES actions (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_action_receipts_incident_id ON action_receipts (incident_id)',
    'CREATE INDEX ix_action_receipts_tenant_id ON action_receipts (tenant_id)',
    'CREATE TABLE evidence_claims (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tevidence_id VARCHAR(64) NOT NULL, \n\tclaim_type VARCHAR(64) NOT NULL, \n\tvalue TEXT NOT NULL, \n\tconfidence FLOAT NOT NULL, \n\tprovenance JSON NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE, \n\tFOREIGN KEY(evidence_id) REFERENCES evidence_artifacts (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_evidence_claims_evidence_id ON evidence_claims (evidence_id)',
    'CREATE INDEX ix_evidence_claims_incident_id ON evidence_claims (incident_id)',
    'CREATE INDEX ix_evidence_claims_tenant_id ON evidence_claims (tenant_id)',
    'CREATE TABLE return_cases (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\tcustomer_id VARCHAR(64) NOT NULL, \n\torder_id VARCHAR(64) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\trecovery_method VARCHAR(32) NOT NULL, \n\trecovered_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_return_order_incident UNIQUE (tenant_id, incident_id, order_id), \n\tFOREIGN KEY(incident_id) REFERENCES incidents (id) ON DELETE CASCADE, \n\tFOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE, \n\tFOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_return_cases_customer_id ON return_cases (customer_id)',
    'CREATE INDEX ix_return_cases_incident_id ON return_cases (incident_id)',
    'CREATE INDEX ix_return_cases_order_id ON return_cases (order_id)',
    'CREATE INDEX ix_return_cases_tenant_id ON return_cases (tenant_id)',
    'CREATE TABLE shipments (\n\tid VARCHAR(64) NOT NULL, \n\torder_id VARCHAR(64) NOT NULL, \n\tcarrier VARCHAR(80) NOT NULL, \n\ttracking_ref VARCHAR(128), \n\tstatus VARCHAR(32) NOT NULL, \n\tversion INTEGER NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_shipments_order_id ON shipments (order_id)',
    'CREATE INDEX ix_shipments_tenant_id ON shipments (tenant_id)',
    'CREATE TABLE verifications (\n\tid VARCHAR(64) NOT NULL, \n\tincident_id VARCHAR(64) NOT NULL, \n\taction_id VARCHAR(64) NOT NULL, \n\treceipt_id VARCHAR(64) NOT NULL, \n\tstatus VARCHAR(32) NOT NULL, \n\tmethod VARCHAR(80) NOT NULL, \n\tdetails JSON NOT NULL, \n\tverified_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\ttenant_id VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(action_id) REFERENCES actions (id) ON DELETE CASCADE, \n\tFOREIGN KEY(receipt_id) REFERENCES action_receipts (id) ON DELETE CASCADE\n)',
    'CREATE INDEX ix_verifications_action_id ON verifications (action_id)',
    'CREATE INDEX ix_verifications_incident_id ON verifications (incident_id)',
    'CREATE INDEX ix_verifications_tenant_id ON verifications (tenant_id)',
]

TABLES_IN_CREATE_ORDER = ['audit_events', 'customers', 'incidents', 'inventory_lots', 'organizations', 'outbox_events', 'proof_edges', 'proof_nodes', 'security_events', 'supply_edges', 'supply_nodes', 'users', 'actions', 'approvals', 'evidence_artifacts', 'memberships', 'notifications', 'orders', 'recall_strategies', 'action_receipts', 'evidence_claims', 'return_cases', 'shipments', 'verifications']


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("RedTag production migrations require PostgreSQL")
    for statement in UPGRADE_SQL:
        op.execute(statement)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("RedTag production migrations require PostgreSQL")
    for table in reversed(TABLES_IN_CREATE_ORDER):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
