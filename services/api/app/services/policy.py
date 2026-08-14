from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PolicyDecision:
    outcome: str
    reason: str
    risk_class: str
    approval_required: bool
    policy_version: str = "builtin-1.0"

    def as_dict(self) -> dict:
        return asdict(self)


class PolicyEngine:
    """Deterministic policy layer. Replace or extend with tenant policy-as-code in production."""

    def evaluate(
        self,
        *,
        action_type: str,
        risk_class: str,
        autonomy_level: int,
        quantity: int = 0,
        customer_count: int = 0,
    ) -> PolicyDecision:
        if action_type in {"customer.bulk_export", "system.shell", "system.sql"}:
            return PolicyDecision("DENY", "Prohibited capability", risk_class, False)
        if risk_class == "R4":
            return PolicyDecision("REQUIRE_APPROVAL", "Legally or financially sensitive", risk_class, True)
        if risk_class == "R3" or quantity > 1000 or customer_count > 10000:
            return PolicyDecision("REQUIRE_APPROVAL", "High impact threshold exceeded", risk_class, True)
        if autonomy_level < 2 and risk_class in {"R1", "R2"}:
            return PolicyDecision("REQUIRE_APPROVAL", "Tenant autonomy level requires approval", risk_class, True)
        return PolicyDecision("ALLOW", "Allowed by built-in guarded autonomy policy", risk_class, False)
