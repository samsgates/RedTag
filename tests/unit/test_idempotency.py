from app.services.actions import build_idempotency_key


def test_idempotency_key_is_stable():
    a = build_idempotency_key("t", "i", "inventory.quarantine", "lot1")
    b = build_idempotency_key("t", "i", "inventory.quarantine", "lot1")
    assert a == b
    assert len(a) == 64
