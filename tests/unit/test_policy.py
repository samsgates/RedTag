from app.services.policy import PolicyEngine


def test_r2_guarded_action_allowed():
    decision = PolicyEngine().evaluate(action_type="inventory.quarantine", risk_class="R2", autonomy_level=2)
    assert decision.outcome == "ALLOW"
    assert not decision.approval_required


def test_r4_requires_approval():
    decision = PolicyEngine().evaluate(action_type="regulatory.file", risk_class="R4", autonomy_level=4)
    assert decision.approval_required


def test_bulk_export_denied():
    decision = PolicyEngine().evaluate(action_type="customer.bulk_export", risk_class="R4", autonomy_level=4)
    assert decision.outcome == "DENY"
